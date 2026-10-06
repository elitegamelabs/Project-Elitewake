#include "EWPickup.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
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
    if (!IsValid(Character) || !Character->GetWorld() || !Character->GetController()
        || Character->GetController()->GetPawn() != Character) return nullptr;
    FVector Eye; FRotator Rotation;
    Character->GetActorEyesViewPoint(Eye, Rotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWPickupInteraction), false, Character);
    FHitResult Hit;
    Character->GetWorld()->LineTraceSingleByChannel(Hit, Eye,
        Eye + Rotation.Vector() * InteractionRange, ECC_Visibility, Query);
    return Cast<AEWPickup>(Hit.GetActor());
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
    if (Quantity <= 0) Destroy();
    else if (Added > 0) ForceNetUpdate();
    return Added;
}
