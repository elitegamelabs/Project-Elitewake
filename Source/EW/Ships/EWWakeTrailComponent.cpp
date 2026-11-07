#include "Ships/EWWakeTrailComponent.h"
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

namespace
{
    // The patch: a flat square on the water (the engine's 1 m plane) in the trail's foam material.
    const TCHAR* const PatchMesh = TEXT("/Engine/BasicShapes/Plane.Plane");
    const TCHAR* const PatchMaterial = TEXT("/Game/Elitewake/World/Ships/M_WakeTrail_v1.M_WakeTrail_v1");
    // How long a patch is along the track, and how much wider than the beam it is when laid and when old (tuning).
    constexpr float PatchLength = 260.f, WidthLaid = 1.1f, WidthOld = 2.6f;
}

UEWWakeTrailComponent::UEWWakeTrailComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

AEWShip* UEWWakeTrailComponent::Ship() const
{
    return Cast<AEWShip>(GetOwner());
}

FVector UEWWakeTrailComponent::Stern(const AEWShip* S) const
{
    const FVector Extent = S->Definition ? S->Definition->HullExtent : FVector(700, 250, 200);
    FVector At = S->GetActorLocation() - S->GetActorForwardVector() * Extent.X * .9f;
    At.Z = S->SurfaceZ + 4.f;
    return At;
}

void UEWWakeTrailComponent::BeginPlay()
{
    Super::BeginPlay();
    AEWShip* S = Ship();
    UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, PatchMesh);
    UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, PatchMaterial, nullptr, LOAD_Quiet | LOAD_NoWarn);
    if (!S || !Mesh || !Material || GetNetMode() == NM_DedicatedServer)
    {
        SetComponentTickEnabled(false);
        return;
    }
    // Its own component, not attached to the hull: the patches stay where they were laid.
    Foam = NewObject<UInstancedStaticMeshComponent>(S, NAME_None, RF_Transient);
    Foam->SetStaticMesh(Mesh);
    Foam->SetMaterial(0, Material);
    Foam->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Foam->SetCastShadow(false);
    Foam->NumCustomDataFloats = 1;   // how strong this patch's foam is now (0 to 1)
    Foam->SetUsingAbsoluteLocation(true);
    Foam->SetUsingAbsoluteRotation(true);
    Foam->SetUsingAbsoluteScale(true);
    Foam->SetTranslucentSortPriority(2);
    Foam->RegisterComponent();
    Foam->SetWorldTransform(FTransform::Identity);
}

void UEWWakeTrailComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (Foam) Foam->DestroyComponent();
    Super::EndPlay(Reason);
}

float UEWWakeTrailComponent::GetTrailReach() const
{
    const AEWShip* S = Ship();
    if (!S || Patches.IsEmpty()) return 0.f;
    return FVector::Dist2D(Patches[0].At, Stern(S));
}

FVector UEWWakeTrailComponent::GetPatchLocation(int32 Index) const
{
    return Patches.IsValidIndex(Index) ? Patches[Index].At : FVector::ZeroVector;
}

void UEWWakeTrailComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    const AEWShip* S = Ship();
    if (!S || !Foam) return;
    const FVector Here = Stern(S);
    // Only going forward lays foam (owner: when a ship moves forward); backing or drifting lays none.
    const float Forward = FVector::DotProduct(Here - (bHasLast ? LastStern : Here), S->GetActorForwardVector());
    LastStern = Here;
    bHasLast = true;
    const float Top = S->Definition && S->Definition->TopSpeed > 0.f ? S->Definition->TopSpeed : 600.f;
    const float Strength = FMath::Clamp(S->GetSpeed() / Top, 0.f, 1.f);
    if (Forward > 0.f && Strength > .03f && !S->IsSinking())
    {
        Travelled += Forward;
        SinceDrop += Forward;
        if (SinceDrop >= DropSpacing || Patches.IsEmpty())
        {
            SinceDrop = 0.f;
            FPatch P;
            P.At = Here;
            P.Yaw = S->GetActorRotation().Yaw;
            P.DroppedAt = Travelled;
            P.Strength = Strength;
            Patches.Add(P);
            SinceLastPatch = 0.f;
        }
    }
    SinceLastPatch += DeltaSeconds;
    // A patch is gone once the ship is a trail's length past it, and the whole trail once the ship has stopped a while.
    Patches.RemoveAll([this](const FPatch& P) { return Travelled - P.DroppedAt > TrailLength; });
    if (SinceLastPatch > StopFadeSeconds + .5f) Patches.Empty();
    const float Beam = S->Definition ? S->Definition->HullExtent.Y * 2.f : 500.f;
    Redraw(Beam);
}

void UEWWakeTrailComponent::Redraw(float Beam)
{
    // Rebuilt each frame: a sloop's trail holds about twenty patches.
    Foam->ClearInstances();
    for (int32 i = 0; i < Patches.Num(); ++i)
    {
        const FPatch& P = Patches[i];
        const float Along = FMath::Clamp((Travelled - P.DroppedAt) / TrailLength, 0.f, 1.f);
        // Faded by how far behind it lies, and, once the ship has stopped laying more, by how long ago that was.
        const float Left = (1.f - Along) * FMath::Clamp(1.f - (SinceLastPatch - .5f) / StopFadeSeconds, 0.f, 1.f);
        const float Width = Beam * FMath::Lerp(WidthLaid, WidthOld, Along);
        const FTransform Patch(FRotator(0.f, P.Yaw, 0.f), P.At, FVector(PatchLength / 100.f, Width / 100.f, 1.f));
        const int32 Index = Foam->AddInstance(Patch, true);
        Foam->SetCustomDataValue(Index, 0, P.Strength * Left, false);
    }
    Foam->MarkRenderStateDirty();
}
