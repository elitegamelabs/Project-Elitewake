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

	/** The world's edge and its growth (see UEWExplorationComponent). */
	UPROPERTY(VisibleAnywhere, Category="World")
	TObjectPtr<class UEWExplorationComponent> WorldEdge;

private:
	FTimerHandle StructureSaveTimer;
	/** A hosted or dedicated server keeps what players built (not in the editor's Play, not in single player). */
	bool KeepsStructures() const;
};



