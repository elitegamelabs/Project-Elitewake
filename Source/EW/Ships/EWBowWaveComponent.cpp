#include "Ships/EWBowWaveComponent.h"
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

namespace
{
    // The same flat patch and churned-foam material as the wake trail.
    const TCHAR* const BowPatchMesh = TEXT("/Engine/BasicShapes/Plane.Plane");
    const TCHAR* const BowPatchMaterial = TEXT("/Game/Elitewake/World/Ships/M_WakeTrail_v1.M_WakeTrail_v1");
    // Tuning: how the bow waves splay from the stem (degrees off the heading), how long they run (beams, at full
    // strength), the side wash's width (cm), how much a turn shifts the wash to the outside, the turn rate (deg/s)
    // that counts as a hard turn, and how fast it all follows her.
    constexpr float BowSplay = 32.f, BowLengthBeams = 1.6f, WashWidth = 160.f, TurnShift = .7f, HardTurn = 12.f, Follow = 3.f;
}

UEWBowWaveComponent::UEWBowWaveComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

AEWShip* UEWBowWaveComponent::Ship() const
{
    return Cast<AEWShip>(GetOwner());
}

void UEWBowWaveComponent::BeginPlay()
{
    Super::BeginPlay();
    AEWShip* S = Ship();
    UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, BowPatchMesh);
    UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, BowPatchMaterial, nullptr, LOAD_Quiet | LOAD_NoWarn);
    if (!S || !Mesh || !Material || GetNetMode() == NM_DedicatedServer)
    {
        SetComponentTickEnabled(false);
        return;
    }
    Foam = NewObject<UInstancedStaticMeshComponent>(S, NAME_None, RF_Transient);
    Foam->SetStaticMesh(Mesh);
    Foam->SetMaterial(0, Material);
    Foam->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Foam->SetCastShadow(false);
    Foam->NumCustomDataFloats = 1;   // the patch's foam strength (0 to 1), as the wake trail's
    Foam->SetUsingAbsoluteLocation(true);
    Foam->SetUsingAbsoluteRotation(true);
    Foam->SetUsingAbsoluteScale(true);
    Foam->SetTranslucentSortPriority(3);
    Foam->RegisterComponent();
    Foam->SetWorldTransform(FTransform::Identity);
}

void UEWBowWaveComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (Foam) Foam->DestroyComponent();
    Super::EndPlay(Reason);
}

void UEWBowWaveComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    const AEWShip* S = Ship();
    if (!S || !Foam || DeltaSeconds <= 0.f) return;
    // Her turn, as this machine sees it: the change in heading, smoothed.
    const float Yaw = S->GetActorRotation().Yaw;
    const float Turn = bHasYaw ? FMath::FindDeltaAngleDegrees(LastYaw, Yaw) / DeltaSeconds : 0.f;
    LastYaw = Yaw;
    bHasYaw = true;
    TurnRate = FMath::FInterpTo(TurnRate, Turn, DeltaSeconds, Follow);
    const float Top = S->Definition && S->Definition->TopSpeed > 0.f ? S->Definition->TopSpeed * 1.8f : 1000.f;   // the best sail's multiplier
    const float Way = S->IsSinking() ? 0.f : FMath::Clamp(S->GetSpeed() / Top, 0.f, 1.f);
    // Turning to starboard throws the wash out to port, the outside of the turn, and the other way about.
    const float Lean = FMath::Clamp(TurnRate / HardTurn, -1.f, 1.f) * TurnShift;
    Bow = FMath::FInterpTo(Bow, FMath::Sqrt(Way), DeltaSeconds, Follow);
    Port = FMath::FInterpTo(Port, FMath::Clamp(Way * (1.f + Lean), 0.f, 1.f), DeltaSeconds, Follow);
    Starboard = FMath::FInterpTo(Starboard, FMath::Clamp(Way * (1.f - Lean), 0.f, 1.f), DeltaSeconds, Follow);

    Foam->ClearInstances();
    if (Bow < .02f && Port < .02f && Starboard < .02f) return;
    const FVector Extent = S->Definition ? S->Definition->HullExtent : FVector(700, 250, 200);
    const float Beam = Extent.Y * 2.f;
    const FVector Forward = S->GetActorForwardVector().GetSafeNormal2D();
    const FVector Right = FVector::CrossProduct(FVector::UpVector, Forward);
    const FVector Middle(S->GetActorLocation().X, S->GetActorLocation().Y, S->SurfaceZ + 5.f);
    const FVector Stem = Middle + Forward * Extent.X * .92f;
    auto Patch = [this](const FVector& Centre, float YawDeg, float Length, float Width, float Strength)
    {
        if (Strength < .02f) return;
        const int32 Index = Foam->AddInstance(FTransform(FRotator(0.f, YawDeg, 0.f), Centre, FVector(Length / 100.f, Width / 100.f, 1.f)), true);
        Foam->SetCustomDataValue(Index, 0, Strength, false);
    };
    const float Heading = Forward.Rotation().Yaw;
    for (const float Side : {-1.f, 1.f})
    {
        // A bow wave: from the stem, running aft and out at the splay, longer and stronger with way on her, and
        // heavier on the side the turn throws water to.
        const float Strength = Bow * (Side > 0.f ? Starboard : Port) / FMath::Max(Way, .05f);
        const float Length = Beam * BowLengthBeams * (.4f + .6f * Bow);
        const FVector Out = (-Forward).RotateAngleAxis(-Side * BowSplay, FVector::UpVector);
        Patch(Stem + Out * Length * .5f + Right * Side * Beam * .15f, Heading + 180.f - Side * BowSplay, Length, WashWidth * (.6f + .6f * Bow),
              FMath::Clamp(Strength, 0.f, 1.f) * .9f);
        // The side wash along her, from abreast the bow wave to the stern, just outside the hull.
        const float Wash = Side > 0.f ? Starboard : Port;
        Patch(Middle - Forward * Extent.X * .1f + Right * Side * (Extent.Y + WashWidth * .35f), Heading, Extent.X * 1.6f, WashWidth, Wash * .75f);
    }
    Foam->MarkRenderStateDirty();
}
