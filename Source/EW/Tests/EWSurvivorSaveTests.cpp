#if WITH_DEV_AUTOMATION_TESTS

#include "EWCharacter.h"
#include "EWEquipmentComponent.h"
#include "EWHotbarComponent.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "EWSurvivorSave.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWSurvivorSaveRoundTripTest, "Elitewake.Save.SurvivorRoundTrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWSurvivorSaveRoundTripTest::RunTest(const FString& Parameters)
{
    const FString SlotName = FString::Printf(TEXT("EW_SaveRoundTrip_%s"), *FGuid::NewGuid().ToString(EGuidFormats::Digits));
    ON_SCOPE_EXIT { UGameplayStatics::DeleteGameInSlot(SlotName, 0); };

    const UWorld::InitializationValues Values = UWorld::InitializationValues().AllowAudioPlayback(false)
        .CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true,
        ERHIFeatureLevel::Num, &Values);
    if (!TestNotNull(TEXT("Save test world"), World)) return false;
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);
    ON_SCOPE_EXIT { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); };

    UClass* CharacterClass = LoadClass<AEWCharacter>(nullptr,
        TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    UEWItemDefinition* Berry = LoadObject<UEWItemDefinition>(nullptr,
        TEXT("/Game/Elitewake/Items/Testing/DA_TestAzulBerry.DA_TestAzulBerry"));
    UEWItemDefinition* Axe = LoadObject<UEWItemDefinition>(nullptr,
        TEXT("/Game/Elitewake/Items/Testing/DA_TestWoodenAxe.DA_TestWoodenAxe"));
    if (!TestNotNull(TEXT("Playable survivor Blueprint"), CharacterClass) ||
        !TestNotNull(TEXT("Berry definition"), Berry) || !TestNotNull(TEXT("Equippable axe definition"), Axe))
        return false;

    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AEWCharacter* Original = World->SpawnActor<AEWCharacter>(CharacterClass, FVector(120.f, -240.f, 500.f),
        FRotator(0.f, 73.f, 0.f), Spawn);
    if (!TestNotNull(TEXT("Original survivor"), Original)) return false;
    Original->GetSurvivalComponent()->ApplyDamage(23.f);
    Original->GetSurvivalComponent()->SetHunger(42.f);
    Original->GetSurvivalComponent()->SetHydration(31.f);
    Original->GetInventoryComponent()->AddItem(Berry, 4);
    Original->GetInventoryComponent()->AdvanceFoodAge(321.f);
    Original->GetInventoryComponent()->AddItem(Axe, 1);
    TestTrue(TEXT("Original equips its owned axe"),
        Original->GetEquipmentComponent()->EquipItem(Axe, EEWEquipmentSlot::MainHand) == EEWEquipmentResult::Success);
    TestTrue(TEXT("Axe shortcut binds"), Original->GetHotbarComponent()->BindItem(2, Axe) == EEWHotbarResult::Success);
    TestTrue(TEXT("Berry shortcut binds"), Original->GetHotbarComponent()->BindItem(5, Berry) == EEWHotbarResult::Success);

    TestTrue(TEXT("Save writes to isolated test slot"), UEWSurvivorSave::SaveSurvivor(Original, SlotName));
    TestTrue(TEXT("Test slot exists"), UEWSurvivorSave::HasSave(SlotName));
    Original->GetSurvivalComponent()->ApplyDamage(50.f);
    Original->GetSurvivalComponent()->SetHunger(1.f);
    Original->GetSurvivalComponent()->SetHydration(2.f);
    Original->GetInventoryComponent()->RemoveItem(Berry, 4);

    UEWSurvivorSave* Saved = UEWSurvivorSave::LoadSave(SlotName);
    if (!TestNotNull(TEXT("Saved survivor loads"), Saved)) return false;
    AEWCharacter* Resumed = World->SpawnActor<AEWCharacter>(CharacterClass, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    if (!TestNotNull(TEXT("Fresh survivor"), Resumed)) return false;
    // Simulate a starter supply already present when the resumed pawn is prepared.
    Resumed->GetInventoryComponent()->AddItem(Axe, 1);
    TestTrue(TEXT("Saved survivor applies on the same map"), Saved->ApplyTo(Resumed));

    TestTrue(TEXT("Saved location restored"), Resumed->GetActorLocation().Equals(FVector(120.f, -240.f, 500.f), .1f));
    TestTrue(TEXT("Saved facing restored"), FMath::IsNearlyEqual(Resumed->GetActorRotation().Yaw, 73.f, .1f));
    TestTrue(TEXT("Health restored"), FMath::IsNearlyEqual(Resumed->GetSurvivalComponent()->GetHealth(), 77.f, .01f));
    TestTrue(TEXT("Hunger restored"), FMath::IsNearlyEqual(Resumed->GetSurvivalComponent()->GetHunger(), 42.f, .01f));
    TestTrue(TEXT("Hydration restored"), FMath::IsNearlyEqual(Resumed->GetSurvivalComponent()->GetHydration(), 31.f, .01f));
    const TArray<FEWInventoryEntry> ResumedEntries = Resumed->GetInventoryComponent()->GetInventoryEntries();
    const FEWInventoryEntry* SavedBerry = ResumedEntries.FindByPredicate(
        [Berry](const FEWInventoryEntry& Entry) { return Entry.ItemDefinition == Berry; });
    TestNotNull(TEXT("Saved food stack restored"), SavedBerry);
    TestTrue(TEXT("Food age survives the save"), SavedBerry && FMath::IsNearlyEqual(SavedBerry->FoodAgeSeconds, 321.f, 1.f));
    TestEqual(TEXT("Equipped tool restored"), Resumed->GetEquipmentComponent()->GetEquippedItem(EEWEquipmentSlot::MainHand), Axe);
    TestEqual(TEXT("Tool is not duplicated in inventory"), Resumed->GetInventoryComponent()->GetItemCount(Axe), 0);
    TestEqual(TEXT("Starter and saved tool resolve to one owned unit"), Resumed->GetHotbarComponent()->GetOwnedQuantity(Axe), 1);
    TestEqual(TEXT("First hotbar binding restored"), Resumed->GetHotbarComponent()->GetBoundItem(2), Axe);
    TestEqual(TEXT("Second hotbar binding restored"), Resumed->GetHotbarComponent()->GetBoundItem(5), Berry);
    TestTrue(TEXT("Temporary save slot is removed"), UGameplayStatics::DeleteGameInSlot(SlotName, 0));
    TestFalse(TEXT("Temporary save slot no longer exists"), UEWSurvivorSave::HasSave(SlotName));
    return true;
}

#endif
