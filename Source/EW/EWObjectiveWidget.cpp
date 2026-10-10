#include "EWObjectiveWidget.h"
#include "EWObjectiveComponent.h"
#include "EWPlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/SizeBox.h"
#include "Components/VerticalBox.h"
#include "Components/TextBlock.h"

TSharedRef<SWidget> UEWObjectiveWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
        WidgetTree->RootWidget = Canvas;
        WidthBox = WidgetTree->ConstructWidget<USizeBox>();
        WidthBox->SetWidthOverride(340);
        auto* PanelSlot = Canvas->AddChildToCanvas(WidthBox);
        PanelSlot->SetAutoSize(true);
        PanelSlot->SetPosition(FVector2D(24,100));
        Panel = WidgetTree->ConstructWidget<UBorder>();
        Panel->SetPadding(FMargin(12));
        Panel->SetBrushColor(FLinearColor(.015f,.025f,.035f,.65f));
        WidthBox->SetContent(Panel);
        auto* Content = WidgetTree->ConstructWidget<UVerticalBox>();
        Panel->SetContent(Content);
        auto* Title = WidgetTree->ConstructWidget<UTextBlock>();
        Title->SetText(NSLOCTEXT("Elitewake","CurrentObjective","Current objective"));
        auto Font = Title->GetFont(); Font.Size = 14; Title->SetFont(Font);
        Title->SetColorAndOpacity(FLinearColor(.75f,.78f,.82f));
        Content->AddChildToVerticalBox(Title);
        Description = WidgetTree->ConstructWidget<UTextBlock>();
        Font.Size = 18; Description->SetFont(Font);
        Description->SetAutoWrapText(true);
        Content->AddChildToVerticalBox(Description);
        Count = WidgetTree->ConstructWidget<UTextBlock>();
        Font.Size = 16; Count->SetFont(Font);
        Content->AddChildToVerticalBox(Count);
        Panel->SetVisibility(ESlateVisibility::Collapsed);
    }
    return Super::RebuildWidget();
}

void UEWObjectiveWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UEWObjectiveWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    if (!Panel || !Description || !Count) return;
    WidthBox->SetWidthOverride(FMath::Clamp(Geometry.GetLocalSize().X-48.f, 100.f, 340.f));
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const auto* Objectives = PC ? PC->GetObjectiveComponent() : nullptr;
    const auto State = Objectives ? Objectives->GetState() : FEWObjectiveState();
    const bool bShow = PC && !PC->IsInventoryOpen() && State.Steps.IsValidIndex(State.StepIndex)
        && !State.Steps[State.StepIndex].Description.IsEmpty();
    Panel->SetVisibility(bShow ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (!bShow)
    {
        Description->SetText(FText::GetEmpty()); Count->SetText(FText::GetEmpty()); return;
    }
    const auto& Step = State.Steps[State.StepIndex];
    Description->SetText(Step.Description);
    Count->SetText(FText::Format(NSLOCTEXT("Elitewake","ObjectiveCount","{0} / {1}"),
        FText::AsNumber(State.Progress), FText::AsNumber(Step.RequiredCount)));
}

bool UEWObjectiveWidget::IsObjectiveVisible() const
{
    return Panel && Panel->GetVisibility() != ESlateVisibility::Collapsed;
}
FText UEWObjectiveWidget::GetDisplayedDescription() const
{
    return IsObjectiveVisible() ? Description->GetText() : FText::GetEmpty();
}
FText UEWObjectiveWidget::GetDisplayedCount() const
{
    return IsObjectiveVisible() ? Count->GetText() : FText::GetEmpty();
}
