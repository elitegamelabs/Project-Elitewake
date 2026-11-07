#include "EWArrivalPromptWidget.h"
#include "EWArrivalComponent.h"
#include "EWCharacter.h"
#include "EWInteractionWidget.h"
#include "EWPlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/RichTextBlock.h"
#include "EWControllerIcons.h"
#include "Styling/CoreStyle.h"

TSharedRef<SWidget> UEWArrivalPromptWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
        WidgetTree->RootWidget = Canvas;
        Panel = WidgetTree->ConstructWidget<UBorder>();
        Panel->SetPadding(FMargin(20, 10));
        // Warm off-white on near-black: about 15:1 contrast, readable over sand, grass and sky alike.
        Panel->SetBrushColor(FLinearColor(.012f, .016f, .02f, .78f));
        auto* PanelSlot = Canvas->AddChildToCanvas(Panel);
        PanelSlot->SetAnchors(FAnchors(.5f, HeightFraction));
        PanelSlot->SetAlignment(FVector2D(.5f, .5f));
        PanelSlot->SetAutoSize(true);
        Prompt = WidgetTree->ConstructWidget<URichTextBlock>();
        FTextBlockStyle Style = FTextBlockStyle::GetDefault();
        Style.SetFont(FCoreStyle::GetDefaultFontStyle("Regular", FontSize));
        Style.SetColorAndOpacity(FLinearColor(.93f, .89f, .8f));
        Prompt->SetDefaultTextStyle(Style);
        Prompt->SetDecorators({UEWButtonIconDecorator::StaticClass()});
        Prompt->SetJustification(ETextJustify::Center);
        Panel->SetContent(Prompt);
        Panel->SetVisibility(ESlateVisibility::Collapsed);
    }
    return Super::RebuildWidget();
}

void UEWArrivalPromptWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UEWArrivalPromptWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    if (!Panel || !Prompt) return;
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const auto* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    const auto* Arrival = Survivor ? Survivor->GetArrivalComponent() : nullptr;
    const auto* Interaction = PC ? PC->GetInteractionWidget() : nullptr;
    // One prompt at a time: never over a menu, a death, the helm's controls or the interaction prompt.
    // The arrival's steps first; then, in Saltreach, the town's (slice 5).
    const bool bTown = Arrival && Arrival->IsTownPromptDue();
    const bool bShow = Arrival && (Arrival->IsPromptDue() || bTown) && !Survivor->IsDead() && !Survivor->GetHelmShip()
        && !PC->IsInventoryOpen() && !PC->IsMapOpen() && !PC->IsOptionsMenuOpen() && !PC->IsDialogueOpen()
        && !(Interaction && !Interaction->GetDisplayedPrompt().IsEmpty());
    Panel->SetVisibility(bShow ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    const FText Words = !bShow ? FText::GetEmpty()
        : bTown ? UEWArrivalComponent::TownPromptFor(Arrival->GetTownStep(), PC->UsesControllerPrompts())
                : UEWArrivalComponent::PromptFor(Arrival->GetStep(), PC->UsesControllerPrompts());
    const EEWGamepadFamily Family = PC ? PC->GetPromptFamily() : EEWGamepadFamily::Unknown;
    PlainPrompt = FEWControllerIcons::Expand(Words, Family, false);
    const FText Rich = FEWControllerIcons::Expand(Words, Family, true);
    if (!Prompt->GetText().EqualTo(Rich)) Prompt->SetText(Rich);
}

bool UEWArrivalPromptWidget::IsPromptVisible() const
{
    return Panel && Panel->GetVisibility() != ESlateVisibility::Collapsed;
}

FText UEWArrivalPromptWidget::GetDisplayedPrompt() const
{
    return IsPromptVisible() ? PlainPrompt : FText::GetEmpty();
}
