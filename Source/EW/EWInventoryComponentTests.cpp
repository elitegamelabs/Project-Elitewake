// Copyright Elite Game Labs. All Rights Reserved.

#if WITH_DEV_AUTOMATION_TESTS

#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"
#include "Engine/AssetManager.h"

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FEWPersistedInventoryItemTest,
	"Elitewake.Inventory.PersistedTestItem",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWPersistedInventoryItemTest::RunTest(const FString& Parameters)
{
	const FPrimaryAssetId WoodId(TEXT("EWItem"), TEXT("Test.Wood"));
	const FSoftObjectPath WoodPath = UAssetManager::Get().GetPrimaryAssetPath(WoodId);
	TestTrue(TEXT("Saved Wood is discovered by the configured asset scan"), WoodPath.IsValid());
	UEWItemDefinition* Wood = Cast<UEWItemDefinition>(WoodPath.TryLoad());
	if (!TestNotNull(TEXT("Saved native item definition loads"), Wood))
	{
		return false;
	}
	TestEqual(TEXT("Saved item preserves its stable primary ID"), Wood->GetPrimaryAssetId(), WoodId);
	TestEqual(TEXT("Resource stack follows the current Bible"), Wood->MaxStackSize, 250);

	AActor* Owner = NewObject<AActor>();
	UEWSurvivalComponent* Survival = NewObject<UEWSurvivalComponent>(Owner);
	UEWInventoryComponent* Inventory = NewObject<UEWInventoryComponent>(Owner);
	Owner->AddInstanceComponent(Survival);
	Owner->AddInstanceComponent(Inventory);

	TestEqual(TEXT("251 saved items are accepted"), Inventory->AddItem(Wood, 251), 251);
	TestEqual(TEXT("251 items cross the real asset stack boundary"), Inventory->GetUsedSlotCount(), 2);
	TestTrue(TEXT("Loaded fixture weight reaches survival"), FMath::IsNearlyEqual(Survival->GetCarriedWeight(), 251 * Wood->UnitWeight));
	TestEqual(TEXT("Only remaining slot capacity is accepted"), Inventory->AddItem(Wood, 6000), 5749);
	TestEqual(TEXT("Full inventory holds 24 resource stacks"), Inventory->GetUsedSlotCount(), 24);
	TestEqual(TEXT("Excess grant cannot overfill inventory"), Inventory->AddItem(Wood, 1), 0);
	TestEqual(TEXT("Removing all content returns actual accepted count"), Inventory->RemoveItem(Wood, 6001), 6000);
	TestEqual(TEXT("Removing saved content clears slots"), Inventory->GetUsedSlotCount(), 0);
	TestEqual(TEXT("Removing saved content clears carried weight"), Survival->GetCarriedWeight(), 0.0f);
	return true;
}

#endif
