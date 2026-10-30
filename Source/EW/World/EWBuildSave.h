#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "World/EWBuildPiece.h"
#include "Ships/EWShip.h"
#include "EWBuildSave.generated.h"

/**
 * The server's own save of what players built and the ships afloat (MULTIPLAYER_RULES: the server persists buildings; M7: ships). Separate from the single-player
 * Save Game, which keeps the pieces inside the survivor's save. AEWGameMode restores it when a hosted or dedicated server starts
 * and saves it every minute and when the world ends (not in the editor's Play, so test runs leave no structures behind).
 */
UCLASS(BlueprintType)
class EW_API UEWBuildSave : public USaveGame
{
    GENERATED_BODY()
public:
    static inline const TCHAR* ServerSlot = TEXT("ServerStructures");

    /** Authority only: writes every built piece in World to the slot. */
    UFUNCTION(BlueprintCallable, Category="Save") static bool SaveWorld(UWorld* World, const FString& SlotName = TEXT("ServerStructures"));
    /** Authority only: builds what the slot holds, if the map matches and nothing is built yet. Returns the number built. */
    UFUNCTION(BlueprintCallable, Category="Save") static int32 RestoreWorld(UWorld* World, const FString& SlotName = TEXT("ServerStructures"));

    UPROPERTY(BlueprintReadOnly, Category="Save") FString MapPath;
    UPROPERTY(BlueprintReadOnly, Category="Save") FDateTime SavedAt;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWSavedPiece> Pieces;
    /** The ships afloat (October 30). An older save has none and leaves the map's ships as they are. */
    UPROPERTY(BlueprintReadOnly, Category="Save") bool bHasShips = false;
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWSavedShip> Ships;
};
