#if WITH_DEV_AUTOMATION_TESTS
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWContainerTransferTest, "Elitewake.Inventory.ContainerTransfer",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWContainerTransferTest::RunTest(const FString& Parameters)
{
    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(false)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    auto MakeInventory = [World](const TCHAR* Name)
    {
        AActor* Owner = World->SpawnActor<AActor>();
        auto* Inventory = NewObject<UEWInventoryComponent>(Owner, Name);
        Inventory->RegisterComponent();
        return Inventory;
    };
    UEWInventoryComponent* Carried = MakeInventory(TEXT("Carried"));
    UEWInventoryComponent* Hold = MakeInventory(TEXT("Hold"));
    auto* Wood = NewObject<UEWItemDefinition>(GetTransientPackage());
    Wood->ItemId = TEXT("Test.Wood"); Wood->MaxStackSize = 100; Wood->UnitWeight = .5f;
    auto* Stone = NewObject<UEWItemDefinition>(GetTransientPackage());
    Stone->ItemId = TEXT("Test.Stone"); Stone->MaxStackSize = 100;
    auto* Berry = NewObject<UEWItemDefinition>(GetTransientPackage());
    Berry->ItemId = TEXT("Test.Berry"); Berry->MaxStackSize = 500;
    Berry->Category = EEWItemCategory::Consumable; Berry->FoodKind = EEWFoodKind::Berry; Berry->FreshLifetimeSeconds = 1200.f;
    auto Total = [&](UEWItemDefinition* Item) { return Carried->GetItemCount(Item) + Hold->GetItemCount(Item); };

    // A whole stack moves; nothing is created or lost.
    Carried->AddItem(Wood, 150);
    TestEqual(TEXT("Two wood stacks carried"), Carried->GetUsedSlotCount(), 2);
    TestEqual(TEXT("Move a full stack"), Carried->TransferEntryTo(Hold, 0, 100), 100);
    TestEqual(TEXT("Hold has it"), Hold->GetItemCount(Wood), 100);
    TestEqual(TEXT("Carried keeps the rest"), Carried->GetItemCount(Wood), 50);
    TestEqual(TEXT("Wood conserved"), Total(Wood), 150);

    // A full hold accepts nothing, and nothing leaves the inventory.
    Hold->SetMaxSlots(1);
    TestEqual(TEXT("Full hold refuses more"), Carried->TransferEntryTo(Hold, 0, 50), 0);
    TestEqual(TEXT("Refused wood stays carried"), Carried->GetItemCount(Wood), 50);
    Carried->AddItem(Stone, 10);
    TestEqual(TEXT("Full hold refuses another item"), Carried->TransferEntryTo(Hold, 1, 10), 0);
    Hold->SetMaxSlots(0);
    TestEqual(TEXT("Slots never drop below those in use"), Hold->GetMaxSlotCount(), 1);

    // Partial room: only what fits moves, merging into a partial stack.
    Hold->SetMaxSlots(2);
    TestEqual(TEXT("Move 50 wood into a new slot"), Carried->TransferEntryTo(Hold, 0, 50), 50);
    Carried->AddItem(Wood, 80);
    const int32 WoodIndex = Carried->GetInventoryEntries().IndexOfByPredicate([&](const FEWInventoryEntry& E) { return E.ItemDefinition == Wood; });
    TestEqual(TEXT("Only the 50 that fit the partial stack move"), Carried->TransferEntryTo(Hold, WoodIndex, 80), 50);
    TestEqual(TEXT("30 wood stay carried"), Carried->GetItemCount(Wood), 30);
    TestEqual(TEXT("Wood conserved through partial moves"), Total(Wood), 230);

    // Ageing food keeps its age and stays its own batch, both ways.
    Hold->SetMaxSlots(10);
    Carried->AddItem(Berry, 10);
    Carried->AdvanceFoodAge(600.f);
    Hold->AddItem(Berry, 5);
    const int32 BerryIndex = Carried->GetInventoryEntries().IndexOfByPredicate([&](const FEWInventoryEntry& E) { return E.ItemDefinition == Berry; });
    TestEqual(TEXT("Move the aged berries"), Carried->TransferEntryTo(Hold, BerryIndex, 10), 10);
    const TArray<FEWInventoryEntry> HoldEntries = Hold->GetInventoryEntries();
    const FEWInventoryEntry* Aged = HoldEntries.FindByPredicate([&](const FEWInventoryEntry& E) { return E.ItemDefinition == Berry && E.Quantity == 10; });
    TestNotNull(TEXT("Aged berries stay a separate batch"), Aged);
    TestTrue(TEXT("Aged berries keep their age in the hold"), Aged && Aged->FoodAgeSeconds >= 600.f);
    const int32 AgedIndex = HoldEntries.IndexOfByPredicate([&](const FEWInventoryEntry& E) { return E.ItemDefinition == Berry && E.Quantity == 10; });
    TestEqual(TEXT("Take them back"), Hold->TransferEntryTo(Carried, AgedIndex, 10), 10);
    const FEWInventoryEntry* Back = Carried->GetInventoryEntries().FindByPredicate([&](const FEWInventoryEntry& E) { return E.ItemDefinition == Berry; });
    TestTrue(TEXT("Storing and taking back never refreshes food"), Back && Back->FoodAgeSeconds >= 600.f);
    TestEqual(TEXT("Berries conserved"), Total(Berry), 15);

    // Bad requests move nothing.
    TestEqual(TEXT("Invalid index"), Carried->TransferEntryTo(Hold, 99, 1), 0);
    TestEqual(TEXT("Zero quantity"), Carried->TransferEntryTo(Hold, 0, 0), 0);
    TestEqual(TEXT("Transfer to itself"), Carried->TransferEntryTo(Carried, 0, 1), 0);
    TestEqual(TEXT("No destination"), Carried->TransferEntryTo(nullptr, 0, 1), 0);

    World->DestroyWorld(false);
    return true;
}
#endif
