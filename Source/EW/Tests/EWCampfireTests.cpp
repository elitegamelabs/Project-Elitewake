#if WITH_DEV_AUTOMATION_TESTS
#include "World/EWCampfire.h"
#include "EWCharacter.h"
#include "EWCraftingRecipe.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWCampfireCookingTest, "Elitewake.Survival.CookingNeedsALitFire",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWCampfireCookingTest::RunTest(const FString& Parameters)
{
    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    UClass* PawnClass = LoadClass<AEWCharacter>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    if (!TestNotNull(TEXT("Player class"), PawnClass)) { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return false; }
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Cook = World->SpawnActor<AEWCharacter>(PawnClass, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);

    auto* Berry = NewObject<UEWItemDefinition>(); Berry->ItemId = TEXT("Test.Berry"); Berry->MaxStackSize = 50;
    auto* Dish = NewObject<UEWItemDefinition>(); Dish->ItemId = TEXT("Test.Dish"); Dish->MaxStackSize = 50;
    auto* Recipe = NewObject<UEWCraftingRecipe>(); Recipe->Output = Dish; Recipe->bNeedsFire = true;
    FEWCraftingIngredient Cost; Cost.Item = Berry; Cost.Quantity = 3; Recipe->Ingredients.Add(Cost);
    auto* Pack = Cook->GetInventoryComponent();
    Pack->UnlockRecipe(Recipe);
    Pack->AddItem(Berry, 3);

    TestEqual(TEXT("No fire anywhere: the dish cannot be cooked"), Pack->GetCraftReadiness(Recipe), EEWCraftResult::NeedsFire);
    TestEqual(TEXT("Nor made by the server"), Pack->CraftItem(Recipe), EEWCraftResult::NeedsFire);
    TestEqual(TEXT("Nothing is used up by a refused craft"), Pack->GetItemCount(Berry), 3);
    auto* Fire = World->SpawnActor<AEWCampfire>(AEWCampfire::StaticClass(), FVector(150, 0, 0), FRotator::ZeroRotator, Spawn);
    TestFalse(TEXT("A newly spawned ring is cold until it is given fuel"), Fire->IsLit());
    TestEqual(TEXT("A cold ring beside the cook is not enough"), Pack->GetCraftReadiness(Recipe), EEWCraftResult::NeedsFire);
    Fire->SetFuel(AEWCampfire::StartingFuel);
    TestTrue(TEXT("Fuel lights it"), Fire->IsLit());
    TestEqual(TEXT("A lit fire within reach lets the dish be cooked"), Pack->GetCraftReadiness(Recipe), EEWCraftResult::Success);
    Fire->SetActorLocation(FVector(AEWCampfire::CookReach + 50.f, 0, 0));
    TestEqual(TEXT("A lit fire out of reach does not"), Pack->GetCraftReadiness(Recipe), EEWCraftResult::NeedsFire);
    Fire->SetActorLocation(FVector(150, 0, 0));
    TestEqual(TEXT("Back in reach, the server cooks it"), Pack->CraftItem(Recipe), EEWCraftResult::Success);
    TestEqual(TEXT("Three berries make one dish"), Pack->GetItemCount(Dish), 1);
    Fire->SetFuel(AEWCampfire::MaxFuel * 10.f);
    TestEqual(TEXT("Fuel is capped"), Fire->GetFuelLeft(), AEWCampfire::MaxFuel);
    TestEqual(TEXT("The save keeps the burn time left"), Fire->CaptureForSave().FuelLeft, AEWCampfire::MaxFuel);
    Fire->SetFuel(0.f);
    TestFalse(TEXT("Burnt down, it is cold"), Fire->IsLit());
    TestFalse(TEXT("And no fire is lit near"), AEWCampfire::IsLitFireNear(Cook));
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false);
    return true;
}
#endif
