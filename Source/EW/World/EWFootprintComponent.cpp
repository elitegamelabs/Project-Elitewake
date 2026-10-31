#include "World/EWFootprintComponent.h"
#include "World/EWClimateRegion.h"
#include "Components/DecalComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
    const TCHAR* const PrintMaterialPath = TEXT("/Game/Elitewake/World/Footprints/M_Footprint_v1.M_Footprint_v1");
    constexpr float SeaZ = -65.f;
    constexpr float BeachTopZ = SeaZ + 70.f;    // the sand of a beach on the Plains and in the Jungle: the first 70 cm above the water, about 11 m inland (tuning)
    constexpr float PrintHalfLength = 17.f, PrintHalfWidth = 7.f;   // cm
}

UEWFootprintComponent::UEWFootprintComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UEWFootprintComponent::BeginPlay()
{
    Super::BeginPlay();
    PrintMaterial = LoadObject<UMaterialInterface>(nullptr, PrintMaterialPath);
    SetComponentTickEnabled(PrintMaterial && !IsNetMode(NM_DedicatedServer));
}

void UEWFootprintComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    for (FPrint& Print : Prints) if (Print.Decal.IsValid()) Print.Decal->DestroyComponent();
    Prints.Reset();
    Super::EndPlay(Reason);
}

EEWFootSurface UEWFootprintComponent::SurfaceAt(const UObject* WorldContext, const FVector& Location)
{
    const EEWRegion Region = AEWClimateRegion::SampleClimate(WorldContext, Location).Region;
    if (Region == EEWRegion::Winter) return EEWFootSurface::Snow;
    if (Region == EEWRegion::Swamp) return EEWFootSurface::Mud;
    if (Region == EEWRegion::Desert || Location.Z < BeachTopZ) return EEWFootSurface::Sand;
    return EEWFootSurface::Firm;
}

int32 UEWFootprintComponent::GetLastingPrintCount() const
{
    int32 Count = 0;
    for (const FPrint& Print : Prints) if (Print.bLasting && Print.Vanishing < 0.f) ++Count;
    return Count;
}

void UEWFootprintComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    UpdatePrints(DeltaSeconds);
    const ACharacter* Character = Cast<ACharacter>(GetOwner());
    const UCharacterMovementComponent* Movement = Character ? Character->GetCharacterMovement() : nullptr;
    if (!Movement || !Movement->IsMovingOnGround() || Movement->IsSwimming()) { bHavePrint = false; return; }
    const FVector Velocity = Movement->Velocity * FVector(1, 1, 0);
    const float Speed = Velocity.Size();
    if (Speed < 30.f) return;
    const FVector Here = Character->GetActorLocation();
    if (!bHavePrint) { LastPrintAt = Here; bHavePrint = true; MakePrint(); return; }
    // A stride is longer at a run.
    const float Stride = Speed > 450.f ? 120.f : 75.f;
    if (FVector::DistXY(Here, LastPrintAt) >= Stride) { LastPrintAt = Here; MakePrint(); }
}

void UEWFootprintComponent::MakePrint()
{
    const ACharacter* Character = Cast<ACharacter>(GetOwner());
    UWorld* World = GetWorld();
    if (!Character || !World || !PrintMaterial) return;
    const FVector Heading = (Character->GetCharacterMovement()->Velocity * FVector(1, 1, 0)).GetSafeNormal();
    if (Heading.IsNearlyZero()) return;
    const FVector Right = FVector::CrossProduct(FVector::UpVector, Heading);
    bRightFoot = !bRightFoot;
    const FVector Foot = Character->GetActorLocation() + Right * (bRightFoot ? 11.f : -11.f);
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(Footprint), false, Character);
    if (!World->LineTraceSingleByChannel(Hit, Foot + FVector(0, 0, 40), Foot - FVector(0, 0, 200), ECC_Visibility, Params)) return;
    if (Hit.ImpactPoint.Z <= SeaZ || Hit.ImpactNormal.Z < .6f) return;   // not under the water, not on a cliff face
    const EEWFootSurface Surface = SurfaceAt(this, Hit.ImpactPoint);
    // The print's top points the way the survivor is heading; its depth runs down through the ground.
    const FRotator Rotation = FRotationMatrix::MakeFromXZ(-Hit.ImpactNormal, Heading).Rotator();
    UDecalComponent* Decal = UGameplayStatics::SpawnDecalAtLocation(World, PrintMaterial,
        FVector(30.f, PrintHalfWidth, PrintHalfLength), Hit.ImpactPoint + Hit.ImpactNormal * 2.f, Rotation, 0.f);
    if (!Decal) return;
    Decal->SetFadeScreenSize(0.f);
    UMaterialInstanceDynamic* Material = Decal->CreateDynamicMaterialInstance();
    if (Material)
    {
        // Black on firm ground; snow's shows blue-grey, sand's brown, mud's the darkest of the three.
        const FLinearColor Colors[] = { FLinearColor(0.f, 0.f, 0.f), FLinearColor(.18f, .22f, .3f), FLinearColor(.03f, .02f, .01f), FLinearColor(.2f, .13f, .06f) };
        Material->SetVectorParameterValue(TEXT("Tint"), Colors[int32(Surface)]);
        Material->SetScalarParameterValue(TEXT("Opacity"), 1.f);
    }
    FPrint Print;
    Print.Decal = Decal;
    Print.Material = Material;
    Print.bLasting = Surface != EEWFootSurface::Firm;
    Print.Lifetime = Print.bLasting ? LastingSeconds : FirmFadeSeconds;
    Prints.Add(Print);
    LastSurface = Surface;
    ++PrintsMade;
    // In snow, mud and sand only the last few stay: the oldest vanishes as a new print is made.
    int32 Lasting = 0;
    for (int32 I = Prints.Num() - 1; I >= 0; --I)
    {
        if (!Prints[I].bLasting || Prints[I].Vanishing >= 0.f) continue;
        if (++Lasting > MaxLastingPrints) Prints[I].Vanishing = VanishSeconds;
    }
}

void UEWFootprintComponent::UpdatePrints(float DeltaSeconds)
{
    for (int32 I = Prints.Num() - 1; I >= 0; --I)
    {
        FPrint& Print = Prints[I];
        Print.Age += DeltaSeconds;
        float Opacity;
        bool bGone = false;
        if (Print.Vanishing >= 0.f)
        {
            Print.Vanishing -= DeltaSeconds;
            Opacity = FMath::Clamp(Print.Vanishing / VanishSeconds, 0.f, 1.f);
            bGone = Print.Vanishing <= 0.f;
        }
        else
        {
            // A print on firm ground holds for a moment, then fades; a lasting one fades over its last few seconds.
            const float FadeSeconds = Print.bLasting ? 6.f : Print.Lifetime * .7f;
            Opacity = FMath::Clamp((Print.Lifetime - Print.Age) / FadeSeconds, 0.f, 1.f);
            bGone = Print.Age >= Print.Lifetime;
        }
        if (bGone || !Print.Decal.IsValid())
        {
            if (Print.Decal.IsValid()) Print.Decal->DestroyComponent();
            Prints.RemoveAt(I);
            continue;
        }
        if (Print.Material.IsValid() && !FMath::IsNearlyEqual(Opacity, Print.Opacity, .02f))
        {
            Print.Opacity = Opacity;
            Print.Material->SetScalarParameterValue(TEXT("Opacity"), Opacity);
        }
    }
}
