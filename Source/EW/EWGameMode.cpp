// Copyright Epic Games, Inc. All Rights Reserved.

#include "EWGameMode.h"
#include "EWExplorationComponent.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "World/EWBuildSave.h"
#include "EWCharacter.h"
#include "EWGameInstance.h"
#include "EWSurvivorSave.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/SecureHash.h"

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
	GetWorldTimerManager().SetTimer(StructureSaveTimer, [this]() { UEWBuildSave::SaveWorld(GetWorld()); SaveAllPlayers(); }, 60.f, true);      // every minute (tuning)
}

void AEWGameMode::EndPlay(const EEndPlayReason::Type Reason)
{
	if (KeepsStructures()) { UEWBuildSave::SaveWorld(GetWorld()); SaveAllPlayers(); }
	Super::EndPlay(Reason);
}

FString AEWGameMode::InitNewPlayer(APlayerController* NewPlayerController, const FUniqueNetIdRepl& UniqueId, const FString& Options, const FString& Portal)
{
	// The stable id a joining game sends (letters and digits only, never trusted beyond naming a save); the host's own is this PC's.
	FString Id = UGameplayStatics::ParseOption(Options, TEXT("EWId"));
	const bool bValid = !Id.IsEmpty() && Id.Len() <= 64 && !Id.Contains(TEXT(" ")) && [&Id]() { for (TCHAR C : Id) if (!FChar::IsAlnum(C)) return false; return true; }();
	if (!bValid) Id = NewPlayerController && NewPlayerController->IsLocalController() ? UEWGameInstance::StablePlayerId() : FString();
	if (NewPlayerController && !Id.IsEmpty()) PlayerIds.Add(NewPlayerController, Id);
	return Super::InitNewPlayer(NewPlayerController, UniqueId, Options, Portal);
}

FString AEWGameMode::PlayerKey(const AController* Player) const
{
	const APlayerState* State = Player ? Player->PlayerState.Get() : nullptr;
	if (!State) return FString();
	// The stable id the player's game sent, else their online identity (which a direct-IP game changes every launch), else their name.
	const FString* Sent = PlayerIds.Find(const_cast<APlayerController*>(Cast<APlayerController>(Player)));
	return Sent ? *Sent : State->GetUniqueId().IsValid() ? State->GetUniqueId()->ToString() : State->GetPlayerName();
}

FString AEWGameMode::PlayerSlot(const APlayerController* Player) const
{
	// Hashed so any characters are safe in a file name.
	const FString Identity = PlayerKey(Player);
	return Identity.IsEmpty() ? FString() : TEXT("ServerSurvivor_") + FMD5::HashAnsiString(*Identity);
}

bool AEWGameMode::SavePlayerSurvivor(APlayerController* Player)
{
	const FString Slot = PlayerSlot(Player);
	auto* Survivor = Player ? Cast<AEWCharacter>(Player->GetPawn()) : nullptr;
	// Not while dead or carried by something not in the save: the last good save stands.
	return HasAuthority() && !Slot.IsEmpty() && Survivor && UEWSurvivorSave::SaveSurvivor(Survivor, Slot, false);
}

bool AEWGameMode::RestorePlayerSurvivor(APlayerController* Player)
{
	const FString Slot = PlayerSlot(Player);
	auto* Survivor = Player ? Cast<AEWCharacter>(Player->GetPawn()) : nullptr;
	if (!HasAuthority() || Slot.IsEmpty() || !Survivor || !UEWSurvivorSave::HasSave(Slot)) return false;
	const UEWSurvivorSave* Save = UEWSurvivorSave::LoadSave(Slot);
	return Save && Save->ApplyTo(Survivor);
}

void AEWGameMode::SaveAllPlayers()
{
	for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
		if (APlayerController* Player = It->Get()) SavePlayerSurvivor(Player);
}

void AEWGameMode::HandleStartingNewPlayer_Implementation(APlayerController* NewPlayer)
{
	Super::HandleStartingNewPlayer_Implementation(NewPlayer);
	// A player who has been here before gets their survivor back as they left it.
	if (KeepsStructures() && RestorePlayerSurvivor(NewPlayer))
		UE_LOG(LogTemp, Log, TEXT("Restored the survivor of %s"), *GetNameSafe(NewPlayer->PlayerState));
}

void AEWGameMode::Logout(AController* Exiting)
{
	if (KeepsStructures()) SavePlayerSurvivor(Cast<APlayerController>(Exiting));
	PlayerIds.Remove(Cast<APlayerController>(Exiting));
	Super::Logout(Exiting);
}
