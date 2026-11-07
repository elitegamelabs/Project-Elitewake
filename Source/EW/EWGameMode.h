// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "EWGameMode.generated.h"

/**
 *  Simple GameMode for a third person game
 */
UCLASS(abstract)
class AEWGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	
	/** Constructor */
	AEWGameMode();
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual void HandleStartingNewPlayer_Implementation(APlayerController* NewPlayer) override;
	virtual void Logout(AController* Exiting) override;
	virtual FString InitNewPlayer(APlayerController* NewPlayerController, const FUniqueNetIdRepl& UniqueId, const FString& Options, const FString& Portal) override;

	/** A hosted game keeps each player's survivor (owner, October 30: friends keep their progress when they rejoin): saved when they
	 *  leave and every minute, given back when they join again; the world itself is kept by UEWBuildSave. Keyed by the player's
	 *  online identity on this host. Authority only. */
	UFUNCTION(BlueprintCallable, Category="Save")
	bool SavePlayerSurvivor(APlayerController* Player);
	UFUNCTION(BlueprintCallable, Category="Save")
	bool RestorePlayerSurvivor(APlayerController* Player);
	/** The save slot a player's survivor is kept in on this host: by the stable id their game sent (EWId), else their online identity. */
	UFUNCTION(BlueprintPure, Category="Save")
	FString PlayerSlot(const APlayerController* Player) const;
	/** A player's stable key on this host (what PlayerSlot hashes): the id their game sent, else their online identity, else their
	 *  name. Ships keep their owner by it. */
	FString PlayerKey(const AController* Player) const;

	/** The world's edge and its growth (see UEWExplorationComponent). */
	UPROPERTY(VisibleAnywhere, Category="World")
	TObjectPtr<class UEWExplorationComponent> WorldEdge;

private:
	FTimerHandle StructureSaveTimer;
	/** A hosted or dedicated server keeps what players built (not in the editor's Play, not in single player). */
	bool KeepsStructures() const;
	void SaveAllPlayers();
	/** Each player's stable id as their game sent it when joining (the host's own: this PC's). */
	TMap<TWeakObjectPtr<APlayerController>, FString> PlayerIds;
};



