#include "EWStarterKit.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "EWItemDefinition.h"
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
        const UEWShipDefinition* Def = It->Definition;
        if (!Hold || !Def) continue;
        for (const FEWStarterKitItem& Entry : ShipCargo)
        {
            // Fittings go only to ships with a mount for them that is not built into the hull.
            const bool bUseful = Entry.Item && (Entry.Item->FittingMountType == EEWShipMountType::None
                || Def->Mounts.ContainsByPredicate([&](const FEWShipMount& Mount)
                    { return UEWShipDefinition::Accepts(Mount, Entry.Item) && !Def->IsBuiltIn(Mount.MountId); }));
            if (bUseful) Hold->AddItem(Entry.Item, Entry.Quantity);
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
