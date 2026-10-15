#include "World/EWSnowfall.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"

UEWSnowfallComponent::UEWSnowfallComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    SetIsReplicatedByDefault(false);
}

bool UEWSnowfallComponent::ShouldSnow() const
{
    const APawn* Pawn = Cast<APawn>(GetOwner());
    if (!Pawn || !Pawn->IsLocallyControlled()) return false;
    const UEWSurvivalComponent* Survival = Pawn->FindComponentByClass<UEWSurvivalComponent>();
    return Survival && Survival->GetClimate().Region == EEWRegion::Winter;
}

bool UEWSnowfallComponent::UnderCover(const FVector& Eye) const
{
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWSnowCover), false, GetOwner());
    FHitResult Hit;
    return GetWorld()->LineTraceSingleByChannel(Hit, Eye, Eye + FVector(0, 0, 4000), ECC_Visibility, Query);
}

void UEWSnowfallComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    const APawn* Pawn = Cast<APawn>(GetOwner());
    const APlayerController* Player = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
    bool bWant = ShouldSnow() && Player && Player->PlayerCameraManager;
    FVector Eye = FVector::ZeroVector;
    if (bWant)
    {
        Eye = Player->PlayerCameraManager->GetCameraLocation();
        // Looking up for a roof twice a second is enough.
        CoverCheckIn -= DeltaTime;
        if (CoverCheckIn <= 0.f)
        {
            CoverCheckIn = .5f;
            bCovered = UnderCover(Eye);
        }
        bWant = !bCovered;
    }
    if (bWant && !Flakes)
    {
        UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Elitewake/World/Weather/SM_Snowfall_v1.SM_Snowfall_v1"));
        if (Mesh)
        {
            Flakes = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("SnowfallFlakes"));
            Flakes->SetStaticMesh(Mesh);
            Flakes->SetUsingAbsoluteLocation(true);
            Flakes->SetUsingAbsoluteRotation(true);
            Flakes->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Flakes->SetCastShadow(false);
            // The material moves every flake; keep the field from being culled as it does.
            Flakes->SetBoundsScale(4.f);
            Flakes->RegisterComponent();
        }
    }
    if (Flakes)
    {
        if (bWant) Flakes->SetWorldLocationAndRotation(Eye, FRotator::ZeroRotator);
        Flakes->SetVisibility(bWant);
    }
    bSnowing = bWant && Flakes;
}

void UEWSnowfallComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (Flakes) Flakes->DestroyComponent();
    Flakes = nullptr;
    Super::EndPlay(EndPlayReason);
}
