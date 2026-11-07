#if WITH_DEV_AUTOMATION_TESTS
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWHotbarComponent.h"
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
    auto* Hotbar = NewObject<UEWHotbarComponent>(Owner); Owner->AddInstanceComponent(Hotbar);
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
    Inventory->RemoveItem(Toxic, 10000);
    Inventory->AddItem(Berry, 2);
    TestEqual(TEXT("Food can be assigned without extra storage"), Hotbar->BindItem(0, Berry), EEWHotbarResult::Success);
    TestEqual(TEXT("Full survivor hotbar action preserves berries"), Hotbar->ActivateSlot(0), EEWHotbarResult::NoBenefit);
    Survival->SetHunger(50.f);
    TestEqual(TEXT("Hotbar eats exactly one owned berry"), Hotbar->ActivateSlot(0), EEWHotbarResult::Success);
    TestEqual(TEXT("Hotbar quantity decreases once"), Inventory->GetItemCount(Berry), 1);
    TestEqual(TEXT("Hotbar restores hunger"), Survival->GetHunger(), 56.25f);
    Inventory->AdvanceFoodAge(600.f);
    TestTrue(TEXT("Freshness presentation reflects oldest batch"), FMath::IsNearlyEqual(Inventory->GetFoodFreshness(Berry), .5f, .01f));
    Inventory->AdvanceFoodAge(600.f);
    TestEqual(TEXT("Expired shortcut cannot consume toxic replacement"), Hotbar->ActivateSlot(0), EEWHotbarResult::NotOwned);
    TestEqual(TEXT("Expired shortcut remains bound to original definition"), Hotbar->GetBoundItem(0), Berry);
    TestEqual(TEXT("No freshness bar for expired original definition"), Inventory->GetFoodFreshness(Berry), -1.f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWNeedsTest, "Elitewake.Survival.HungerThirstAndFoodSickness",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWNeedsTest::RunTest(const FString& Parameters)
{
    AActor* Owner = NewObject<AActor>();
    auto* Inventory = NewObject<UEWInventoryComponent>(Owner);
    auto* Survival = NewObject<UEWSurvivalComponent>(Owner);
    Owner->AddInstanceComponent(Inventory); Owner->AddInstanceComponent(Survival);
    Owner->SetRole(ROLE_Authority);
    Survival->UpdateNeeds(false, 60.f);
    TestTrue(TEXT("Hunger empties in 45 minutes"), FMath::IsNearlyEqual(100.f - Survival->GetHunger(), 100.f / 2700.f * 60.f, .01f));
    TestTrue(TEXT("Thirst empties in 25 minutes"), FMath::IsNearlyEqual(100.f - Survival->GetHydration(), 100.f / 1500.f * 60.f, .01f));
    Survival->SetHunger(0.f);
    const float Before = Survival->GetHealth();
    Survival->UpdateNeeds(false, 10.f);
    TestTrue(TEXT("Zero hunger costs health gradually"), Survival->GetHealth() < Before && Survival->GetHealth() > Before - 5.f);
    Survival->SetHunger(100.f); Survival->SetHydration(100.f);
    Survival->ContractFoodSickness();
    TestTrue(TEXT("Sickness lasts three minutes"), FMath::IsNearlyEqual(Survival->GetFoodSicknessLeft(), 180.f));
    Survival->UpdateNeeds(false, 60.f);
    TestTrue(TEXT("Sickness quickens thirst by half"), FMath::IsNearlyEqual(100.f - Survival->GetHydration(), 100.f / 1500.f * 60.f * 1.5f, .01f));
    Survival->UpdateNeeds(false, 130.f);
    TestFalse(TEXT("Sickness ends by itself"), Survival->IsFoodSick());
    auto* Meat = NewObject<UEWItemDefinition>();
    Meat->ItemId = TEXT("Test.RawMeat"); Meat->Category = EEWItemCategory::Consumable; Meat->FoodKind = EEWFoodKind::RawMeat;
    Meat->MaxStackSize = 50; Meat->UnitWeight = .4f; Meat->bFoodConsumptionEnabled = true;
    Meat->HungerRestoreFraction = .12f; Meat->HealthRestoreFraction = -.03f; Meat->SicknessChance = 1.f;
    Survival->SetHunger(20.f);
    const float HealthBeforeMeat = Survival->GetHealth();
    Inventory->AddItem(Meat, 1);
    TestEqual(TEXT("Raw meat is eaten"), Inventory->ConsumeFood(Meat), EEWFoodUseResult::Success);
    TestTrue(TEXT("Raw meat restores 12 hunger"), FMath::IsNearlyEqual(Survival->GetHunger(), 32.f, .01f));
    TestTrue(TEXT("Raw meat costs 3 health"), FMath::IsNearlyEqual(Survival->GetHealth(), HealthBeforeMeat - 3.f, .01f));
    TestTrue(TEXT("A certain sickness chance sickens"), Survival->IsFoodSick());
    auto* Herb = NewObject<UEWItemDefinition>();
    Herb->ItemId = TEXT("Test.Herb"); Herb->Category = EEWItemCategory::Consumable; Herb->FoodKind = EEWFoodKind::Remedy;
    Herb->MaxStackSize = 50; Herb->UnitWeight = .05f; Herb->bFoodConsumptionEnabled = true; Herb->bCuresFoodSickness = true;
    Inventory->AddItem(Herb, 1);
    TestEqual(TEXT("A herb is eaten while sick"), Inventory->ConsumeFood(Herb), EEWFoodUseResult::Success);
    TestFalse(TEXT("The herb cures the sickness"), Survival->IsFoodSick());
    Inventory->AddItem(Herb, 1);
    TestEqual(TEXT("A herb does nothing when well"), Inventory->ConsumeFood(Herb), EEWFoodUseResult::NoBenefit);
    return true;
}

#endif
