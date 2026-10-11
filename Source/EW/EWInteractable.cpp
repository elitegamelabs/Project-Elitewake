#include "EWInteractable.h"
#include "EWCharacter.h"
#include "Ships/EWShip.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"

bool IEWInteractable::CanInteract_Implementation(AEWCharacter* Character) const { return false; }
FText IEWInteractable::GetInteractionPrompt_Implementation(AEWCharacter* Character) const { return FText::GetEmpty(); }
EEWInteractionMode IEWInteractable::GetInteractionMode_Implementation() const { return EEWInteractionMode::Press; }
float IEWInteractable::GetHoldDuration_Implementation() const { return 1.f; }
bool IEWInteractable::Interact_Implementation(AEWCharacter* Character) { return false; }

AActor* FEWInteractionTargeting::FindTarget(const AEWCharacter* Character)
{
    if (!IsValid(Character) || !Character->GetWorld() || !Character->GetController()
        || Character->GetController()->GetPawn() != Character) return nullptr;
    // Leaving the helm does not depend on where the helmsman looks.
    if (IsValid(Character->GetHelmShip())) return Character->GetHelmShip();
    FVector Eye; FRotator Rotation;
    Character->GetActorEyesViewPoint(Eye, Rotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWInteraction), false, Character);
    FHitResult Hit;
    Character->GetWorld()->LineTraceSingleByChannel(Hit, Eye,
        Eye + Rotation.Vector() * Range, ECC_Visibility, Query);
    AActor* Target = Hit.GetActor();
    return IsValid(Target) && !Target->IsActorBeingDestroyed()
        && Target->Implements<UEWInteractable>() ? Target : nullptr;
}
