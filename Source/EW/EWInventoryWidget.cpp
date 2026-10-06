// Copyright Elite Game Labs. All Rights Reserved.

#include "EWInventoryWidget.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "InputCoreTypes.h"
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
    SetIsFocusable(true);
    SelectedIndex = INDEX_NONE;
    bShowingDetails = false;

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
    AnalogDirection = 0;
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
    ItemsScroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("InventoryScroll"));
    ItemsScroll->AddChild(ItemsBox);
    auto* ScrollSlot = Content->AddChildToVerticalBox(ItemsScroll);
    ScrollSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    DetailsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryDetails"));
    DetailsText->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(DetailsText)->SetPadding(FMargin(0,12));

	UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryHint"));
	Hint->SetText(FText::FromString(TEXT("Select: Up/Down, D-pad or left stick, mouse\nDetails: Enter / A / click    Close: I / Y / B / Esc")));
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
        ItemsBox->ClearChildren(); Rows.Reset(); DisplayedEntries.Reset();
        SelectedIndex = INDEX_NONE; bShowingDetails = false;
        DetailsText->SetText(FText::FromString(TEXT("No item selected")));
		return;
	}

    RefreshSummary();
    UEWItemDefinition* PreviousItem = DisplayedEntries.IsValidIndex(SelectedIndex) ? DisplayedEntries[SelectedIndex].ItemDefinition.Get() : nullptr;
    int32 PreviousOrdinal = 0;
    for (int32 i = 0; i < SelectedIndex; ++i)
        if (DisplayedEntries[i].ItemDefinition == PreviousItem) ++PreviousOrdinal;
    DisplayedEntries = Inventory->GetInventoryEntries();
    DisplayedEntries.RemoveAll([](const FEWInventoryEntry& Entry) { return !Entry.ItemDefinition || Entry.Quantity <= 0; });
    int32 Match = INDEX_NONE, Ordinal = 0;
    for (int32 i = 0; i < DisplayedEntries.Num(); ++i)
        if (DisplayedEntries[i].ItemDefinition == PreviousItem && Ordinal++ == PreviousOrdinal) { Match = i; break; }
    SelectedIndex = DisplayedEntries.IsEmpty() ? INDEX_NONE : (Match != INDEX_NONE ? Match : FMath::Clamp(SelectedIndex, 0, DisplayedEntries.Num()-1));
    if (PreviousItem && (SelectedIndex == INDEX_NONE || DisplayedEntries[SelectedIndex].ItemDefinition != PreviousItem)) bShowingDetails = false;
    ItemsBox->ClearChildren();
    Rows.Reset();
    if (DisplayedEntries.IsEmpty())
    {
        UTextBlock* EmptyText = WidgetTree->ConstructWidget<UTextBlock>();
        EmptyText->SetText(FText::FromString(TEXT("Inventory is empty.")));
        ItemsBox->AddChildToVerticalBox(EmptyText);
        bShowingDetails = false;
    }
    for (const FEWInventoryEntry& Entry : DisplayedEntries)
    {
        UBorder* Row = WidgetTree->ConstructWidget<UBorder>();
        Row->SetPadding(FMargin(10,8));
        UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>();
        const FString Name = Entry.ItemDefinition->DisplayName.IsEmpty() ? Entry.ItemDefinition->ItemId.ToString() : Entry.ItemDefinition->DisplayName.ToString();
        Text->SetText(FText::FromString(FString::Printf(TEXT("%s   x%d     %.1f kg"), *Name, Entry.Quantity, Entry.ItemDefinition->UnitWeight * Entry.Quantity)));
        Row->SetContent(Text);
        ItemsBox->AddChildToVerticalBox(Row)->SetPadding(FMargin(0,3));
        Rows.Add(Row);
    }
    UpdateSelection();
}

void UEWInventoryWidget::RefreshSummary()
{
    UEWInventoryComponent* Inventory = BoundInventory.Get();
    if (!Inventory || !SummaryText) return;
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
}

void UEWInventoryWidget::Select(int32 Index)
{
    if (DisplayedEntries.IsEmpty()) return;
    Index = FMath::Clamp(Index, 0, DisplayedEntries.Num()-1);
    if (Index != SelectedIndex) { SelectedIndex = Index; bShowingDetails = false; UpdateSelection(); }
}

void UEWInventoryWidget::UpdateSelection()
{
    for (int32 i=0; i<Rows.Num(); ++i)
        Rows[i]->SetBrushColor(i == SelectedIndex ? FLinearColor(.06f,.35f,.45f,1) : FLinearColor(.025f,.045f,.06f,1));
    if (!DetailsText) return;
    DetailsText->SetText(FText::FromString(SelectedIndex == INDEX_NONE ? TEXT("No item selected") : TEXT("Confirm to view item details")));
    if (bShowingDetails) ConfirmSelection();
    if (Rows.IsValidIndex(SelectedIndex)) ItemsScroll->ScrollWidgetIntoView(Rows[SelectedIndex], true);
    RevealSelectionAfterFrames = 2;
}

void UEWInventoryWidget::ConfirmSelection()
{
    if (!DisplayedEntries.IsValidIndex(SelectedIndex)) return;
    const FEWInventoryEntry& Entry = DisplayedEntries[SelectedIndex];
    bShowingDetails = true;
    DetailsText->SetText(FText::FromString(FString::Printf(TEXT("%s\n%s\nQuantity %d    Unit weight %.1f kg    Stack limit %d"),
        *Entry.ItemDefinition->DisplayName.ToString(), *Entry.ItemDefinition->Description.ToString(), Entry.Quantity,
        Entry.ItemDefinition->UnitWeight, Entry.ItemDefinition->MaxStackSize)));
    // Details change the list's available height; reveal the selected row after that layout change.
    if (Rows.IsValidIndex(SelectedIndex)) ItemsScroll->ScrollWidgetIntoView(Rows[SelectedIndex], true, EDescendantScrollDestination::Center);
    RevealSelectionAfterFrames = 2;
}

FReply UEWInventoryWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key == EKeys::I || Key == EKeys::Gamepad_FaceButton_Top || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Escape)
    {
        if (!Event.IsRepeat()) if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->SetInventoryOpen(false);
        return FReply::Handled();
    }
    if (Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up) { Select(SelectedIndex-1); return FReply::Handled(); }
    if (Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down) { Select(SelectedIndex+1); return FReply::Handled(); }
    if (Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom) { ConfirmSelection(); return FReply::Handled(); }
    return FReply::Handled(); // UI owns input while open, including gameplay bindings.
}

FReply UEWInventoryWidget::NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event)
{
    if (Event.GetKey() == EKeys::Gamepad_LeftY)
    {
        const int32 Direction = FMath::Abs(Event.GetAnalogValue()) >= .5f ? (Event.GetAnalogValue() > 0 ? -1 : 1) : 0;
        if (Direction != AnalogDirection) { AnalogDirection = Direction; AnalogRepeatRemaining = .35f; if (Direction) Select(SelectedIndex+Direction); }
    }
    return FReply::Handled();
}

int32 UEWInventoryWidget::RowAt(const FVector2D& Position) const
{
    if (!ItemsScroll->GetCachedGeometry().IsUnderLocation(Position)) return INDEX_NONE;
    for (int32 i=0; i<Rows.Num(); ++i) if (Rows[i]->GetCachedGeometry().IsUnderLocation(Position)) return i;
    return INDEX_NONE;
}

FReply UEWInventoryWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (!Event.GetCursorDelta().IsNearlyZero()) { const int32 Row = RowAt(Event.GetScreenSpacePosition()); if (Row != INDEX_NONE) Select(Row); }
    return Super::NativeOnMouseMove(Geometry, Event);
}

FReply UEWInventoryWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() == EKeys::LeftMouseButton)
    {
        const int32 Row = RowAt(Event.GetScreenSpacePosition());
        if (Row != INDEX_NONE) { Select(Row); ConfirmSelection(); return FReply::Handled().SetUserFocus(TakeWidget()); }
    }
    return Super::NativeOnMouseButtonDown(Geometry, Event);
}

void UEWInventoryWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    if (UEWInventoryComponent* Inventory = ResolveInventory(); Inventory != BoundInventory)
    {
        if (BoundInventory) BoundInventory->OnInventoryChanged.RemoveDynamic(this, &UEWInventoryWidget::RefreshInventory);
        BoundInventory = Inventory;
        if (BoundInventory) BoundInventory->OnInventoryChanged.AddDynamic(this, &UEWInventoryWidget::RefreshInventory);
        DisplayedEntries.Reset(); SelectedIndex = INDEX_NONE; bShowingDetails = false;
        if (!BoundInventory) { ItemsBox->ClearChildren(); Rows.Reset(); DetailsText->SetText(FText::FromString(TEXT("No item selected"))); }
        RefreshInventory();
    }
    RefreshSummary();
    // Use settled geometry: confirmation may shrink the scroll viewport after the input event.
    if (RevealSelectionAfterFrames > 0 && --RevealSelectionAfterFrames == 0 && Rows.IsValidIndex(SelectedIndex))
    {
        if (SelectedIndex == Rows.Num()-1) ItemsScroll->ScrollToEnd();
        else ItemsScroll->ScrollWidgetIntoView(Rows[SelectedIndex], false);
    }
    if (!HasUserFocus(GetOwningPlayer())) AnalogDirection = 0;
    if (AnalogDirection)
    {
        AnalogRepeatRemaining -= DeltaTime;
        if (AnalogRepeatRemaining <= 0) { Select(SelectedIndex+AnalogDirection); AnalogRepeatRemaining = .18f; }
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
