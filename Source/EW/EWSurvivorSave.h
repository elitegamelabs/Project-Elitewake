#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "EWSurvivorSave.generated.h"

class AEWCharacter;
class UEWItemDefinition;

/**
 * Single player's SAVE GAME (Options menu): the survivor as they were, kept for the next Single Player.
 * Kept: the map, where they stand and look, health, hunger and thirst, the inventory (with food ages), what is
 * equipped and the hotbar. Not kept yet (M7): the world itself (felled trees, mined rocks, dropped items, fish,
 * ships, structures), so the island comes back fresh around a resumed survivor.
 */
UCLASS(BlueprintType)
class EW_API UEWSurvivorSave : public USaveGame
{
    GENERATED_BODY()
public:
    static inline const TCHAR* Slot = TEXT("Survivor");

    /** Authority only: writes Survivor to the save slot. */
    UFUNCTION(BlueprintCallable, Category="Save")
    static bool SaveSurvivor(AEWCharacter* Survivor);
    UFUNCTION(BlueprintPure, Category="Save")
    static bool HasSave();
    UFUNCTION(BlueprintCallable, Category="Save")
    static UEWSurvivorSave* LoadSave();
    /** Authority only: puts Survivor back as saved, if the save was made on Survivor's map. */
    UFUNCTION(BlueprintCallable, Category="Save")
    bool ApplyTo(AEWCharacter* Survivor) const;

    UPROPERTY(BlueprintReadOnly, Category="Save") FString MapPath;
    UPROPERTY(BlueprintReadOnly, Category="Save") FDateTime SavedAt;
    UPROPERTY(BlueprintReadOnly, Category="Save") FVector Location = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Save") FRotator Facing = FRotator::ZeroRotator;
    UPROPERTY(BlueprintReadOnly, Category="Save") float Health = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Save") float Hunger = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Save") float Hydration = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWInventoryEntry> Inventory;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWEquipmentEntry> Equipment;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<TObjectPtr<UEWItemDefinition>> Hotbar;
};
