#include "EWGameState.h"

#include "Ships/EWShip.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"

AEWGameState::AEWGameState()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 2.f;
}

void AEWGameState::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority()) return;

    TArray<FEWShipMapEntry> Current;
    for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
    {
        if (It->IsActorBeingDestroyed()) continue;
        FEWShipMapEntry Entry;
        Entry.Location = It->GetActorLocation();
        Entry.Yaw = It->GetActorRotation().Yaw;
        Entry.Name = It->GetShipName();
        Current.Add(Entry);
    }
    ShipsOnMap = MoveTemp(Current);
    ForceNetUpdate();
}

void AEWGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWGameState, ShipsOnMap);
}
