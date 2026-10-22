#include "EWHarvestTree.h"
#include "EWProgressionComponent.h"
#include "EWCharacter.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"

AEWHarvestTree::AEWHarvestTree()
{
    // Trees stay still until an authoritative environmental knockdown.
    SetReplicateMovement(false);
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
}

void AEWHarvestTree::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWHarvestTree, Wood); DOREPLIFETIME(AEWHarvestTree, Thatch);
    DOREPLIFETIME(AEWHarvestTree, WoodRemaining); DOREPLIFETIME(AEWHarvestTree, ThatchRemaining);
    DOREPLIFETIME(AEWHarvestTree, WoodPerStrike); DOREPLIFETIME(AEWHarvestTree, ThatchPerStrike);
    DOREPLIFETIME(AEWHarvestTree, bFelled);
}

void AEWHarvestTree::PlayHitShake(const FVector& Direction, float Degrees)
{
    if (!bFelled) Super::PlayHitShake(Direction, Degrees);
}

bool AEWHarvestTree::Fell(FVector Direction)
{
    if (!HasAuthority() || bFelled || !IsValid(Mesh) || Direction.IsNearlyZero()) return false;

    Direction.Z = 0.f;
    Direction = Direction.GetSafeNormal();
    if (Direction.IsNearlyZero()) return false;

    const FVector TipAxis = FVector::CrossProduct(FVector::UpVector, Direction).GetSafeNormal();
    if (TipAxis.IsNearlyZero()) return false;

    bFelled = true;
    FallElapsed = 0.f;
    FallStartRotation = GetActorQuat();
    FallTargetRotation = (FQuat(TipAxis, HALF_PI) * FallStartRotation).GetNormalized();
    ConfigureFelledCollision();
    SetReplicateMovement(true);
    SetActorTickEnabled(true);
    ForceNetUpdate();
    return true;
}

void AEWHarvestTree::Tick(float DeltaSeconds)
{
    if (!bFelled)
    {
        Super::Tick(DeltaSeconds);
        return;
    }

    if (!HasAuthority()) return; // Clients receive the authoritative actor transform through movement replication.

    FallElapsed = FMath::Min(FallDuration, FallElapsed + FMath::Max(DeltaSeconds, 0.f));
    const float Alpha = FallDuration > 0.f ? FMath::Clamp(FallElapsed / FallDuration, 0.f, 1.f) : 1.f;
    SetActorRotation(FQuat::Slerp(FallStartRotation, FallTargetRotation, Alpha).GetNormalized());
    if (Alpha >= 1.f) SetActorTickEnabled(false);
}

void AEWHarvestTree::OnRep_Felled()
{
    if (bFelled) ConfigureFelledCollision();
}

void AEWHarvestTree::ConfigureFelledCollision()
{
    if (!Blocker || !Mesh) return;

    const bool bHasBlocker = BlockerRadius > 0.f && BlockerHalfHeight > 0.f;
    const float Radius = FMath::Max(BlockerRadius, 1.f);
    float HalfHeight = FMath::Max(BlockerHalfHeight, Radius);
    if (const UStaticMesh* StaticMesh = Mesh->GetStaticMesh())
    {
        const FVector MeshScale = Mesh->GetComponentScale().GetAbs();
        HalfHeight = FMath::Max(HalfHeight, StaticMesh->GetBoundingBox().GetExtent().Z * MeshScale.Z);
    }

    // The capsule stays attached to the trunk and turns with it, approximating the fallen tree as a solid log.
    Blocker->SetUsingAbsoluteRotation(false);
    Blocker->SetRelativeRotation(FRotator::ZeroRotator);
    // Set in world space so nonuniform or random mesh scale does not scale the pivot offset twice.
    Blocker->SetWorldLocation(GetActorLocation() + GetActorUpVector() * HalfHeight);
    Blocker->SetCapsuleSize(Radius, HalfHeight);
    Blocker->SetCollisionEnabled(bHasBlocker ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    Blocker->SetCollisionResponseToAllChannels(ECR_Block);
    Blocker->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
}

bool AEWHarvestTree::CanAccessSource(AEWCharacter* Survivor) const
{
    if (bHarvesting || !Super::CanInteract_Implementation(Survivor) || !Survivor->GetSurvivalComponent()
        || Survivor->GetSurvivalComponent()->GetHealth() <= 0 || !Survivor->GetInventoryComponent()
        || !IsValid(Wood) || !IsValid(Thatch) || Wood == Thatch
        || Wood->Category != EEWItemCategory::Resource || Thatch->Category != EEWItemCategory::Resource
        || Wood->ItemId.IsNone() || Thatch->ItemId.IsNone() || WoodPerStrike <= 0 || ThatchPerStrike <= 0
        || WoodRemaining < 0 || ThatchRemaining < 0 || (WoodRemaining == 0 && ThatchRemaining == 0)) return false;
    return true;
}

bool AEWHarvestTree::CanHarvest(AEWCharacter* Survivor) const
{
    if (!CanAccessSource(Survivor) || !Survivor->GetEquipmentComponent()) return false;
    const auto* Tool = Survivor->GetEquipmentComponent()->GetEquippedItem(EEWEquipmentSlot::MainHand);
    return IsValid(Tool) && Tool->Category == EEWItemCategory::Tool && Tool->GatheringTool == EEWGatheringTool::Hatchet;
}

int32 AEWHarvestTree::TryHarvest(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !IsValid(Survivor) || !Survivor->HasAuthority() || !CanHarvest(Survivor)
        || FEWInteractionTargeting::FindTarget(Survivor) != this) return 0;
    TGuardValue<bool> Guard(bHarvesting, true);
    auto* Inventory = Survivor->GetInventoryComponent();
    const int32 AddedWood = Inventory->AddItem(Wood, FMath::Min(WoodRemaining, WoodPerStrike));
    WoodRemaining -= AddedWood;
    const int32 AddedThatch = Inventory->AddItem(Thatch, FMath::Min(ThatchRemaining, ThatchPerStrike));
    ThatchRemaining -= AddedThatch;
    if (AddedWood + AddedThatch > 0) if (auto* Progress = Survivor->GetProgressionComponent()) Progress->Award(EEWExperienceSource::Gather);
    if (WoodRemaining == 0 && ThatchRemaining == 0) Destroy();
    else if (AddedWood > 0 || AddedThatch > 0) ForceNetUpdate();
    return AddedWood + AddedThatch;
}
