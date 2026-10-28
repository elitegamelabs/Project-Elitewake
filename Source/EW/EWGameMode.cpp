// Copyright Epic Games, Inc. All Rights Reserved.

#include "EWGameMode.h"
#include "EWExplorationComponent.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "World/EWBuildSave.h"

AEWGameMode::AEWGameMode()
{
	WorldEdge = CreateDefaultSubobject<UEWExplorationComponent>(TEXT("WorldEdge"));
}

bool AEWGameMode::KeepsStructures() const
{
	const UWorld* World = GetWorld();
	return World && !World->IsPlayInEditor() && (World->GetNetMode() == NM_ListenServer || World->GetNetMode() == NM_DedicatedServer);
}

void AEWGameMode::BeginPlay()
{
	Super::BeginPlay();
	if (!KeepsStructures()) return;
	UEWBuildSave::RestoreWorld(GetWorld());
	GetWorldTimerManager().SetTimer(StructureSaveTimer, [this]() { UEWBuildSave::SaveWorld(GetWorld()); }, 60.f, true);      // every minute (tuning)
}

void AEWGameMode::EndPlay(const EEndPlayReason::Type Reason)
{
	if (KeepsStructures()) UEWBuildSave::SaveWorld(GetWorld());
	Super::EndPlay(Reason);
}
