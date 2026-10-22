// Copyright Epic Games, Inc. All Rights Reserved.

#include "EWGameMode.h"
#include "EWExplorationComponent.h"

AEWGameMode::AEWGameMode()
{
	WorldEdge = CreateDefaultSubobject<UEWExplorationComponent>(TEXT("WorldEdge"));
}
