// Copyright Elite Game Labs. All Rights Reserved.

#include "EWInventoryWidget.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/SlateColor.h"

TSharedRef<SWidget> UEWInventoryWidget::RebuildWidget()
{
	// The native tree must exist before UUserWidget creates its Slate content.
	BuildWidgetTree();
	return Super::RebuildWidget();
}

void UEWInventoryWidget::NativeConstruct()
{
	Super::NativeConstruct();

	BoundInventory = ResolveInventory();
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.AddDynamic(this, &UEWInventoryWidget::RefreshInventory);
	}

	RefreshInventory();
}

void UEWInventoryWidget::NativeDestruct()
{
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.RemoveDynamic(this, &UEWInventoryWidget::RefreshInventory);
	}
	BoundInventory = nullptr;
	Super::NativeDestruct();
}

void UEWInventoryWidget::BuildWidgetTree()
{
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("InventoryPanel"));
	Panel->SetBrushColor(FLinearColor(0.015f, 0.025f, 0.035f, 0.94f));
	Panel->SetPadding(FMargin(24.0f));
	Panel->SetHorizontalAlignment(HAlign_Fill);
	Panel->SetVerticalAlignment(VAlign_Fill);
	WidgetTree->RootWidget = Panel;

	UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryContent"));
	Panel->SetContent(Content);

	UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryTitle"));
	Title->SetText(FText::FromString(TEXT("INVENTORY")));
	Title->SetColorAndOpacity(FSlateColor(FLinearColor(0.25f, 0.85f, 0.95f)));
	FSlateFontInfo TitleFont = Title->GetFont();
	TitleFont.Size = 30;
	Title->SetFont(TitleFont);
	Content->AddChildToVerticalBox(Title)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 12.0f));

	SummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventorySummary"));
	SummaryText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
	Content->AddChildToVerticalBox(SummaryText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 18.0f));

	ItemsBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryItems"));
	Content->AddChildToVerticalBox(ItemsBox);

	UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryHint"));
	Hint->SetText(FText::FromString(TEXT("Press I to close")));
	Hint->SetColorAndOpacity(FSlateColor(FLinearColor(0.55f, 0.6f, 0.65f)));
	Content->AddChildToVerticalBox(Hint)->SetPadding(FMargin(0.0f, 24.0f, 0.0f, 0.0f));
}

void UEWInventoryWidget::RefreshInventory()
{
	if (!SummaryText || !ItemsBox)
	{
		return;
	}

	UEWInventoryComponent* Inventory = BoundInventory ? BoundInventory.Get() : ResolveInventory();
	if (!Inventory)
	{
		SummaryText->SetText(FText::FromString(TEXT("Inventory unavailable")));
		return;
	}

	float MaxWeight = 0.0f;
	if (const AEWCharacter* Character = Cast<AEWCharacter>(GetOwningPlayerPawn()))
	{
		if (const UEWSurvivalComponent* Survival = Character->GetSurvivalComponent())
		{
			MaxWeight = Survival->GetMaxCarryWeight();
		}
	}

	SummaryText->SetText(FText::FromString(FString::Printf(TEXT("Slots %d / %d     Weight %.1f / %.1f kg"),
		Inventory->GetUsedSlotCount(), Inventory->GetMaxSlotCount(), Inventory->GetTotalWeight(), MaxWeight)));
	ItemsBox->ClearChildren();

	const TArray<FEWInventoryEntry> Entries = Inventory->GetInventoryEntries();
	if (Entries.IsEmpty())
	{
		UTextBlock* EmptyText = WidgetTree->ConstructWidget<UTextBlock>();
		EmptyText->SetText(FText::FromString(TEXT("Inventory is empty.")));
		EmptyText->SetColorAndOpacity(FSlateColor(FLinearColor(0.7f, 0.72f, 0.75f)));
		ItemsBox->AddChildToVerticalBox(EmptyText);
		return;
	}

	for (const FEWInventoryEntry& Entry : Entries)
	{
		if (!Entry.ItemDefinition)
		{
			continue;
		}

		UTextBlock* ItemText = WidgetTree->ConstructWidget<UTextBlock>();
		const FString Name = Entry.ItemDefinition->DisplayName.IsEmpty()
			? Entry.ItemDefinition->ItemId.ToString()
			: Entry.ItemDefinition->DisplayName.ToString();
		ItemText->SetText(FText::FromString(FString::Printf(TEXT("%s   x%d     %.1f kg"),
			*Name, Entry.Quantity, Entry.ItemDefinition->UnitWeight * Entry.Quantity)));
		ItemText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
		ItemsBox->AddChildToVerticalBox(ItemText)->SetPadding(FMargin(0.0f, 4.0f));
	}
}

UEWInventoryComponent* UEWInventoryWidget::ResolveInventory() const
{
	if (const AEWCharacter* Character = Cast<AEWCharacter>(GetOwningPlayerPawn()))
	{
		return Character->GetInventoryComponent();
	}
	return nullptr;
}
