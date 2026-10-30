#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "World/EWBuildPiece.h"
#include "Ships/EWShip.h"
#include "EWSurvivorSave.generated.h"

class AEWCharacter;
class UEWItemDefinition;

/**
 * Single player's SAVE GAME (Options menu): the survivor as they were, kept for the next Single Player.
 * Kept: the map, where they stand and look, health, hunger and thirst, the inventory (with food ages), what is
 * equipped and the hotbar. Structures built with Build Mode are kept too, and the ships afloat (October 30). Not kept yet (M7): the rest of
 * the world (felled trees, mined rocks, dropped items, fish), so the island comes back fresh around a resumed survivor.
 */
UCLASS(BlueprintType)
class EW_API UEWSurvivorSave : public USaveGame
{
    GENERATED_BODY()
public:
    static inline const TCHAR* Slot = TEXT("Survivor");

    /** Authority only: writes Survivor to the save slot. */
    UFUNCTION(BlueprintCallable, Category="Save")
    static bool SaveSurvivor(AEWCharacter* Survivor, const FString& SlotName = TEXT("Survivor"));
    UFUNCTION(BlueprintPure, Category="Save")
    static bool HasSave(const FString& SlotName = TEXT("Survivor"));
    UFUNCTION(BlueprintCallable, Category="Save")
    static UEWSurvivorSave* LoadSave(const FString& SlotName = TEXT("Survivor"));
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
    /** Level, experience, stat and skill points and the lit stars (October 22). Older saves have none: the survivor then keeps level 1. */
    UPROPERTY(BlueprintReadOnly, Category="Save") int32 Level = 0;
    UPROPERTY(BlueprintReadOnly, Category="Save") int32 Experience = 0;
    UPROPERTY(BlueprintReadOnly, Category="Save") int32 UnspentStatPoints = 0;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<int32> StatPoints;
    /** The purse in Copper (October 29). -1 in an older save: the survivor then keeps the starting purse. */
    UPROPERTY(BlueprintReadOnly, Category="Save") int64 Copper = -1;
    UPROPERTY(BlueprintReadOnly, Category="Save") int32 SkillPoints = 0;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FName> UnlockedSkills;
    /** Everything built with Build Mode (October 27), bases before what stands on them. Older saves have none. */
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWSavedPiece> BuiltPieces;
    /** Every ship afloat (October 30). An older save has none and leaves the map's ships as they are. */
    UPROPERTY(BlueprintReadOnly, Category="Save") bool bHasShips = false;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWSavedShip> Ships;
    /** What the survivor has explored: the map's cleared cells, a bit each, and the square they cover. */
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<uint8> ExploredBits;
    UPROPERTY(BlueprintReadOnly, Category="Save") FVector2D ExploredMin = FVector2D::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Save") float ExploredSize = 0.f;
};
