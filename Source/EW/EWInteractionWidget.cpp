#include "EWInteractionWidget.h"
#include "EWInnTorchPickup.h"
#include "Rendering/DrawElements.h"
#include "EWPlayerController.h"
#include "EWCharacter.h"
#include "EWInteractable.h"
#include "EWInteractionComponent.h"
#include "Gathering/EWHarvestTree.h"
#include "Gathering/EWMineable.h"
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
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"

TSharedRef<SWidget> UEWInteractionWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
        WidgetTree->RootWidget = Canvas;
        InnMessage = WidgetTree->ConstructWidget<UTextBlock>();
        InnMessage->SetText(FText::FromString(TEXT("ye, this looks like it will be useful")));
        auto InnFont = InnMessage->GetFont(); InnFont.Size = 22; InnMessage->SetFont(InnFont);
        InnMessage->SetJustification(ETextJustify::Center);
        InnMessage->SetAutoWrapText(true);
        InnMessage->SetShadowColorAndOpacity(FLinearColor::Black); InnMessage->SetShadowOffset(FVector2D(1,1));
        auto* InnSlot = Canvas->AddChildToCanvas(InnMessage);
        InnSlot->SetAnchors(FAnchors(.5f,0)); InnSlot->SetAlignment(FVector2D(.5f,0));
        InnSlot->SetOffsets(FMargin(0,35,600,64)); InnMessage->SetVisibility(ESlateVisibility::Collapsed);
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
    auto* Torch = Cast<AEWInnTorchPickup>(Target);
    const bool bNoticeTorch = Torch && Torch->CanInteract_Implementation(Survivor);
    InnMessage->SetVisibility(bNoticeTorch ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (bNoticeTorch) HighlightedTorches.AddUnique(Torch);
    HighlightedTorches.RemoveAll([Survivor](const TWeakObjectPtr<AEWInnTorchPickup>& Item)
        { return !Item.IsValid() || Item->IsActorBeingDestroyed() || Item->HasCollected(Survivor); });
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
    if (const auto* Node = Cast<AEWMineable>(Target))
    {
        if (!Node->CanAccessSource(Survivor))
        {
            Prompt->SetText(FText::GetEmpty()); Progress->SetPercent(0);
            Panel->SetVisibility(ESlateVisibility::Collapsed); return;
        }
        Prompt->SetText(Node->CanMine(Survivor)
            ? (PC->UsesControllerPrompts() ? NSLOCTEXT("Elitewake","MineRT","RT: Mine resource")
                : NSLOCTEXT("Elitewake","MineMouse","Left Mouse: Mine resource"))
            : NSLOCTEXT("Elitewake","MineNeedsPickaxe","Equip a pickaxe to mine"));
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
FText UEWInteractionWidget::GetInnMessage() const
{
    return InnMessage && InnMessage->GetVisibility()!=ESlateVisibility::Collapsed ? InnMessage->GetText() : FText::GetEmpty();
}
float UEWInteractionWidget::GetDisplayedProgress() const { return Progress ? Progress->GetPercent() : 0.f; }

int32 UEWInteractionWidget::NativePaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& Clip,
    FSlateWindowElementList& Elements, int32 Layer, const FWidgetStyle& Style, bool bEnabled) const
{
    const int32 Base = Super::NativePaint(Args, Geometry, Clip, Elements, Layer, Style, bEnabled);
    const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
    const auto* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    if (!Survivor || PC->IsInventoryOpen() || Survivor->GetSurvivalComponent()->GetHealth() <= 0.f) return Base;
    for (const auto& Weak : HighlightedTorches)
    {
        auto* Torch = Weak.Get(); if (!Torch || Torch->HasCollected(Survivor)) continue;
        FVector Origin, Extent; Torch->GetActorBounds(false, Origin, Extent);
        FVector2D Minimum(FLT_MAX,FLT_MAX), Maximum(-FLT_MAX,-FLT_MAX);
        bool bProjected = true;
        for (int32 Corner=0; Corner<8; ++Corner)
        {
            FVector2D Point;
            if (!PC->ProjectWorldLocationToScreen(Origin+Extent*FVector(Corner&1 ? 1:-1,Corner&2 ? 1:-1,Corner&4 ? 1:-1),Point,true))
            { bProjected=false; break; }
            // Projection is in physical viewport pixels; Slate geometry uses logical units.
            if (!PC->GetLocalPlayer() || !PC->GetLocalPlayer()->ViewportClient) { bProjected=false; break; }
            FVector2D ViewportSize; PC->GetLocalPlayer()->ViewportClient->GetViewportSize(ViewportSize);
            if (ViewportSize.X<=0 || ViewportSize.Y<=0) { bProjected=false; break; }
            Point *= Geometry.GetLocalSize()/ViewportSize;
            Minimum.X=FMath::Min(Minimum.X,Point.X); Minimum.Y=FMath::Min(Minimum.Y,Point.Y);
            Maximum.X=FMath::Max(Maximum.X,Point.X); Maximum.Y=FMath::Max(Maximum.Y,Point.Y);
        }
        if (!bProjected) continue;
        Minimum-=FVector2D(4); Maximum+=FVector2D(4);
        TArray<FVector2D> Points={Minimum,FVector2D(Maximum.X,Minimum.Y),Maximum,FVector2D(Minimum.X,Maximum.Y),Minimum};
        FSlateDrawElement::MakeLines(Elements,Base+1,Geometry.ToPaintGeometry(),Points,ESlateDrawEffect::None,FLinearColor(.9f,.93f,1),true,2.f);
    }
    return Base+1;
}
