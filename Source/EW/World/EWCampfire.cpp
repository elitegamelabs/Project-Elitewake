#include "World/EWCampfire.h"
#include "EWGameInstance.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "World/EWSafeZone.h"
#include "World/EWDayNight.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PhysicsVolume.h"
#include "Net/UnrealNetwork.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

AEWCampfire::AEWCampfire()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = .05f;
    Ring = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Ring"));
    SetRootComponent(Ring);
    Ring->SetCollisionProfileName(TEXT("BlockAll"));
    Flame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Flame"));
    Flame->SetupAttachment(Ring);
    Flame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Flame->SetCastShadow(false);
    Flame->SetRelativeLocation(FVector(0, 0, 8));
    Flame->SetRelativeScale3D(FVector(3.2f, 3.2f, 2.6f));
    Glow = CreateDefaultSubobject<UPointLightComponent>(TEXT("Glow"));
    Glow->SetupAttachment(Ring);
    Glow->SetRelativeLocation(FVector(0, 0, 60));
    Glow->SetLightColor(FLinearColor(1.f, .52f, .2f));
    Glow->SetIntensityUnits(ELightUnits::Candelas);
    Glow->SetIntensity(GlowCandelas);
    Glow->SetAttenuationRadius(GlowRadius);
    Crackle = CreateDefaultSubobject<UAudioComponent>(TEXT("Crackle"));
    Crackle->SetupAttachment(Ring);
    Crackle->bAutoActivate = false;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> RingMesh(TEXT("/Game/Elitewake/World/Campfire/SM_Campfire_v1.SM_Campfire_v1"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> FlameMesh(TEXT("/Game/Elitewake/World/Tools/SM_TorchFlame_v1.SM_TorchFlame_v1"));
    static ConstructorHelpers::FObjectFinder<USoundBase> Loop(TEXT("/Game/Elitewake/Audio/World/S_CampfireLoop_v1.S_CampfireLoop_v1"));
    static ConstructorHelpers::FObjectFinder<UEWItemDefinition> Wood(TEXT("/Game/Elitewake/Items/Testing/DA_TestWood.DA_TestWood"));
    if (RingMesh.Succeeded()) Ring->SetStaticMesh(RingMesh.Object);
    if (FlameMesh.Succeeded()) Flame->SetStaticMesh(FlameMesh.Object);
    if (Loop.Succeeded()) Crackle->SetSound(Loop.Object);
    if (Wood.Succeeded()) FuelItem = Wood.Object;
    CampfireItem = TSoftObjectPtr<UEWItemDefinition>(FSoftObjectPath(TEXT("/Game/Elitewake/Items/Building/DA_Campfire.DA_Campfire")));
}

void AEWCampfire::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWCampfire, bLit);
}

void AEWCampfire::BeginPlay()
{
    Super::BeginPlay();
    ShowFire();
}

void AEWCampfire::SetFuel(float Seconds)
{
    if (!HasAuthority()) return;
    FuelLeft = FMath::Clamp(Seconds, 0.f, MaxFuel);
    const bool bNowLit = FuelLeft > 0.f;
    if (bNowLit != bLit)
    {
        bLit = bNowLit;
        ForceNetUpdate();
        ShowFire();
    }
}

void AEWCampfire::OnRep_Lit()
{
    ShowFire();
}

void AEWCampfire::ShowFire()
{
    Flame->SetVisibility(bLit);
    Glow->SetVisibility(bLit);
    if (!Crackle || GetNetMode() == NM_DedicatedServer) return;
    if (bLit && !Crackle->IsPlaying()) Crackle->Play(FMath::FRandRange(0.f, 10.f));
    else if (!bLit && Crackle->IsPlaying()) Crackle->Stop();
}

void AEWCampfire::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (HasAuthority() && bLit) SetFuel(FuelLeft - DeltaSeconds);
    if (bLit && GetNetMode() != NM_DedicatedServer)
    {
        if (Crackle) Crackle->SetVolumeMultiplier(UEWGameInstance::GetSoundEffectsVolume());
        // A living fire's light wavers (cosmetic, each machine its own), and in daylight it barely shows.
        const float T = GetWorld()->GetTimeSeconds();
        const UEWDayNightSubsystem* Clock = UEWDayNightSubsystem::GetForWorld(this);
        const float Daylight = Clock && Clock->IsDay() ? DaylightShare : 1.f;
        Glow->SetIntensity(GlowCandelas * Daylight * (.82f + .1f * FMath::Sin(T * 7.3f) + .08f * FMath::Sin(T * 17.1f + 1.3f)));
    }
}

bool AEWCampfire::IsLitFireNear(const AActor* Actor)
{
    if (!Actor || !Actor->GetWorld()) return false;
    for (TActorIterator<AEWCampfire> It(Actor->GetWorld()); It; ++It)
        if (It->bLit && !It->IsActorBeingDestroyed() && FVector::Dist(It->GetActorLocation(), Actor->GetActorLocation()) <= CookReach) return true;
    return false;
}

bool AEWCampfire::FindPlacement(const AEWCharacter* Survivor, FTransform& Out, bool& bHit)
{
    bHit = false;
    UWorld* World = Survivor ? Survivor->GetWorld() : nullptr;
    if (!World || !Survivor->GetController()) return false;
    FVector Eye; FRotator View;
    Survivor->GetActorEyesViewPoint(Eye, View);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWCampfirePlace), false, Survivor);
    FHitResult Hit;
    // Where the survivor looks, if that is close; else the ground a couple of metres ahead of them.
    if (!World->LineTraceSingleByChannel(Hit, Eye, Eye + View.Vector() * PlaceReach, ECC_Visibility, Query))
    {
        const FVector Ahead = Survivor->GetActorLocation() + FRotator(0.f, View.Yaw, 0.f).Vector() * 200.f;
        if (!World->LineTraceSingleByChannel(Hit, Ahead + FVector(0, 0, 150), Ahead - FVector(0, 0, 300), ECC_Visibility, Query)) return false;
    }
    bHit = true;
    Out = FTransform(FRotator(0.f, View.Yaw, 0.f), Hit.ImpactPoint);
    // Bare ground only: the island, not a creature, a pickup or a ship.
    const UPrimitiveComponent* Ground = Hit.GetComponent();
    if (!Ground || Ground->Mobility != EComponentMobility::Static || Hit.GetActor()->Implements<UEWInteractable>()) return false;
    if (Hit.ImpactNormal.Z < FMath::Cos(FMath::DegreesToRadians(MaxSlopeDegrees))) return false;
    if (FVector::Dist2D(Hit.ImpactPoint, Survivor->GetActorLocation()) > PlaceReach) return false;
    for (TActorIterator<APhysicsVolume> It(World); It; ++It)
        if (It->bWaterVolume && It->EncompassesPoint(Hit.ImpactPoint + FVector(0, 0, 20))) return false;
    if (AEWSafeZone::IsBuildingBlocked(World, Hit.ImpactPoint)) return false;
    for (TActorIterator<AEWCampfire> It(World); It; ++It)
        if (FVector::Dist(It->GetActorLocation(), Hit.ImpactPoint) < 250.f) return false;
    FCollisionQueryParams Clear(SCENE_QUERY_STAT(EWCampfireClear), false, Survivor);
    return !World->OverlapAnyTestByChannel(Hit.ImpactPoint + FVector(0, 0, ClearRadius + 15.f), FQuat::Identity, ECC_Pawn,
        FCollisionShape::MakeSphere(ClearRadius), Clear);
}

FEWSavedCampfire AEWCampfire::CaptureForSave() const
{
    FEWSavedCampfire Saved;
    Saved.Transform = GetActorTransform();
    Saved.FuelLeft = FuelLeft;
    return Saved;
}

bool AEWCampfire::HasFuelFor(const AEWCharacter* Survivor) const
{
    const UEWInventoryComponent* Pack = Survivor ? Survivor->GetInventoryComponent() : nullptr;
    return Pack && FuelItem && Pack->GetItemCount(FuelItem) > 0;
}

bool AEWCampfire::CanInteract_Implementation(AEWCharacter* Survivor) const
{
    if (IsActorBeingDestroyed() || !IsValid(Survivor) || !Survivor->GetController() || Survivor->GetController()->GetPawn() != Survivor
        || !Survivor->GetSurvivalComponent() || Survivor->GetSurvivalComponent()->GetHealth() <= 0.f) return false;
    // Wood to feed it; or, cold, it can be taken up. A burning fire with nothing to add asks nothing.
    return HasFuelFor(Survivor) || !bLit;
}

FText AEWCampfire::GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const
{
    if (HasFuelFor(Survivor))
        return bLit ? NSLOCTEXT("Elitewake", "CampfireFeed", "Add wood to the fire") : NSLOCTEXT("Elitewake", "CampfireLight", "Light the fire (1 Wood)");
    return NSLOCTEXT("Elitewake", "CampfireTakeUp", "Take up the cold campfire");
}

EEWInteractionMode AEWCampfire::GetInteractionModeFor_Implementation(AEWCharacter* Survivor) const
{
    return HasFuelFor(Survivor) ? EEWInteractionMode::Press : EEWInteractionMode::Hold;
}

bool AEWCampfire::Interact_Implementation(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !CanInteract_Implementation(Survivor) || FEWInteractionTargeting::FindTarget(Survivor) != this) return false;
    UEWInventoryComponent* Pack = Survivor->GetInventoryComponent();
    if (HasFuelFor(Survivor))
    {
        if (Pack->RemoveItem(FuelItem, 1) != 1) return false;
        SetFuel((bLit ? FuelLeft : 0.f) + FuelPerWood);
        return true;
    }
    // Cold: taken up whole, if the pack has room for it.
    UEWItemDefinition* Item = CampfireItem.LoadSynchronous();
    if (bLit || !Item || Pack->AddItem(Item, 1) != 1) return false;
    Destroy();
    return true;
}
