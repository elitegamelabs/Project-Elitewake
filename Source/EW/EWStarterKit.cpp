#include "EWStarterKit.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "EWItemDefinition.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerState.h"
#include "HAL/IConsoleManager.h"

static TAutoConsoleVariable<int32> CVarTestStarterKit(TEXT("ew.TestStarterKit"), 0,
    TEXT("1 gives each survivor the map's test starter kit (checks and testing only); 0, the normal start, gives nothing."));

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
        const UEWShipDefinition* Def = It->Definition;
        if (!Hold || !Def) continue;
        for (const FEWStarterKitItem& Entry : ShipCargo)
        {
            if (!Entry.Item) continue;
            if (Entry.Item->FittingMountType == EEWShipMountType::None)
            {
                Hold->AddItem(Entry.Item, Entry.Quantity);
                continue;
            }
            // A fitting goes to each ship that can take it, Quantity for every mount that is not built into the hull.
            const int32 Mounts = Def->Mounts.FilterByPredicate([&](const FEWShipMount& Mount)
                { return UEWShipDefinition::Accepts(Mount, Entry.Item) && !Def->IsBuiltIn(Mount.MountId); }).Num();
            if (Mounts > 0) Hold->AddItem(Entry.Item, Entry.Quantity * Mounts);
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
    if (!HasAuthority() || !Player || !Inventory || Given.Contains(Player) || CVarTestStarterKit.GetValueOnGameThread() == 0) return false;
    Given.Add(Player);
    for (const FEWStarterKitItem& Entry : Items)
    {
        if (Entry.Item) Inventory->AddItem(Entry.Item, Entry.Quantity);
    }
    return true;
}
