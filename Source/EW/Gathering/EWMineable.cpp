#include "EWMineable.h"
#include "World/EWWorldState.h"
#include "EWProgressionComponent.h"
#include "EWCharacter.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"

AEWMineable::AEWMineable()
{
    // It never moves, so every machine can shake its own copy when struck.
    SetReplicateMovement(false);
}

void AEWMineable::BeginPlay()
{
    Super::BeginPlay();
    InitializeMiningStock();
}

void AEWMineable::InitializeMiningStock()
{
    if (!HasAuthority() || bStockInitialized) return;
    bStockInitialized = true;
    if (bRandomizeStock)
    {
        const int32 Low = FMath::Max(1, MinimumStock);
        Remaining = FMath::RandRange(Low, FMath::Max(Low, MaximumStock));
    }
    InitialStock = Remaining;
    RefreshNodeAvailability();
    ForceNetUpdate();
}

void AEWMineable::OnRep_Remaining()
{
    RefreshNodeAvailability();
}

void AEWMineable::RefreshNodeAvailability()
{
    const bool bHasStock = Remaining > 0;
    if (Mesh)
    {
        Mesh->SetVisibility(bHasStock, true);
        Mesh->SetCollisionEnabled(bHasStock ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    }
    if (Blocker)
    {
        const bool bHasBlocker = BlockerRadius > 0.f && BlockerHalfHeight > 0.f;
        Blocker->SetCollisionEnabled(bHasStock && bHasBlocker ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    }
}

void AEWMineable::Respawn()
{
    if (!HasAuthority() || IsActorBeingDestroyed()) return;
    if (bRandomizeStock)
    {
        const int32 Low = FMath::Max(1, MinimumStock);
        Remaining = FMath::RandRange(Low, FMath::Max(Low, MaximumStock));
    }
    else Remaining = InitialStock;
    RefreshNodeAvailability();
    ForceNetUpdate();
}

float AEWMineable::GetRespawnLeft() const
{
    return GetWorld() && GetWorldTimerManager().IsTimerActive(RespawnTimer) ? GetWorldTimerManager().GetTimerRemaining(RespawnTimer) : -1.f;
}

void AEWMineable::RestoreSaved(int32 InRemaining, float RespawnLeft)
{
    if (!HasAuthority()) return;
    InitializeMiningStock();
    Remaining = FMath::Max(0, InRemaining);
    RefreshNodeAvailability();
    GetWorldTimerManager().ClearTimer(RespawnTimer);
    if (Remaining == 0 && bRespawnWhenDepleted)
        GetWorldTimerManager().SetTimer(RespawnTimer, this, &AEWMineable::Respawn, FMath::Max(0.01f, RespawnLeft >= 0.f ? RespawnLeft : RespawnSeconds), false);
    ForceNetUpdate();
}

void AEWMineable::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWMineable, Resource);
    DOREPLIFETIME(AEWMineable, Remaining);
    DOREPLIFETIME(AEWMineable, PerStrike);
    DOREPLIFETIME(AEWMineable, MinimumPickaxeTier);
}

bool AEWMineable::CanAccessSource(AEWCharacter* Survivor) const
{
    return !bMining && Super::CanInteract_Implementation(Survivor)
        && Survivor->GetSurvivalComponent() && Survivor->GetSurvivalComponent()->GetHealth() > 0
        && Survivor->GetInventoryComponent() && IsValid(Resource)
        && Resource->Category == EEWItemCategory::Resource && !Resource->ItemId.IsNone()
        && Remaining > 0 && PerStrike > 0;
}

bool AEWMineable::CanMine(AEWCharacter* Survivor) const
{
    if (!CanAccessSource(Survivor) || !Survivor->GetEquipmentComponent()) return false;
    const auto* Tool = Survivor->GetEquipmentComponent()->GetEquippedItem(EEWEquipmentSlot::MainHand);
    return IsValid(Tool) && Tool->Category == EEWItemCategory::Tool
        && Tool->GatheringTool == EEWGatheringTool::Pickaxe
        && static_cast<uint8>(Tool->PickaxeTier) >= static_cast<uint8>(MinimumPickaxeTier);
}

int32 AEWMineable::TryMine(AEWCharacter* Survivor)
{
    InitializeMiningStock();
    if (!HasAuthority() || !IsValid(Survivor) || !Survivor->HasAuthority() || !CanMine(Survivor)
        || FEWInteractionTargeting::FindTarget(Survivor) != this) return 0;
    TGuardValue<bool> Guard(bMining, true);
    const int32 Added = Survivor->GetInventoryComponent()->AddItem(Resource, FMath::Min(Remaining, PerStrike));
    Remaining -= Added;
    UEWWorldStateSubsystem::Touch(this);
    if (Added > 0) if (auto* Progress = Survivor->GetProgressionComponent()) Progress->Award(EEWExperienceSource::Gather, 2);
    if (Remaining == 0)
    {
        RefreshNodeAvailability();
        if (bRespawnWhenDepleted && GetWorld())
        {
            GetWorldTimerManager().SetTimer(RespawnTimer, this, &AEWMineable::Respawn, FMath::Max(0.01f, RespawnSeconds), false);
            ForceNetUpdate();
        }
        else Destroy();
    }
    else if (Added > 0) ForceNetUpdate();
    return Added;
}
