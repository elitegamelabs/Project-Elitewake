#if WITH_DEV_AUTOMATION_TESTS
#include "EWCraftingRecipe.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWCraftingTest, "Elitewake.Crafting.AtomicTransaction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWCraftingTest::RunTest(const FString& Parameters)
{
    AActor* Owner = NewObject<AActor>();
    auto* Inventory = NewObject<UEWInventoryComponent>(Owner);
    auto* Wood = NewObject<UEWItemDefinition>();
    Wood->ItemId = TEXT("Test.CraftWood"); Wood->MaxStackSize = 250;
    auto* Axe = NewObject<UEWItemDefinition>(); Axe->ItemId = TEXT("Test.CraftAxe");
    auto* Recipe = NewObject<UEWCraftingRecipe>(); Recipe->Output = Axe;
    FEWCraftingIngredient Cost; Cost.Item = Wood; Cost.Quantity = 20;
    Recipe->Ingredients.Add(Cost);
    TestEqual(TEXT("Default baseline list is empty"), Inventory->StartingRecipes.Num(), 0);
    TestEqual(TEXT("Unapproved recipe rejected"), Inventory->CraftItem(Recipe), EEWCraftResult::Locked);
    Inventory->StartingRecipes = {Recipe, Recipe, nullptr};
    Inventory->InitializeStartingRecipes();
    TestEqual(TEXT("Authored baseline ignores nulls and duplicate references"), Inventory->GetAvailableRecipes().Num(), 1);
    TestEqual(TEXT("Starting recipes grant no finished items"), Inventory->GetUsedSlotCount(), 0);
    Inventory->AddItem(Wood, 19);
    TestEqual(TEXT("Preview reports missing ingredients"), Inventory->GetCraftReadiness(Recipe), EEWCraftResult::MissingIngredients);
    TestEqual(TEXT("Preview never consumes ingredients"), Inventory->GetItemCount(Wood), 19);
    TestEqual(TEXT("Insufficient ingredients rejected"), Inventory->CraftItem(Recipe), EEWCraftResult::MissingIngredients);
    TestEqual(TEXT("Failed craft preserves wood"), Inventory->GetItemCount(Wood), 19);
    Inventory->AddItem(Wood, 1);
    TestEqual(TEXT("Preview allows a consumed stack to free output space"), Inventory->GetCraftReadiness(Recipe), EEWCraftResult::Success);
    TestEqual(TEXT("Twenty wood crafts one axe"), Inventory->CraftItem(Recipe), EEWCraftResult::Success);
    TestEqual(TEXT("All required wood consumed"), Inventory->GetItemCount(Wood), 0);
    TestEqual(TEXT("Exactly one output"), Inventory->GetItemCount(Axe), 1);
    Inventory->AddItem(Axe, 22); Inventory->AddItem(Wood, 21);
    TestEqual(TEXT("Preview reports output capacity failure"), Inventory->GetCraftReadiness(Recipe), EEWCraftResult::InventoryFull);
    TestEqual(TEXT("No output space rejected"), Inventory->CraftItem(Recipe), EEWCraftResult::InventoryFull);
    TestEqual(TEXT("Capacity failure preserves costs"), Inventory->GetItemCount(Wood), 21);
    TestEqual(TEXT("Capacity failure preserves output"), Inventory->GetItemCount(Axe), 23);
    Inventory->RemoveItem(Axe, 23);
    Recipe->Ingredients.Add(Cost);
    TestEqual(TEXT("Duplicate ingredient lines aggregate"), Inventory->CraftItem(Recipe), EEWCraftResult::MissingIngredients);
    Cost.Quantity = MAX_int32; Recipe->Ingredients.Add(Cost);
    TestEqual(TEXT("Overflow authoring rejected"), Inventory->CraftItem(Recipe), EEWCraftResult::InvalidRecipe);
    Owner->SetRole(ROLE_SimulatedProxy);
    auto* ClientInventory = NewObject<UEWInventoryComponent>(Owner);
    ClientInventory->StartingRecipes = {Recipe};
    ClientInventory->InitializeStartingRecipes();
    TestEqual(TEXT("Client initialization cannot grant a baseline recipe"), ClientInventory->GetAvailableRecipes().Num(), 0);
    TestFalse(TEXT("Client cannot unlock"), Inventory->UnlockRecipe(Recipe));
    TestEqual(TEXT("Client cannot craft"), Inventory->CraftItem(Recipe), EEWCraftResult::NotAuthority);
    return true;
}
#endif
