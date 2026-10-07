#include "EWHotbarWidget.h"
#include "EWCharacter.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/ProgressBar.h"
#include "EWInventoryComponent.h"

void UEWHotbarSlotButton::InitializeSlot(int32 NewSlotIndex)
{
    SlotIndex = NewSlotIndex;
    OnClicked.AddUniqueDynamic(this, &UEWHotbarSlotButton::EmitSlot);
}
void UEWHotbarSlotButton::EmitSlot() { OnSlotPressed.Broadcast(SlotIndex); }

TSharedRef<SWidget> UEWHotbarWidget::RebuildWidget()
{
    BuildWidgetTree();
    return Super::RebuildWidget();
}

void UEWHotbarWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::HitTestInvisible);
    LastDisplay.Reset();
}

void UEWHotbarWidget::BuildWidgetTree()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;
    auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
    WidgetTree->RootWidget = Canvas;
    auto* Panel = WidgetTree->ConstructWidget<UBorder>();
    Panel->SetBrushColor(FLinearColor(.015f,.025f,.035f,.9f));
    Panel->SetPadding(FMargin(6));
    auto* CanvasSlot = Canvas->AddChildToCanvas(Panel);
    CanvasSlot->SetAnchors(FAnchors(0.f,1.f,1.f,1.f));
    CanvasSlot->SetOffsets(FMargin(12,-212,12,200));
    auto* Content = WidgetTree->ConstructWidget<UVerticalBox>();
    Panel->SetContent(Content);
    Status = WidgetTree->ConstructWidget<UTextBlock>();
    auto Font = Status->GetFont(); Font.Size = 22; Status->SetFont(Font);
    Status->SetAutoWrapText(true);
    Content->AddChildToVerticalBox(Status);
    auto* Slots = WidgetTree->ConstructWidget<UHorizontalBox>();
    Content->AddChildToVerticalBox(Slots);
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
    {
        auto* Cell = WidgetTree->ConstructWidget<UBorder>();
        Cell->SetPadding(FMargin(4));
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
        Label->SetFont(Font); Label->SetAutoWrapText(true);
        auto* CellContent = WidgetTree->ConstructWidget<UVerticalBox>();
        CellContent->AddChildToVerticalBox(Label);
        auto* Freshness = WidgetTree->ConstructWidget<UProgressBar>();
        Freshness->SetFillColorAndOpacity(FLinearColor(.25f,.8f,.35f));
        CellContent->AddChildToVerticalBox(Freshness);
        FreshnessBars.Add(Freshness);
        Cell->SetContent(CellContent);
        auto* CellSlot = Slots->AddChildToHorizontalBox(Cell);
        CellSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); CellSlot->SetPadding(FMargin(2));
        Labels.Add(Label); Cells.Add(Cell);
    }
}

void UEWHotbarWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    const auto* Pawn = Cast<AEWCharacter>(GetOwningPlayerPawn());
    UEWHotbarComponent* Hotbar = Pawn ? Pawn->GetHotbarComponent() : nullptr;
    if (PreviousHotbar.Get() != Hotbar)
    {
        PreviousHotbar = Hotbar; MessageRemaining = 0; LastDisplay.Reset();
    }
    if (MessageRemaining > 0.f) MessageRemaining = FMath::Max(0.f,MessageRemaining-DeltaTime);
    if (MessageRemaining == 0.f) Status->SetText(FText::GetEmpty());
    FString Display;
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
    {
        UEWItemDefinition* Item = Hotbar ? Hotbar->GetBoundItem(i) : nullptr;
        const float Freshness = Pawn ? Pawn->GetInventoryComponent()->GetFoodFreshness(Item) : -1.f;
        Display += FString::Printf(TEXT("%d:%s:%d:%.4f;"),i,*GetPathNameSafe(Item),Hotbar ? Hotbar->GetOwnedQuantity(Item) : 0,Freshness);
    }
    Display += FString::FromInt(Hotbar ? Hotbar->GetSelectedSlot() : INDEX_NONE);
    if (Display == LastDisplay) return;
    LastDisplay = Display;
    for (int32 i=0; i<Labels.Num(); ++i)
    {
        const auto* Item = Hotbar ? Hotbar->GetBoundItem(i) : nullptr;
        const int32 Quantity = Hotbar ? Hotbar->GetOwnedQuantity(Item) : 0;
        const float Freshness = Pawn ? Pawn->GetInventoryComponent()->GetFoodFreshness(Item) : -1.f;
        FreshnessBars[i]->SetVisibility(Freshness >= 0.f ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        FreshnessBars[i]->SetPercent(FMath::Max(0.f, Freshness));
        FString Name = Item ? Item->DisplayName.ToString() : TEXT("Empty");
        if (Name.Len()>16) Name=Name.Left(15)+TEXT("…");
        Labels[i]->SetText(FText::FromString(FString::Printf(TEXT("%d\n%s\n%s"),i+1,*Name,
            Item ? *(Quantity>0 ? FString::Printf(TEXT("x%d"),Quantity) : FString(TEXT("Unavailable"))) : TEXT(""))));
        Labels[i]->SetColorAndOpacity(FSlateColor(Item && Quantity==0 ? FLinearColor(.5f,.5f,.5f) : FLinearColor::White));
        Cells[i]->SetBrushColor(Hotbar && Hotbar->GetSelectedSlot()==i ? FLinearColor(.06f,.35f,.45f) : FLinearColor(.025f,.045f,.06f));
    }
}

FText UEWHotbarWidget::ResultText(EEWHotbarResult Result)
{
    switch (Result)
    {
        case EEWHotbarResult::Success: return FText::FromString(TEXT("Hotbar updated"));
        case EEWHotbarResult::EmptySlot: return FText::FromString(TEXT("That hotbar slot is empty"));
        case EEWHotbarResult::NotOwned: return FText::FromString(TEXT("That item is currently unavailable"));
        case EEWHotbarResult::UnsupportedAction: return FText::FromString(TEXT("That item's action is not available yet"));
        case EEWHotbarResult::InventoryFull: return FText::FromString(TEXT("Inventory is full — make space to return the equipped item"));
        case EEWHotbarResult::NoBenefit: return FText::FromString(TEXT("Hunger and health are already full"));
        case EEWHotbarResult::UnavailableSurvivor: return FText::FromString(TEXT("You cannot eat while dead"));
        case EEWHotbarResult::InvalidFood: return FText::FromString(TEXT("That food cannot be eaten"));
        default: return FText::FromString(TEXT("Hotbar change could not be completed"));
    }
}
void UEWHotbarWidget::ShowResult(EEWHotbarResult Result)
{
    if (Status) Status->SetText(ResultText(Result));
    MessageRemaining = 3.f;
}
