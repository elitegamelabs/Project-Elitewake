#if WITH_DEV_AUTOMATION_TESTS
#include "EWHotbarComponent.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWHotbarTest, "Elitewake.Inventory.HotbarOwnershipAndActivation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWHotbarTest::RunTest(const FString& Parameters)
{
    AActor* Owner=NewObject<AActor>();
    auto* Inventory=NewObject<UEWInventoryComponent>(Owner); Owner->AddInstanceComponent(Inventory);
    auto* Equipment=NewObject<UEWEquipmentComponent>(Owner); Owner->AddInstanceComponent(Equipment);
    auto* Survival=NewObject<UEWSurvivalComponent>(Owner); Owner->AddInstanceComponent(Survival);
    auto* Hotbar=NewObject<UEWHotbarComponent>(Owner); Owner->AddInstanceComponent(Hotbar);
    auto* Hat=NewObject<UEWItemDefinition>(); Hat->EquipmentSlot=EEWEquipmentSlot::Head; Hat->UnitWeight=2;
    auto* Alternate=NewObject<UEWItemDefinition>(); Alternate->EquipmentSlot=EEWEquipmentSlot::Head; Alternate->UnitWeight=3;
    auto* Wood=NewObject<UEWItemDefinition>(); Wood->MaxStackSize=250; Wood->UnitWeight=.1f;
    auto Result=[this](const TCHAR* Label,EEWHotbarResult Actual,EEWHotbarResult Expected){TestTrue(Label,Actual==Expected);};
    auto Weight=[this,Inventory,Equipment,Survival](float Expected)
    {
        TestTrue(TEXT("Shortcut/equipment action preserves composite weight"),FMath::IsNearlyEqual(Inventory->GetTotalWeight()+Equipment->GetTotalWeight(),Expected,.01f));
        TestTrue(TEXT("Survival reflects actual carried units"),FMath::IsNearlyEqual(Survival->GetCarriedWeight(),Expected,.01f));
    };
    Result(TEXT("Missing authority rejected"),NewObject<UEWHotbarComponent>()->BindItem(0,Hat),EEWHotbarResult::NotAuthority);
    Result(TEXT("Negative slot rejected"),Hotbar->BindItem(-1,Hat),EEWHotbarResult::InvalidSlot);
    Result(TEXT("Ninth slot rejected"),Hotbar->ActivateSlot(8),EEWHotbarResult::InvalidSlot);
    TestEqual(TEXT("Invalid request does not select"),Hotbar->GetSelectedSlot(),INDEX_NONE);
    Result(TEXT("Unowned binding rejected"),Hotbar->BindItem(0,Hat),EEWHotbarResult::NotOwned);
    Inventory->AddItem(Hat,1); Inventory->AddItem(Alternate,1); Inventory->AddItem(Wood,250); Weight(30.f);
    Result(TEXT("Owned binding accepted"),Hotbar->BindItem(0,Hat),EEWHotbarResult::Success);
    Result(TEXT("Final slot supports resource binding"),Hotbar->BindItem(7,Wood),EEWHotbarResult::Success);
    TestEqual(TEXT("Binding never moves inventory"),Inventory->GetItemCount(Hat),1); Weight(30.f);
    Result(TEXT("Reassignment accepted"),Hotbar->BindItem(4,Hat),EEWHotbarResult::Success);
    TestNull(TEXT("Reassignment clears previous shortcut"),Hotbar->GetBoundItem(0));
    TestEqual(TEXT("Reassignment preserves new shortcut"),Hotbar->GetBoundItem(4),Hat);
    Result(TEXT("Activation equips owned unit"),Hotbar->ActivateSlot(4),EEWHotbarResult::Success);
    TestEqual(TEXT("Unit now worn"),Equipment->GetEquippedItem(EEWEquipmentSlot::Head),Hat);
    TestEqual(TEXT("Worn unit still available to shortcut"),Hotbar->GetOwnedQuantity(Hat),1);
    Result(TEXT("Already worn activation is safe"),Hotbar->ActivateSlot(4),EEWHotbarResult::Success); Weight(30.f);
    Result(TEXT("Worn item can be rebound"),Hotbar->BindItem(1,Hat),EEWHotbarResult::Success);
    Hotbar->BindItem(2,Alternate);
    Result(TEXT("Activation swaps via equipment rules"),Hotbar->ActivateSlot(2),EEWHotbarResult::Success);
    TestEqual(TEXT("Previous unit returned exactly once"),Inventory->GetItemCount(Hat),1); Weight(30.f);
    Result(TEXT("Empty slot does not use item"),Hotbar->ActivateSlot(0),EEWHotbarResult::EmptySlot);
    Result(TEXT("Resource action rejects without consuming"),Hotbar->ActivateSlot(7),EEWHotbarResult::UnsupportedAction);
    TestEqual(TEXT("All resource units retained"),Inventory->GetItemCount(Wood),250);
    Inventory->RemoveItem(Wood,250);
    Result(TEXT("Unavailable shortcut cannot act"),Hotbar->ActivateSlot(7),EEWHotbarResult::NotOwned);
    TestEqual(TEXT("Unavailable binding retained for replenishment"),Hotbar->GetBoundItem(7),Wood);
    Inventory->AddItem(Wood,1);
    TestEqual(TEXT("Replenishment restores availability"),Hotbar->GetOwnedQuantity(Wood),1); Weight(5.1f);
    auto* Stacked=NewObject<UEWItemDefinition>(); Stacked->EquipmentSlot=EEWEquipmentSlot::Head; Stacked->MaxStackSize=2;
    Inventory->AddItem(Stacked,2); Inventory->AddItem(Wood,6000);
    TestEqual(TEXT("Capacity fixture full"),Inventory->GetUsedSlotCount(),24);
    Hotbar->BindItem(6,Stacked);
    const float Before=Survival->GetCarriedWeight();
    Result(TEXT("Blocked swap obeys atomic return capacity"),Hotbar->ActivateSlot(6),EEWHotbarResult::InventoryFull);
    TestEqual(TEXT("Blocked activation retains source"),Inventory->GetItemCount(Stacked),2);
    TestEqual(TEXT("Blocked activation retains old gear"),Equipment->GetEquippedItem(EEWEquipmentSlot::Head),Alternate); Weight(Before);
    Result(TEXT("Clearing is safe"),Hotbar->BindItem(6,nullptr),EEWHotbarResult::Success);
    TestNull(TEXT("Binding cleared"),Hotbar->GetBoundItem(6)); Weight(Before);
    return true;
}
#endif
