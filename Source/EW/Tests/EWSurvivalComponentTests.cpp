#include "EWSurvivalComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWSurvivalFiniteInputTest,"Elitewake.Survival.InvalidNumericInput",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWSurvivalFiniteInputTest::RunTest(const FString& Parameters)
{
    auto* Owner=NewObject<AActor>();
    auto* Survival=NewObject<UEWSurvivalComponent>(Owner);
    Owner->AddInstanceComponent(Survival);
    Survival->ApplyDamage(40.f);
    Survival->UpdateStamina(true,2.f);
    Survival->SetHunger(42.f);
    Survival->SetHydration(31.f);
    Survival->SetBodyTemperature(36.f);
    Survival->SetCarriedWeight(12.f);
    const float InvalidValues[]={std::numeric_limits<float>::quiet_NaN(),
        std::numeric_limits<float>::infinity(),-std::numeric_limits<float>::infinity()};
    for (float Value : InvalidValues)
    {
        Survival->ApplyDamage(Value);
        Survival->RestoreHealth(Value);
        Survival->UpdateStamina(true,Value);
        Survival->UpdateStamina(false,Value);
        Survival->SetHunger(Value);
        Survival->SetHydration(Value);
        Survival->SetBodyTemperature(Value);
        Survival->SetCarriedWeight(Value);
        TestEqual(TEXT("Invalid damage/healing preserves health"),Survival->GetHealth(),60.f);
        TestEqual(TEXT("Invalid elapsed time preserves stamina"),Survival->GetStamina(),70.f);
        TestEqual(TEXT("Invalid needs preserve hunger"),Survival->GetHunger(),42.f);
        TestEqual(TEXT("Invalid needs preserve hydration"),Survival->GetHydration(),31.f);
        TestEqual(TEXT("Invalid temperature preserves temperature"),Survival->GetBodyTemperature(),36.f);
        TestEqual(TEXT("Invalid weight preserves weight"),Survival->GetCarriedWeight(),12.f);
        TestEqual(TEXT("Invalid elapsed time cannot emit exhaustion"),Survival->GetStaminaExhaustionCount(),0);
    }
    Owner->SetRole(ROLE_SimulatedProxy);
    Survival->ApplyDamage(10.f);
    Survival->RestoreHealth(10.f);
    Survival->UpdateStamina(true,1.f);
    Survival->SetHunger(5.f);
    Survival->SetHydration(5.f);
    Survival->SetBodyTemperature(5.f);
    Survival->SetCarriedWeight(5.f);
    TestEqual(TEXT("Client health calls remain unauthorized"),Survival->GetHealth(),60.f);
    TestEqual(TEXT("Client stamina call remains unauthorized"),Survival->GetStamina(),70.f);
    TestEqual(TEXT("Client hunger call remains unauthorized"),Survival->GetHunger(),42.f);
    TestEqual(TEXT("Client hydration call remains unauthorized"),Survival->GetHydration(),31.f);
    TestEqual(TEXT("Client temperature call remains unauthorized"),Survival->GetBodyTemperature(),36.f);
    TestEqual(TEXT("Client weight call remains unauthorized"),Survival->GetCarriedWeight(),12.f);
    Owner->SetRole(ROLE_Authority);
    Survival->RestoreHealth(10.f);
    TestEqual(TEXT("Finite healing still applies"),Survival->GetHealth(),70.f);
    Survival->ApplyDamage(1000.f);
    TestEqual(TEXT("Finite damage still clamps to zero"),Survival->GetHealth(),0.f);
    Survival->SetHunger(120.f);
    Survival->SetHydration(-10.f);
    Survival->SetCarriedWeight(-10.f);
    TestEqual(TEXT("Finite hunger still clamps to full"),Survival->GetHunger(),100.f);
    TestEqual(TEXT("Finite hydration still clamps to empty"),Survival->GetHydration(),0.f);
    TestEqual(TEXT("Finite negative weight still clamps to zero"),Survival->GetCarriedWeight(),0.f);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Finite elapsed time still emits exhaustion"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(false,1.f);
    TestEqual(TEXT("Finite recovery still applies"),Survival->GetStamina(),10.f);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWSurvivalExhaustionTest,"Elitewake.Survival.ExhaustionNotification",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWSurvivalExhaustionTest::RunTest(const FString& Parameters)
{
    auto* Unowned=NewObject<UEWSurvivalComponent>();
    Unowned->UpdateStamina(true,10.f);
    TestEqual(TEXT("No owner cannot drain stamina"),Unowned->GetStamina(),100.f);
    TestEqual(TEXT("No owner cannot emit exhaustion"),Unowned->GetStaminaExhaustionCount(),0);
    auto* Owner=NewObject<AActor>();
    auto* Survival=NewObject<UEWSurvivalComponent>(Owner);
    Owner->AddInstanceComponent(Survival);
    Survival->UpdateStamina(true,1.f);
    TestEqual(TEXT("Partial drain does not emit exhaustion"),Survival->GetStaminaExhaustionCount(),0);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Empty transition emits one retained event"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Persistent empty does not replay event"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(false,.5f);
    TestTrue(TEXT("Recovery restores positive stamina"),Survival->GetStamina()>0.f);
    TestEqual(TEXT("Event survives recovery before replication"),Survival->GetStaminaExhaustionCount(),1);
    Survival->UpdateStamina(true,10.f);
    TestEqual(TEXT("Next exhaustion emits a new event"),Survival->GetStaminaExhaustionCount(),2);
    Survival->SetDebuffNotice(TEXT("Injury"),FText::FromString(TEXT("Injured")),-1.f);
    TestEqual(TEXT("Condition notice added"),Survival->GetDebuffNotices().Num(),1);
    Survival->SetDebuffNotice(TEXT("Injury"),FText::FromString(TEXT("Bandaged")),-1.f);
    TestEqual(TEXT("Same effect updates rather than duplicates"),Survival->GetDebuffNotices().Num(),1);
    Owner->SetRole(ROLE_SimulatedProxy);
    Survival->ClearDebuffNotice(TEXT("Injury"));
    Survival->SetDebuffNotice(TEXT("Poison"),FText::FromString(TEXT("Poisoned")),-1.f);
    TestEqual(TEXT("Client cannot add or clear effects"),Survival->GetDebuffNotices().Num(),1);
    Owner->SetRole(ROLE_Authority);
    Survival->SetDebuffNotice(TEXT("Injury"),FText::GetEmpty(),0.f);
    TestEqual(TEXT("Authority can clear a condition"),Survival->GetDebuffNotices().Num(),0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWSurvivalMendingTest,"Elitewake.Survival.MendingWhenFedAndWatered",EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWSurvivalMendingTest::RunTest(const FString& Parameters)
{
    auto* Owner=NewObject<AActor>();
    auto* Survival=NewObject<UEWSurvivalComponent>(Owner);
    Owner->AddInstanceComponent(Survival);
    const float PerSecond=Survival->GetMaxHealth()/UEWSurvivalComponent::MendSeconds;
    Survival->ApplyDamage(30.f);
    Survival->UpdateRecovery(false,UEWSurvivalComponent::HurtPause*.5f);
    TestEqual(TEXT("No mending straight after a hurt"),Survival->GetHealth(),70.f);
    Survival->UpdateRecovery(false,UEWSurvivalComponent::HurtPause*.5f);
    Survival->UpdateRecovery(false,60.f);
    TestEqual(TEXT("Fed and watered, a minute mends a minute's worth"),Survival->GetHealth(),70.f+60.f*PerSecond,.01f);
    const float Before=Survival->GetHealth();
    Survival->UpdateRecovery(true,60.f);
    TestEqual(TEXT("By a lit fire it mends faster"),Survival->GetHealth(),Before+60.f*PerSecond*UEWSurvivalComponent::FireMendFactor,.01f);
    Survival->ApplyDamage(5.f);
    const float Hurt=Survival->GetHealth();
    Survival->UpdateRecovery(true,UEWSurvivalComponent::HurtPause-1.f);
    TestEqual(TEXT("A new hurt pauses mending again"),Survival->GetHealth(),Hurt);
    Survival->UpdateRecovery(false,5.f);
    Survival->SetHunger(UEWSurvivalComponent::WellFedAbove-1.f);
    const float Hungry=Survival->GetHealth();
    Survival->UpdateRecovery(false,60.f);
    TestEqual(TEXT("Hungry, the body does not mend"),Survival->GetHealth(),Hungry);
    Survival->SetHunger(100.f);
    Survival->ContractFoodSickness();
    Survival->UpdateRecovery(false,60.f);
    TestEqual(TEXT("Nor while food-sick"),Survival->GetHealth(),Hungry);
    Survival->CureFoodSickness();
    Survival->UpdateRecovery(true,UEWSurvivalComponent::MendSeconds);
    TestEqual(TEXT("Mending stops at full health"),Survival->GetHealth(),Survival->GetMaxHealth());
    Owner->SetRole(ROLE_SimulatedProxy);
    Survival->ApplyDamage(10.f);
    TestEqual(TEXT("Clients cannot change health"),Survival->GetHealth(),Survival->GetMaxHealth());
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWSurvivalHazardsTest, "Elitewake.Survival.HazardsAndTreatments",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWSurvivalHazardsTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    AActor* Owner = World->SpawnActor<AActor>();
    auto* Survival = NewObject<UEWSurvivalComponent>(Owner);
    auto* Inventory = NewObject<UEWInventoryComponent>(Owner);
    Owner->AddInstanceComponent(Survival);
    Owner->AddInstanceComponent(Inventory);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();
    TGuardValue<uint64> FrameGuard(GFrameCounter, GFrameCounter);
    auto Wait = [World](int32 Ticks)
    {
        for (int32 I = 0; I < Ticks; ++I) { ++GFrameCounter; World->Tick(LEVELTICK_All, .05f); }
    };
    auto Treatment = [](EEWSurvivalTreatment Kind, FName Id)
    {
        auto* Item = NewObject<UEWItemDefinition>();
        Item->ItemId = Id;
        Item->Category = EEWItemCategory::Consumable;
        Item->FoodKind = EEWFoodKind::Remedy;
        Item->bFoodConsumptionEnabled = true;
        Item->SurvivalTreatment = Kind;
        return Item;
    };
    auto* Bandage = Treatment(EEWSurvivalTreatment::Bandage, TEXT("Test.Bandage"));
    auto* Antidote = Treatment(EEWSurvivalTreatment::Antidote, TEXT("Test.Antidote"));
    Inventory->AddItem(Bandage, 1);
    Inventory->AddItem(Antidote, 1);
    Survival->InflictBleeding();
    Survival->UpdateHazards(false, 10.f);
    TestEqual(TEXT("Bleeding takes four health in ten seconds"), Survival->GetHealth(), 96.f);
    Survival->InflictBleeding();
    TestEqual(TEXT("A new wound refreshes a single timer"), Survival->GetBleedingLeft(), 30.f);
    TestEqual(TEXT("A bandage starts before spending the item"), Inventory->ConsumeFood(Bandage), EEWFoodUseResult::TreatmentStarted);
    Wait(10);
    Inventory->InterruptBandage();
    Wait(42);
    TestTrue(TEXT("An interrupted application leaves the wound and bandage"), Survival->IsBleeding() && Inventory->HasItem(Bandage));
    TestEqual(TEXT("A bandage can be retried"), Inventory->ConsumeFood(Bandage), EEWFoodUseResult::TreatmentStarted);
    Wait(44);
    TestFalse(TEXT("A completed application stops the bleeding"), Survival->IsBleeding());
    TestFalse(TEXT("A completed application spends one bandage"), Inventory->HasItem(Bandage));
    TestEqual(TEXT("Bandaging doesn't restore lost health"), Survival->GetHealth(), 96.f);

    Survival->InflictPoison();
    Survival->UpdateStamina(true, 2.f);
    Survival->UpdateStamina(false, 2.f);
    TestEqual(TEXT("Venom halves stamina recovery"), Survival->GetStamina(), 80.f);
    Survival->UpdateHazards(false, 45.f);
    TestEqual(TEXT("Venom takes eight health and expires"), Survival->GetHealth(), 88.f);
    TestEqual(TEXT("An antidote is preserved when not needed"), Inventory->ConsumeFood(Antidote), EEWFoodUseResult::TreatmentUnneeded);
    Survival->InflictPoison();
    TestEqual(TEXT("An antidote cures active poison"), Inventory->ConsumeFood(Antidote), EEWFoodUseResult::TreatmentApplied);
    TestFalse(TEXT("Poison and spent antidote are gone"), Survival->IsPoisoned() || Inventory->HasItem(Antidote));

    Survival->UpdateHazards(true, 22.f);
    TestEqual(TEXT("Low air begins with eight seconds left"), Survival->GetBreathSeconds(), 8.f);
    Survival->UpdateHazards(true, 9.f);
    TestEqual(TEXT("Only the second after air runs out drowns"), Survival->GetHealth(), 84.f);
    Survival->UpdateHazards(false, 3.f);
    TestFalse(TEXT("Surfacing clears the underwater state"), Survival->IsUnderwater());
    TestEqual(TEXT("Three seconds at the surface refills breath"), Survival->GetBreathSeconds(), 30.f);
    TestEqual(TEXT("Surfacing immediately stops drowning damage"), Survival->GetHealth(), 84.f);
    GEngine->DestroyWorldContext(World);
    World->DestroyWorld(false);
    return true;
}
#endif
