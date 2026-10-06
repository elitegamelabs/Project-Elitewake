#if WITH_DEV_AUTOMATION_TESTS
#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"
#include "Engine/AssetManager.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWEquipmentTransferTest, "Elitewake.Inventory.EquipmentTransfer",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWEquipmentTransferTest::RunTest(const FString& Parameters)
{
    AActor* Owner = NewObject<AActor>();
    auto* Inventory = NewObject<UEWInventoryComponent>(Owner); Owner->AddInstanceComponent(Inventory);
    auto* Equipment = NewObject<UEWEquipmentComponent>(Owner); Owner->AddInstanceComponent(Equipment);
    auto* Survival = NewObject<UEWSurvivalComponent>(Owner); Owner->AddInstanceComponent(Survival);
    auto* Hat = NewObject<UEWItemDefinition>(); Hat->EquipmentSlot = EEWEquipmentSlot::Head; Hat->UnitWeight = 2.f;
    auto* OtherHat = NewObject<UEWItemDefinition>(); OtherHat->EquipmentSlot = EEWEquipmentSlot::Head; OtherHat->UnitWeight = 3.f;
    auto* Wood = NewObject<UEWItemDefinition>(); Wood->MaxStackSize = 250; Wood->UnitWeight = .1f;
    const auto Result = [this](const TCHAR* Label, EEWEquipmentResult Actual, EEWEquipmentResult Expected) { TestTrue(Label, Actual == Expected); };
    auto Weight = [this, Inventory, Equipment, Survival](float Expected)
    {
        TestTrue(TEXT("Inventory plus equipment weight conserved"), FMath::IsNearlyEqual(Inventory->GetTotalWeight()+Equipment->GetTotalWeight(), Expected, .001f));
        TestTrue(TEXT("Survival includes worn weight"), FMath::IsNearlyEqual(Survival->GetCarriedWeight(), Expected, .001f));
    };
    Result(TEXT("Missing owner rejects mutation"), NewObject<UEWEquipmentComponent>()->EquipItem(Hat, EEWEquipmentSlot::Head), EEWEquipmentResult::NotAuthority);
    Result(TEXT("Null item rejected"), Equipment->EquipItem(nullptr, EEWEquipmentSlot::Head), EEWEquipmentResult::InvalidItem);
    Result(TEXT("Unowned item rejected"), Equipment->EquipItem(Hat, EEWEquipmentSlot::Head), EEWEquipmentResult::NotOwned);
    Inventory->AddItem(Hat,1); Inventory->AddItem(OtherHat,1); Inventory->AddItem(Wood,1); Weight(5.1f);
    Result(TEXT("Wrong slot rejected"), Equipment->EquipItem(Hat, EEWEquipmentSlot::Feet), EEWEquipmentResult::InvalidSlot);
    Result(TEXT("Invalid enum rejected"), Equipment->EquipItem(Hat, static_cast<EEWEquipmentSlot>(255)), EEWEquipmentResult::InvalidSlot);
    Result(TEXT("Resource cannot be worn"), Equipment->EquipItem(Wood, EEWEquipmentSlot::None), EEWEquipmentResult::InvalidSlot);
    Result(TEXT("Equip owned unit"), Equipment->EquipItem(Hat, EEWEquipmentSlot::Head), EEWEquipmentResult::Success);
    TestEqual(TEXT("Unit leaves inventory"), Inventory->GetItemCount(Hat),0); TestEqual(TEXT("Unit enters slot"), Equipment->GetEquippedItem(EEWEquipmentSlot::Head),Hat); Weight(5.1f);
    Result(TEXT("Repeated request cannot consume another unit"), Equipment->EquipItem(Hat, EEWEquipmentSlot::Head), EEWEquipmentResult::NotOwned);
    Result(TEXT("Swap returns previous item atomically"), Equipment->EquipItem(OtherHat, EEWEquipmentSlot::Head), EEWEquipmentResult::Success);
    TestEqual(TEXT("Old hat returned"), Inventory->GetItemCount(Hat),1); TestEqual(TEXT("New hat equipped"), Equipment->GetEquippedItem(EEWEquipmentSlot::Head),OtherHat); Weight(5.1f);
    Inventory->AddItem(Wood,5750); // One hat plus 24 Wood stacks would exceed 24 slots; only 23 Wood stacks fit.
    TestEqual(TEXT("Inventory full"), Inventory->GetUsedSlotCount(),24);
    const float BeforeFull = Survival->GetCarriedWeight();
    Result(TEXT("Full inventory rejects unequip"), Equipment->UnequipItem(EEWEquipmentSlot::Head), EEWEquipmentResult::InventoryFull);
    TestEqual(TEXT("Rejected removal retains slot"), Equipment->GetEquippedItem(EEWEquipmentSlot::Head),OtherHat); Weight(BeforeFull);
    Result(TEXT("Swap can use source's freed slot in full inventory"), Equipment->EquipItem(Hat, EEWEquipmentSlot::Head), EEWEquipmentResult::Success); Weight(BeforeFull);
    auto* StackedHat = NewObject<UEWItemDefinition>(); StackedHat->EquipmentSlot = EEWEquipmentSlot::Head; StackedHat->MaxStackSize = 2; StackedHat->UnitWeight = 1.f;
    Inventory->RemoveItem(OtherHat,1); Inventory->AddItem(StackedHat,2);
    const float BeforeRejectedSwap = Survival->GetCarriedWeight();
    Result(TEXT("No return capacity rejects swap without consuming source"), Equipment->EquipItem(StackedHat, EEWEquipmentSlot::Head), EEWEquipmentResult::InventoryFull);
    TestEqual(TEXT("Both incoming units retained"),Inventory->GetItemCount(StackedHat),2);
    TestEqual(TEXT("Rejected swap retains original equipment"),Equipment->GetEquippedItem(EEWEquipmentSlot::Head),Hat); Weight(BeforeRejectedSwap);
    Inventory->RemoveItem(Wood,250);
    Result(TEXT("Capacity makes previous failed swap succeed"), Equipment->EquipItem(StackedHat, EEWEquipmentSlot::Head), EEWEquipmentResult::Success);
    TestEqual(TEXT("Only one stacked unit equipped"),Inventory->GetItemCount(StackedHat),1); Weight(BeforeRejectedSwap-25.f);
    Result(TEXT("Same equipped definition is a no-op"), Equipment->EquipItem(StackedHat, EEWEquipmentSlot::Head), EEWEquipmentResult::AlreadyEquipped);
    Result(TEXT("Unequip can fill existing partial stack"), Equipment->UnequipItem(EEWEquipmentSlot::Head), EEWEquipmentResult::Success);
    TestEqual(TEXT("Both stacked units returned"),Inventory->GetItemCount(StackedHat),2); Weight(BeforeRejectedSwap-25.f);
    Result(TEXT("Repeated unequip is safe"), Equipment->UnequipItem(EEWEquipmentSlot::Head), EEWEquipmentResult::EmptySlot);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWPersistedEquipmentTest, "Elitewake.Inventory.PersistedEquipmentFixtures",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWPersistedEquipmentTest::RunTest(const FString& Parameters)
{
    for (const TCHAR* Name : {TEXT("Test.Hat"), TEXT("Test.HatAlternate")})
    {
        const FPrimaryAssetId Id(TEXT("EWItem"), FName(Name));
        const FSoftObjectPath Path = UAssetManager::Get().GetPrimaryAssetPath(Id);
        TestTrue(TEXT("Saved equipment discovered by stable ID"), Path.IsValid());
        UEWItemDefinition* Item = Cast<UEWItemDefinition>(Path.TryLoad());
        if (!TestNotNull(TEXT("Saved equipment definition loads"), Item)) return false;
        TestEqual(TEXT("Stable ID retained"), Item->GetPrimaryAssetId(), Id);
        TestTrue(TEXT("Fixture uses head slot"), Item->EquipmentSlot == EEWEquipmentSlot::Head);
        TestEqual(TEXT("Fixture stack is one unit"), Item->MaxStackSize, 1);
    }
    return true;
}
#endif
