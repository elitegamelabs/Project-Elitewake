// Copyright Elite Game Labs. All Rights Reserved.

#if WITH_DEV_AUTOMATION_TESTS

#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FEWInventoryStackingTest,
	"Elitewake.Inventory.StackingAndWeight",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWInventoryStackingTest::RunTest(const FString& Parameters)
{
	AActor* Owner = NewObject<AActor>();
	UEWSurvivalComponent* Survival = NewObject<UEWSurvivalComponent>(Owner);
	UEWInventoryComponent* Inventory = NewObject<UEWInventoryComponent>(Owner);
	UEWItemDefinition* Wood = NewObject<UEWItemDefinition>();

	Wood->ItemId = TEXT("Resource.Wood");
	Wood->DisplayName = FText::FromString(TEXT("Wood"));
	Wood->Category = EEWItemCategory::Resource;
	Wood->MaxStackSize = 5;
	Wood->UnitWeight = 2.0f;

	Owner->AddInstanceComponent(Survival);
	Owner->AddInstanceComponent(Inventory);

	TestEqual(TEXT("Eight wood items are accepted"), Inventory->AddItem(Wood, 8), 8);
	TestEqual(TEXT("Eight wood items use two stacks"), Inventory->GetUsedSlotCount(), 2);
	TestEqual(TEXT("Inventory reports the full item count"), Inventory->GetItemCount(Wood), 8);
	TestTrue(TEXT("Inventory reports sufficient quantity"), Inventory->HasItem(Wood, 8));
	TestEqual(TEXT("Inventory weight includes every unit"), Inventory->GetTotalWeight(), 16.0f);
	TestEqual(TEXT("Survival weight follows inventory weight"), Survival->GetCarriedWeight(), 16.0f);

	TestEqual(TEXT("Six wood items are removed"), Inventory->RemoveItem(Wood, 6), 6);
	TestEqual(TEXT("Two wood items remain"), Inventory->GetItemCount(Wood), 2);
	TestEqual(TEXT("Empty stacks are removed"), Inventory->GetUsedSlotCount(), 1);
	TestEqual(TEXT("Weight is recalculated after removal"), Inventory->GetTotalWeight(), 4.0f);
	TestEqual(TEXT("Survival weight is recalculated after removal"), Survival->GetCarriedWeight(), 4.0f);

	return true;
}

#endif
