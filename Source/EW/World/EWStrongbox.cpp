#include "World/EWStrongbox.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "EWSurvivalComponent.h"
#include "UObject/ConstructorHelpers.h"

AEWStrongbox::AEWStrongbox()
{
    bReplicates = true;
    Chest = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Chest"));
    RootComponent = Chest;
    // A plain box until the builder gives it the chest (base at the origin).
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Box(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Box.Succeeded()) Chest->SetStaticMesh(Box.Object);
    Chest->SetCollisionProfileName(TEXT("BlockAll"));
}

bool AEWStrongbox::CanAccess(const AEWCharacter* Survivor) const
{
    return IsValid(Survivor) && Survivor->GetSurvivalComponent() && !Survivor->GetSurvivalComponent()->IsDead()
        && FVector::Dist(Survivor->GetActorLocation(), GetActorLocation()) <= Reach;
}

UEWInventoryComponent* AEWStrongbox::StoreOf(const AEWCharacter* Survivor)
{
    const auto* Controller = IsValid(Survivor) ? Cast<AEWPlayerController>(Survivor->GetController()) : nullptr;
    return Controller ? Controller->GetStrongbox() : nullptr;
}

bool AEWStrongbox::CanInteract_Implementation(AEWCharacter* Character) const { return CanAccess(Character); }

FText AEWStrongbox::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    return NSLOCTEXT("Elitewake", "OpenStrongbox", "Open your strongbox");
}

bool AEWStrongbox::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanAccess(Character) || !StoreOf(Character)) return false;
    auto* PC = Cast<AEWPlayerController>(Character->GetController());
    if (!PC) return false;
    PC->ClientOpenContainer(this);
    return true;
}
