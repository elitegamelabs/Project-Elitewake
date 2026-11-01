#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWStrongbox.generated.h"

class AEWCharacter;
class UEWInventoryComponent;
class UStaticMeshComponent;

/**
 * Saltreach's strongbox by the warehouse (CLAUDE.md Phase 1 slice 5: storage). Every survivor who opens it sees only their own
 * store: the goods are not in the box but on the survivor's player (AEWPlayerController::GetStrongbox), so they outlast death,
 * replicate to that player alone and are saved with the survivor. E beside it opens the store beside the pack, like a ship's hold.
 * Placed, with its oak-and-iron chest, by Scripts/Setup/build_saltreach_welcome.py.
 */
UCLASS()
class EW_API AEWStrongbox : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWStrongbox();

    /** How close a survivor must be to reach into it, cm (tuning). */
    static constexpr float Reach = 300.f;

    UFUNCTION(BlueprintPure, Category="Strongbox") bool CanAccess(const AEWCharacter* Survivor) const;
    /** The survivor's own store, or null (no player, or not yet replicated). */
    UFUNCTION(BlueprintPure, Category="Strongbox") static UEWInventoryComponent* StoreOf(const AEWCharacter* Survivor);

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

private:
    UPROPERTY(VisibleAnywhere, Category="Strongbox") TObjectPtr<UStaticMeshComponent> Chest;
};
