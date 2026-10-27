#include "EWHarvestTree.h"
#include "EWProgressionComponent.h"
#include "EWCharacter.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Net/UnrealNetwork.h"

namespace
{
    /** How each species comes down (all placeholder tuning, TBD owner): time scale, ease exponent (higher = slow start, late
     *  drop), side sway in degrees while leaning, and the landing bounce in degrees. */
    struct FFallStyle { const TCHAR* Name; float TimeScale, Ease, SwayDegrees, BounceDegrees; };
    constexpr float LandBounceSeconds = .5f;
    const FFallStyle Styles[] = {
        {TEXT("Oak"),    1.25f, 2.4f, 0.f, 2.5f},     // heavy: slow, a thud
        {TEXT("Ash"),    1.0f,  2.0f, 1.5f, 1.5f},    // tall and straight: a steady lean, a little sway
        {TEXT("Birch"),  .9f,   1.8f, 4.f, 3.f},      // slender: flexes and springs on landing
        {TEXT("Spruce"), .8f,   2.6f, 0.f, 1.f},      // stiff: holds, then goes over
        {TEXT("Palm"),   .9f,   1.6f, 6.f, 4.f},      // whips side to side as it goes
    };
    const FFallStyle DefaultStyle = {TEXT("Default"), 1.f, 2.f, 0.f, 0.f};

    const FFallStyle& StyleFor(const UStaticMesh* StaticMesh)
    {
        const FString MeshName = StaticMesh ? StaticMesh->GetName() : FString();
        for (const FFallStyle& Style : Styles)
            if (MeshName.Contains(Style.Name) || (FCString::Strcmp(Style.Name, TEXT("Palm")) == 0 && MeshName.Contains(TEXT("VeyranPalm")))) return Style;
        return DefaultStyle;
    }
}

FName AEWHarvestTree::GetFallStyleName() const
{
    return FName(StyleFor(Mesh ? Mesh->GetStaticMesh() : nullptr).Name);
}

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
    DOREPLIFETIME(AEWHarvestTree, bFading);
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
    FallSeconds = FallDuration;
    const FFallStyle& Style = StyleFor(Mesh->GetStaticMesh());
    FallEase = Style.Ease; FallSway = Style.SwayDegrees; FallBounce = Style.BounceDegrees;
    FallDirection = Direction;
    FallTipAxis = TipAxis;
    LandElapsed = 0.f;
    if (const UStaticMesh* StaticMesh = Mesh->GetStaticMesh())
    {
        // Taller trunks take longer to come down (tuning: 6 m is the base time, up to 2.5 times it).
        const float Height = StaticMesh->GetBoundingBox().GetSize().Z * Mesh->GetComponentScale().GetAbs().Z;
        FallSeconds = FallDuration * FMath::Clamp(Height / 600.f, 1.f, 2.5f) * Style.TimeScale;
    }
    FallStartRotation = GetActorQuat();
    FallTargetRotation = (FQuat(TipAxis, HALF_PI) * FallStartRotation).GetNormalized();
    ConfigureFelledCollision();
    SetReplicateMovement(true);
    SetActorTickEnabled(true);
    ForceNetUpdate();
    return true;
}

void AEWHarvestTree::StartFade()
{
    if (bFading) return;
    bFading = true;
    FadeElapsed = 0.f;
    OnRep_Fading();
    ForceNetUpdate();
}

void AEWHarvestTree::OnRep_Fading()
{
    if (!bFading || !Mesh) return;
    // The tree's own copies of its materials, so only this tree fades; materials without a Fade parameter are unaffected.
    FadeMaterials.Reset();
    for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
        if (UMaterialInstanceDynamic* Copy = Mesh->CreateDynamicMaterialInstance(Slot)) FadeMaterials.Add(Copy);
    SetActorTickEnabled(true);
}

void AEWHarvestTree::UpdateFade(float DeltaSeconds)
{
    FadeElapsed += FMath::Max(DeltaSeconds, 0.f);
    FadeAlpha = 1.f - FMath::Clamp(FadeElapsed / FMath::Max(FadeSeconds, .1f), 0.f, 1.f);
    for (UMaterialInstanceDynamic* Copy : FadeMaterials)
        if (Copy) Copy->SetScalarParameterValue(TEXT("Fade"), FadeAlpha);
    if (HasAuthority() && FadeElapsed >= FadeSeconds) Destroy();
}

void AEWHarvestTree::Tick(float DeltaSeconds)
{
    if (bFading)
    {
        UpdateFade(DeltaSeconds);
        return;
    }
    if (!bFelled)
    {
        Super::Tick(DeltaSeconds);
        return;
    }

    if (!HasAuthority()) return; // Clients receive the authoritative actor transform through movement replication.

    FallElapsed = FMath::Min(FallSeconds, FallElapsed + FMath::Max(DeltaSeconds, 0.f));
    const float Time = FallSeconds > 0.f ? FMath::Clamp(FallElapsed / FallSeconds, 0.f, 1.f) : 1.f;
    // A cut tree leans slowly and then drops faster as it goes over (gravity), so ease in; each species adds its own sway and bounce.
    const float Alpha = FMath::Pow(Time, FallEase);
    FQuat Rotation = FQuat::Slerp(FallStartRotation, FallTargetRotation, Alpha).GetNormalized();
    if (Time < 1.f)
    {
        const float Sway = FallSway * FMath::Sin(Time * PI * 3.f) * (1.f - Time);
        if (!FMath::IsNearlyZero(Sway)) Rotation = (FQuat(FallDirection, FMath::DegreesToRadians(Sway)) * Rotation).GetNormalized();
        SetActorRotation(Rotation);
        return;
    }
    LandElapsed += FMath::Max(DeltaSeconds, 0.f);
    const float Bounce = LandElapsed < LandBounceSeconds
        ? FallBounce * FMath::Sin(PI * LandElapsed / LandBounceSeconds) * (1.f - LandElapsed / LandBounceSeconds) : 0.f;
    Rotation = (FQuat(FallTipAxis, -FMath::DegreesToRadians(Bounce)) * FallTargetRotation).GetNormalized();
    SetActorRotation(Rotation);
    if (!bRemoveAfterFall)
    {
        if (LandElapsed >= LandBounceSeconds) SetActorTickEnabled(false);
        return;
    }
    if (LandElapsed >= RemoveDelay) StartFade();
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

bool AEWHarvestTree::CutDown(AEWCharacter* Survivor)
{
    if (!HasAuthority()) return false;
    if (bFelled)
    {
        // Already down (knocked over earlier): it now lies a moment, then goes.
        bRemoveAfterFall = true;
        LandElapsed = LandBounceSeconds;      // already down: no landing bounce, just the wait
        SetActorTickEnabled(true);
        return true;
    }
    const FVector Away = IsValid(Survivor) ? GetActorLocation() - Survivor->GetActorLocation() : GetActorForwardVector();
    bRemoveAfterFall = true;
    LandElapsed = 0.f;
    if (Fell(Away)) return true;
    Destroy();      // no direction to fall in (or nothing to tip): remove it as before
    return false;
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
    if (WoodRemaining == 0 && ThatchRemaining == 0) CutDown(Survivor);
    else if (AddedWood > 0 || AddedThatch > 0) ForceNetUpdate();
    return AddedWood + AddedThatch;
}
