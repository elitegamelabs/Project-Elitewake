#include "EWInteractionWidget.h"
#include "EWPlayerController.h"
#include "EWCharacter.h"
#include "EWInteractable.h"
#include "EWInteractionComponent.h"
#include "Gathering/EWHarvestTree.h"
#include "EWSurvivalComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/ProgressBar.h"
#include "GameFramework/GameStateBase.h"
#include "Engine/World.h"

TSharedRef<SWidget> UEWInteractionWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
        WidgetTree->RootWidget = Canvas;
        Panel = WidgetTree->ConstructWidget<UBorder>();
        Panel->SetPadding(FMargin(12));
        Panel->SetBrushColor(FLinearColor(.015f,.025f,.035f,.85f));
        auto* PanelSlot = Canvas->AddChildToCanvas(Panel);
        PanelSlot->SetAnchors(FAnchors(.5f,.62f)); PanelSlot->SetAlignment(FVector2D(.5,.5));
        PanelSlot->SetOffsets(FMargin(0,0,460,90));
        auto* Content = WidgetTree->ConstructWidget<UVerticalBox>(); Panel->SetContent(Content);
        Prompt = WidgetTree->ConstructWidget<UTextBlock>();
        auto Font = Prompt->GetFont(); Font.Size = 22; Prompt->SetFont(Font);
        Prompt->SetJustification(ETextJustify::Center); Prompt->SetAutoWrapText(true);
        Content->AddChildToVerticalBox(Prompt);
        Progress = WidgetTree->ConstructWidget<UProgressBar>();
        Progress->SetFillColorAndOpacity(FLinearColor(.25f,.8f,.95f));
        Content->AddChildToVerticalBox(Progress)->SetPadding(FMargin(0,8,0,0));
        Panel->SetVisibility(ESlateVisibility::Collapsed);
    }
    return Super::RebuildWidget();
}
void UEWInteractionWidget::NativeConstruct()
{
    Super::NativeConstruct(); SetVisibility(ESlateVisibility::HitTestInvisible);
}
void UEWInteractionWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    if (!Panel || !Prompt || !Progress) return;
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    auto* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    AActor* Target = Survivor && PC && !PC->IsInventoryOpen()
        && Survivor->GetSurvivalComponent()->GetHealth() > 0 ? FEWInteractionTargeting::FindTarget(Survivor) : nullptr;
    if (const auto* Tree = Cast<AEWHarvestTree>(Target))
    {
        if (!Tree->CanAccessSource(Survivor))
        {
            Prompt->SetText(FText::GetEmpty()); Progress->SetPercent(0);
            Panel->SetVisibility(ESlateVisibility::Collapsed); return;
        }
        Prompt->SetText(Tree->CanHarvest(Survivor)
            ? (PC->UsesControllerPrompts() ? NSLOCTEXT("Elitewake","HarvestRT","RT: Chop tree")
                : NSLOCTEXT("Elitewake","HarvestMouse","Left Mouse: Chop tree"))
            : NSLOCTEXT("Elitewake","HarvestNeedsHatchet","Equip a hatchet to harvest"));
        Progress->SetPercent(0); Progress->SetVisibility(ESlateVisibility::Collapsed);
        Panel->SetVisibility(ESlateVisibility::HitTestInvisible); return;
    }
    if (!Target || !IEWInteractable::Execute_CanInteract(Target, Survivor))
    {
        Prompt->SetText(FText::GetEmpty()); Progress->SetPercent(0);
        Panel->SetVisibility(ESlateVisibility::Collapsed); return;
    }
    const FText Action = IEWInteractable::Execute_GetInteractionPrompt(Target, Survivor);
    if (Action.IsEmpty())
    {
        Prompt->SetText(FText::GetEmpty()); Progress->SetPercent(0);
        Panel->SetVisibility(ESlateVisibility::Collapsed); return;
    }
    const bool bHold = IEWInteractable::Execute_GetInteractionMode(Target) == EEWInteractionMode::Hold;
    Prompt->SetText(FText::Format(bHold ? NSLOCTEXT("Elitewake","HoldPrompt","Hold {0}: {1}")
        : NSLOCTEXT("Elitewake","PressPrompt","{0}: {1}"),
        FText::FromString(PC->UsesControllerPrompts() ? TEXT("X") : TEXT("E")), Action));
    Panel->SetVisibility(ESlateVisibility::HitTestInvisible);
    Progress->SetVisibility(bHold ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    const FEWHoldState State = PC->GetInteractionComponent()->GetHoldState();
    const double Now = GetWorld()->GetGameState() ? GetWorld()->GetGameState()->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
    Progress->SetPercent(bHold && PC->HasLocalInteractionIntent() && State.Target == Target && State.Duration > 0
        ? FMath::Clamp(float((Now-State.StartTime)/State.Duration),0.f,1.f) : 0.f);
}
FText UEWInteractionWidget::GetDisplayedPrompt() const { return Prompt ? Prompt->GetText() : FText::GetEmpty(); }
float UEWInteractionWidget::GetDisplayedProgress() const { return Progress ? Progress->GetPercent() : 0.f; }
