#include "EWPickup.h"
#include "World/EWWorldState.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWPickup::AEWPickup()
{
    bReplicates = true;
    SetReplicateMovement(true);
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    SetRootComponent(Mesh);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
    Mesh->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Mesh->SetStaticMesh(Cube.Object);
    Mesh->SetRelativeScale3D(FVector(.3f)); // Draft world marker; replace in placed Blueprint content.
}

void AEWPickup::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWPickup, ItemDefinition);
    DOREPLIFETIME(AEWPickup, Quantity);
}

AEWPickup* AEWPickup::FindTarget(const AEWCharacter* Character)
{
    return Cast<AEWPickup>(FEWInteractionTargeting::FindTarget(Character));
}

bool AEWPickup::CanInteract_Implementation(AEWCharacter* Character) const
{
    return !IsActorBeingDestroyed() && !bTransferInProgress && IsValid(Character)
        && Character->GetWorld() == GetWorld() && IsValid(ItemDefinition) && Quantity > 0
        && Character->GetInventoryComponent() && Character->GetController()
        && Character->GetController()->GetPawn() == Character
        && (!GetOwner() || GetOwner() == Character || GetOwner() == Character->GetController());
}

FText AEWPickup::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    return ItemDefinition ? FText::Format(NSLOCTEXT("Elitewake", "PickupPrompt", "Pick up {0}"),
        ItemDefinition->DisplayName) : FText::GetEmpty();
}

bool AEWPickup::Interact_Implementation(AEWCharacter* Character)
{
    return TryPickup(Character) > 0;
}

void AEWPickup::RestoreSaved(int32 InQuantity)
{
    if (!HasAuthority()) return;
    if (InQuantity <= 0) { Destroy(); return; }
    Quantity = InQuantity;
    ForceNetUpdate();
}

int32 AEWPickup::TryPickup(AEWCharacter* Character)
{
    if (!HasAuthority() || IsActorBeingDestroyed() || bTransferInProgress || !IsValid(Character)
        || !Character->HasAuthority() || Character->GetWorld() != GetWorld()
        || !ItemDefinition || Quantity <= 0 || !Character->GetController()
        || Character->GetController()->GetPawn() != Character
        || (GetOwner() && GetOwner() != Character && GetOwner() != Character->GetController())
        || FindTarget(Character) != this) return 0;
    UEWInventoryComponent* Inventory = Character->GetInventoryComponent();
    if (!Inventory) return 0;
    TGuardValue<bool> TransferGuard(bTransferInProgress, true);
    const int32 Added = Inventory->AddItem(ItemDefinition, Quantity);
    Quantity -= Added;
    if (Added > 0) UEWWorldStateSubsystem::Touch(this);
    if (Added > 0)
    {
        FEWGatherGain Gain;
        Gain.Item = ItemDefinition;
        Gain.Count = Added;
        Character->PlayGatherMotion(UsesBushReach(), {Gain});
    }
    if (Quantity <= 0) Destroy();
    else if (Added > 0) ForceNetUpdate();
    return Added;
}
