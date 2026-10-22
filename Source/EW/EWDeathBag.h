#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWDeathBag.generated.h"

class AEWCharacter;
class UEWInventoryComponent;
class UStaticMeshComponent;

/**
 * What a survivor left where they died: everything they carried, in a bag that stays 30 real minutes (owner, October 22). Anyone beside it opens it like a
 * crate and takes what they want; an emptied bag vanishes, and every bag is gone after LifeSeconds. The server owns its contents.
 */
UCLASS(NotPlaceable)
class EW_API AEWDeathBag : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWDeathBag();
    virtual void Tick(float DeltaSeconds) override;

    /** Owner's decision: a dropped bag stays recoverable for 30 real minutes. */
    static constexpr float LifeSeconds = 30.f * 60.f;
    /** How close a survivor must be to reach into it, cm (tuning). */
    static constexpr float Reach = 350.f;

    UFUNCTION(BlueprintPure, Category="Death")
    UEWInventoryComponent* GetContents() const { return Contents; }
    UFUNCTION(BlueprintPure, Category="Death")
    bool CanAccess(const AEWCharacter* Character) const;
    /** Authority only: moves everything the survivor carries into a new bag where they stand. Returns null (and spawns nothing) when they carry nothing. */
    static AEWDeathBag* DropInventoryOf(AEWCharacter* Dead, const FVector& Where);

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

private:
    UPROPERTY(VisibleAnywhere, Category="Death")
    TObjectPtr<UStaticMeshComponent> Sack;
    UPROPERTY(VisibleAnywhere, Category="Death")
    TObjectPtr<UEWInventoryComponent> Contents;
    bool bEverFilled = false;
};
