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

	/** The world's edge and its growth (see UEWExplorationComponent). */
	UPROPERTY(VisibleAnywhere, Category="World")
	TObjectPtr<class UEWExplorationComponent> WorldEdge;
};



