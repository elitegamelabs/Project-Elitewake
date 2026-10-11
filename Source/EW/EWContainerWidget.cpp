#include "EWContainerWidget.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWInventoryWidget.h"
#include "EWItemDefinition.h"
#include "EWPlayerController.h"
#include "Ships/EWShip.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "InputCoreTypes.h"

namespace
{
    /** Row codes: carried stacks are 0..999, hold stacks are 1000 and up. */
    constexpr int32 HoldOffset = 1000;

    FString Describe(const FEWInventoryEntry& Entry)
    {
        const UEWItemDefinition* Item = Entry.ItemDefinition;
        if (!Item) return FString();
        FString Line = FString::Printf(TEXT("%s  x%d   %.1f kg"), *Item->DisplayName.ToString(), Entry.Quantity, Item->UnitWeight * Entry.Quantity);
        if (Item->FoodKind == EEWFoodKind::Berry && Item->FreshLifetimeSeconds > 0.f)
        {
            const int32 Left = FMath::Max(0, FMath::FloorToInt(Item->FreshLifetimeSeconds - Entry.FoodAgeSeconds));
            Line += FString::Printf(TEXT("   fresh %d:%02d"), Left / 60, Left % 60);
        }
        return Line;
    }

    FString Summarize(const UEWInventoryComponent* Inventory)
    {
        return Inventory ? FString::Printf(TEXT("%d / %d slots   %.1f kg"), Inventory->GetUsedSlotCount(),
            Inventory->GetMaxSlotCount(), Inventory->GetTotalWeight()) : FString();
    }
}

void UEWContainerWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    SetIsFocusable(true);
}

void UEWContainerWidget::SetContainer(AActor* InContainer)
{
    Container = InContainer;
    Signature.Reset();
    OutOfReachSeconds = 0.f;
    Refresh();
}

TSharedRef<SWidget> UEWContainerWidget::RebuildWidget()
{
    if (WidgetTree->RootWidget) return Super::RebuildWidget();
    auto* Backdrop = WidgetTree->ConstructWidget<UBorder>();
    Backdrop->SetPadding(FMargin(24));
    Backdrop->SetBrushColor(FLinearColor(.025f, .035f, .045f, .9f));
    WidgetTree->RootWidget = Backdrop;
    auto* Body = WidgetTree->ConstructWidget<UVerticalBox>();
    Backdrop->SetContent(Body);
    auto MakeText = [this](const FString& Value, int32 Size, UPanelWidget* Parent)
    {
        auto* T = WidgetTree->ConstructWidget<UTextBlock>();
        T->SetText(FText::FromString(Value));
        auto Font = T->GetFont(); Font.Size = Size; T->SetFont(Font);
        T->SetColorAndOpacity(FSlateColor(FLinearColor(.85f, .87f, .9f)));
        Parent->AddChild(T);
        return T;
    };
    Title = MakeText(TEXT("SHIP'S HOLD"), 22, Body);
    MakeText(TEXT("Click a stack to move it across.   Esc / Tab / I to close."), 14, Body);
    auto* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
    Body->AddChild(Columns);
    auto MakeColumn = [&](const FString& Heading, TObjectPtr<UTextBlock>& Summary, TObjectPtr<UVerticalBox>& List)
    {
        auto* Column = WidgetTree->ConstructWidget<UVerticalBox>();
        if (auto* ColumnSlot = Columns->AddChildToHorizontalBox(Column))
        {
            ColumnSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
            ColumnSlot->SetPadding(FMargin(0, 16, 24, 0));
        }
        MakeText(Heading, 18, Column);
        Summary = MakeText(FString(), 14, Column);
        auto* Scroll = WidgetTree->ConstructWidget<UScrollBox>();
        Column->AddChild(Scroll);
        List = WidgetTree->ConstructWidget<UVerticalBox>();
        Scroll->AddChild(List);
    };
    MakeColumn(TEXT("Carried"), CarriedSummary, CarriedList);
    MakeColumn(TEXT("Hold"), HoldSummary, HoldList);
    Refresh();
    return Super::RebuildWidget();
}

UEWInventoryComponent* UEWContainerWidget::CarriedInventory() const
{
    const auto* Survivor = GetOwningPlayer() ? Cast<AEWCharacter>(GetOwningPlayer()->GetPawn()) : nullptr;
    return Survivor ? Survivor->GetInventoryComponent() : nullptr;
}

UEWInventoryComponent* UEWContainerWidget::HoldInventory() const
{
    const auto* Ship = Cast<AEWShip>(Container.Get());
    return Ship ? Ship->GetCargo() : nullptr;
}

void UEWContainerWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    // Close if the hold is gone or out of reach for a moment (the ship sailed off, or the survivor left).
    const auto* Ship = Cast<AEWShip>(Container.Get());
    const auto* Survivor = GetOwningPlayer() ? Cast<AEWCharacter>(GetOwningPlayer()->GetPawn()) : nullptr;
    OutOfReachSeconds = Ship && Survivor && Ship->CanAccessCargo(Survivor) ? 0.f : OutOfReachSeconds + Delta;
    if (OutOfReachSeconds > 1.f) { Close(); return; }
    RefreshRemaining -= Delta;
    if (RefreshRemaining <= 0.f) { RefreshRemaining = .2f; Refresh(); }
}

void UEWContainerWidget::Refresh()
{
    if (!CarriedList || !HoldList) return;
    const UEWInventoryComponent* Carried = CarriedInventory();
    const UEWInventoryComponent* Hold = HoldInventory();
    CarriedSummary->SetText(FText::FromString(Summarize(Carried)));
    HoldSummary->SetText(FText::FromString(Summarize(Hold)));
    FString Next;
    for (const UEWInventoryComponent* Inventory : {Carried, Hold})
    {
        Next += TEXT("|");
        if (Inventory) for (const FEWInventoryEntry& Entry : Inventory->GetInventoryEntries()) Next += Describe(Entry) + TEXT(";");
    }
    if (Next == Signature) return;
    Signature = Next;
    auto Fill = [this](UVerticalBox* List, const UEWInventoryComponent* Inventory, int32 Offset)
    {
        List->ClearChildren();
        if (!Inventory) return;
        const TArray<FEWInventoryEntry> Entries = Inventory->GetInventoryEntries();
        for (int32 i = 0; i < Entries.Num(); ++i)
        {
            auto* Row = WidgetTree->ConstructWidget<UEWRecipeButton>();
            Row->Initialize(Offset + i);
            Row->OnRecipePressed.AddDynamic(this, &UEWContainerWidget::Move);
            Row->SetBackgroundColor(FLinearColor(.09f, .12f, .15f));
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
            Label->SetText(FText::FromString(Describe(Entries[i])));
            auto Font = Label->GetFont(); Font.Size = 16; Label->SetFont(Font);
            Row->SetContent(Label);
            List->AddChild(Row);
        }
    };
    Fill(CarriedList, Carried, 0);
    Fill(HoldList, Hold, HoldOffset);
}

void UEWContainerWidget::Move(int32 Code)
{
    auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const bool bToContainer = Code < HoldOffset;
    const int32 Index = bToContainer ? Code : Code - HoldOffset;
    const UEWInventoryComponent* Source = bToContainer ? CarriedInventory() : HoldInventory();
    if (!PC || !Container.IsValid() || !Source || !Source->GetInventoryEntries().IsValidIndex(Index)) return;
    PC->ServerTransferContainerItem(Container.Get(), bToContainer, Index, Source->GetInventoryEntries()[Index].Quantity);
}

void UEWContainerWidget::Close()
{
    if (auto* PC = Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetInventoryOpen(false);
}

FReply UEWContainerWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Escape || Key == EKeys::Tab || Key == EKeys::I
        || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Gamepad_FaceButton_Top)
    {
        Close();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}
