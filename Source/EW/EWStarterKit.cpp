#include "EWStarterKit.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "Ships/EWShip.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerState.h"

AEWStarterKit::AEWStarterKit()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = .25f;
    SetHidden(true);
}

void AEWStarterKit::BeginPlay()
{
    Super::BeginPlay();
    if (!HasAuthority()) return;
    for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
    {
        UEWInventoryComponent* Hold = It->GetCargo();
        if (!Hold) continue;
        for (const FEWStarterKitItem& Entry : ShipCargo)
        {
            if (Entry.Item) Hold->AddItem(Entry.Item, Entry.Quantity);
        }
    }
}

void AEWStarterKit::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority()) return;
    for (TActorIterator<AEWCharacter> It(GetWorld()); It; ++It) GiveKit(*It);
}

bool AEWStarterKit::GiveKit(AEWCharacter* Survivor)
{
    APlayerState* Player = Survivor ? Survivor->GetPlayerState() : nullptr;
    UEWInventoryComponent* Inventory = Survivor ? Survivor->GetInventoryComponent() : nullptr;
    if (!HasAuthority() || !Player || !Inventory || Given.Contains(Player)) return false;
    Given.Add(Player);
    for (const FEWStarterKitItem& Entry : Items)
    {
        if (Entry.Item) Inventory->AddItem(Entry.Item, Entry.Quantity);
    }
    return true;
}
