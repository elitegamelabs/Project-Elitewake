#if WITH_DEV_AUTOMATION_TESTS
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWFoodTest, "Elitewake.Inventory.FoodConsumptionAndFreshness",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWFoodTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("No owner cannot consume"), NewObject<UEWInventoryComponent>()->ConsumeFood(nullptr), EEWFoodUseResult::NotAuthority);
    AActor* Owner = NewObject<AActor>();
    auto* Inventory = NewObject<UEWInventoryComponent>(Owner);
    auto* Survival = NewObject<UEWSurvivalComponent>(Owner);
    Owner->AddInstanceComponent(Inventory); Owner->AddInstanceComponent(Survival);
    auto* Berry = NewObject<UEWItemDefinition>();
    Berry->ItemId = TEXT("Test.Azul"); Berry->Category = EEWItemCategory::Consumable;
    Berry->FoodKind = EEWFoodKind::Berry; Berry->MaxStackSize = 500; Berry->UnitWeight = .01f;
    Berry->HungerRestoreFraction = 1.f / 16.f; Berry->HealthRestoreFraction = .05f;
    Berry->FreshLifetimeSeconds = 1200.f;
    auto* Toxic = NewObject<UEWItemDefinition>(); Toxic->ItemId = TEXT("Test.ToxicBerry");
    Toxic->Category = EEWItemCategory::Resource; Toxic->MaxStackSize = 500; Toxic->UnitWeight = .01f;
    Berry->SpoiledItemDefinition = Toxic;
    Inventory->AddItem(Berry, 3);
    Owner->SetRole(ROLE_AutonomousProxy);
    TestEqual(TEXT("Client cannot consume locally"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::NotAuthority);
    Inventory->AdvanceFoodAge(1200.f);
    TestEqual(TEXT("Client cannot expire authoritative units"), Inventory->GetItemCount(Berry), 3);
    Owner->SetRole(ROLE_Authority);
    Survival->SetHunger(50.f); Survival->ApplyDamage(50.f);
    TestEqual(TEXT("Unauthored consumption stays disabled"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::InvalidFood);
    Berry->bFoodConsumptionEnabled = true;
    TestEqual(TEXT("One owned berry consumed"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::Success);
    TestEqual(TEXT("One sixteenth of hunger bar restored"), Survival->GetHunger(), 56.25f);
    TestEqual(TEXT("Five percent of maximum health restored"), Survival->GetHealth(), 55.f);
    TestEqual(TEXT("Exactly one unit removed"), Inventory->GetItemCount(Berry), 2);
    TestTrue(TEXT("Carried weight follows consumption"), FMath::IsNearlyEqual(Survival->GetCarriedWeight(), .02f));
    auto* MaxHealth = FindFProperty<FFloatProperty>(UEWSurvivalComponent::StaticClass(), TEXT("MaxHealth"));
    if (!TestNotNull(TEXT("Max health property"), MaxHealth)) return false;
    MaxHealth->SetPropertyValue_InContainer(Survival, 200.f);
    TestEqual(TEXT("Upgraded maximum used"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::Success);
    TestEqual(TEXT("Healing scales to upgraded max, not remaining health"), Survival->GetHealth(), 65.f);
    Survival->RestoreHealth(200.f); Survival->SetHunger(100.f);
    TestEqual(TEXT("No-benefit request preserves food"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::NoBenefit);
    TestEqual(TEXT("No-benefit quantity unchanged"), Inventory->GetItemCount(Berry), 1);
    Survival->ApplyDamage(200.f);
    TestEqual(TEXT("Food cannot revive dead survivor"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::UnavailableSurvivor);
    Survival->RestoreHealth(100.f); Survival->SetHunger(95.f);
    Inventory->bEquipmentTransferInProgress = true;
    TestEqual(TEXT("Transfer guard rejects nested use"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::Busy);
    TestEqual(TEXT("Transfer guard rejects nested removal"), Inventory->RemoveItem(Berry, 1), 0);
    Inventory->bEquipmentTransferInProgress = false;
    Inventory->AdvanceFoodAge(1199.f);
    TestEqual(TEXT("Fresh until twenty real minutes"), Inventory->GetItemCount(Berry), 1);
    Inventory->AddItem(Berry, 2);
    TestEqual(TEXT("Later pickups get separate freshness batches"), Inventory->GetUsedSlotCount(), 2);
    TestTrue(TEXT("New units do not refresh old stack"), Inventory->Entries[0].FoodAgeSeconds >= 1199.f);
    Inventory->AdvanceFoodAge(1.f);
    TestEqual(TEXT("Later berries retain their own twenty minutes"), Inventory->GetItemCount(Berry), 2);
    TestEqual(TEXT("Only expired batch becomes toxic resource"), Inventory->GetItemCount(Toxic), 1);
    TestTrue(TEXT("Expiration preserves carried weight"), FMath::IsNearlyEqual(Survival->GetCarriedWeight(), .03f));
    TestEqual(TEXT("Toxic resource cannot be eaten"), Inventory->ConsumeFood(Toxic), EEWFoodUseResult::InvalidFood);
    Inventory->AdvanceFoodAge(1199.f);
    TestEqual(TEXT("Later batch expires at its own boundary"), Inventory->GetItemCount(Toxic), 3);
    TestEqual(TEXT("Absent berry cannot restore stats"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::NotOwned);
    Inventory->AddItem(Berry, 501);
    TestEqual(TEXT("Food splits at five hundred"), Inventory->GetUsedSlotCount(), 4);
    Inventory->AdvanceFoodAge(1200.f);
    TestEqual(TEXT("Multi-stack expiration conserves quantities"), Inventory->GetItemCount(Toxic), 504);
    Inventory->RemoveItem(Toxic, 504);
    Inventory->AddItem(Berry, 1); Toxic->MaxStackSize = 250;
    Inventory->AdvanceFoodAge(1200.f);
    TestEqual(TEXT("Bad conversion authoring preserves expired unit"), Inventory->GetItemCount(Berry), 1);
    TestEqual(TEXT("Bad conversion cannot make expired food edible"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::InvalidFood);
    Inventory->RemoveItem(Berry, 1);
    Toxic->MaxStackSize = 500;
    Inventory->AddItem(Berry, 1);
    Inventory->LastFoodClockSeconds = FPlatformTime::Seconds() - 1200.;
    Inventory->RefreshFoodAge();
    TestEqual(TEXT("Real monotonic clock drives expiration without game-time advancement"), Inventory->GetItemCount(Toxic), 1);
    Inventory->AddItem(Berry, 1); Survival->SetHunger(99.f); Survival->RestoreHealth(200.f); Survival->ApplyDamage(1.f);
    TestEqual(TEXT("Near-full survivor can use food"), Inventory->ConsumeFood(Berry), EEWFoodUseResult::Success);
    TestEqual(TEXT("Hunger clamps to full bar"), Survival->GetHunger(), 100.f);
    TestEqual(TEXT("Health clamps to upgraded maximum"), Survival->GetHealth(), 200.f);
    return true;
}
#endif
