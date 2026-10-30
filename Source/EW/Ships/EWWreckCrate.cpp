#include "Ships/EWWreckCrate.h"
#include "World/EWWorldState.h"
#include "EWDeathBag.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWPlayerController.h"
#include "EWSurvivalComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Net/UnrealNetwork.h"
#include "Ships/EWShip.h"

AEWWreckCrate::AEWWreckCrate()
{
    bReplicates = true;
    SetReplicateMovement(false);
    PrimaryActorTick.bCanEverTick = true;
    InitialLifeSpan = LifeSeconds;
    Box = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Box"));
    RootComponent = Box;
    // A modelled crate when there is one, else a stand-in cube 70 cm across.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Box->SetStaticMesh(Cube.Object);
    Box->SetWorldScale3D(FVector(.7f, .7f, .55f));
    Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Box->SetCollisionResponseToAllChannels(ECR_Ignore);
    Box->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Contents = CreateDefaultSubobject<UEWInventoryComponent>(TEXT("Contents"));
}

void AEWWreckCrate::BeginPlay()
{
    Super::BeginPlay();
    if (UStaticMesh* Crate = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Elitewake/World/Ships/SM_WreckCrate_v1.SM_WreckCrate_v1"), nullptr, LOAD_Quiet | LOAD_NoWarn))
    {
        Box->SetStaticMesh(Crate);
        Box->SetWorldScale3D(FVector::OneVector);
    }
    BobTime = float(GetTypeHash(GetFName()) % 100) * .07f;
}

FEWSavedContainer AEWWreckCrate::CaptureForSave() const
{
    FEWSavedContainer Saved;
    Saved.bWreckCrate = true;
    Saved.Transform = GetActorTransform();
    if (Contents) Saved.Contents = Contents->Entries;
    Saved.LifeLeft = GetLifeSpan();
    Saved.SurfaceZ = SurfaceZ;
    return Saved;
}

void AEWWreckCrate::RestoreSaved(const FEWSavedContainer& Saved)
{
    if (!HasAuthority() || !Contents) return;
    SurfaceZ = Saved.SurfaceZ;
    Contents->SetMaxSlots(FMath::Max(SlotsPerCrate, Saved.Contents.Num()));
    Contents->Entries = Saved.Contents;
    Contents->HandleInventoryChanged();
    SetLifeSpan(FMath::Max(1.f, Saved.LifeLeft));
    ForceNetUpdate();
}

void AEWWreckCrate::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWWreckCrate, SurfaceZ);
}

void AEWWreckCrate::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    // Riding the swell, a little tilted, on every machine.
    BobTime += DeltaSeconds;
    FVector Here = GetActorLocation();
    Here.Z = SurfaceZ + 8.f * FMath::Sin(BobTime * 1.1f);
    SetActorLocationAndRotation(Here, FRotator(4.f * FMath::Sin(BobTime * .8f), GetActorRotation().Yaw, 5.f * FMath::Sin(BobTime * .9f + 1.f)));
    if (!HasAuthority()) return;
    if (Contents && Contents->GetUsedSlotCount() > 0) bEverFilled = true;
    // Taken clean: it sinks away.
    else if (bEverFilled) Destroy();
}

bool AEWWreckCrate::CanAccess(const AEWCharacter* Character) const
{
    return IsValid(Character) && Character->GetSurvivalComponent() && Character->GetSurvivalComponent()->GetHealth() > 0.f
        && FVector::Dist(Character->GetActorLocation(), GetActorLocation()) <= Reach;
}

bool AEWWreckCrate::CanInteract_Implementation(AEWCharacter* Character) const
{
    return CanAccess(Character);
}

FText AEWWreckCrate::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    return NSLOCTEXT("Elitewake", "OpenWreckCrate", "Open the wreck crate");
}

bool AEWWreckCrate::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanAccess(Character)) return false;
    auto* PC = Cast<AEWPlayerController>(Character->GetController());
    if (!PC) return false;
    PC->ClientOpenContainer(this);
    return true;
}

UEWInventoryComponent* FEWContainerAccess::Inventory(const AActor* Container)
{
    if (const auto* Ship = Cast<AEWShip>(Container)) return Ship->GetCargo();
    if (const auto* Crate = Cast<AEWWreckCrate>(Container)) return Crate->GetContents();
    if (const auto* Bag = Cast<AEWDeathBag>(Container)) return Bag->GetContents();
    return nullptr;
}

bool FEWContainerAccess::CanAccess(const AActor* Container, const AEWCharacter* Survivor)
{
    if (const auto* Ship = Cast<AEWShip>(Container)) return Ship->CanAccessCargo(Survivor);
    if (const auto* Crate = Cast<AEWWreckCrate>(Container)) return Crate->CanAccess(Survivor);
    if (const auto* Bag = Cast<AEWDeathBag>(Container)) return Bag->CanAccess(Survivor);
    return false;
}
