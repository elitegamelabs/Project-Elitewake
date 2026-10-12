#include "EWSurvivalWidget.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
#include "EWHudIcon.h"
#include "GameFramework/GameStateBase.h"
#include "Components/SizeBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"

namespace
{
    /** Painted status art, in HUD order. A missing texture falls back to the generated icon. */
    const TCHAR* const StatArt[]={
        TEXT("/Game/Elitewake/UI/HUD/T_Health_Matte_v2.T_Health_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Stamina_Matte_v2.T_Stamina_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Hunger_Matte_v2.T_Hunger_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Hydration_Matte_v2.T_Hydration_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Weight_Matte_v2.T_Weight_Matte_v2")};
}

TSharedRef<SWidget> UEWSurvivalWidget::RebuildWidget()
{
    BuildWidgetTree();
    return Super::RebuildWidget();
}

void UEWSurvivalWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UEWSurvivalWidget::BuildWidgetTree()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;
    auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
    WidgetTree->RootWidget = Canvas;
    Panel = WidgetTree->ConstructWidget<UBorder>();
    Panel->SetPadding(FMargin(0));
    Panel->SetBrushColor(FLinearColor::Transparent);
    auto* PanelSlot = Canvas->AddChildToCanvas(Panel);
    PanelSlot->SetAnchors(FAnchors(0.f,1.f));
    PanelSlot->SetOffsets(FMargin(18,-122,320,104));
    auto* Content = WidgetTree->ConstructWidget<UHorizontalBox>();
    Panel->SetContent(Content);
    for (int32 i=0;i<5;++i)
    {
        auto* Column = WidgetTree->ConstructWidget<UVerticalBox>();
        Content->AddChildToHorizontalBox(Column)->SetPadding(FMargin(2));
        auto* Box = WidgetTree->ConstructWidget<USizeBox>();
        Box->SetWidthOverride(60); Box->SetHeightOverride(66);
        Column->AddChildToVerticalBox(Box);
        auto* Bar = WidgetTree->ConstructWidget<UProgressBar>();
        auto Style=Bar->GetWidgetStyle();
        // Painted art: a dark copy shows the empty part and the full-colour copy fills from the bottom.
        UTexture2D* Art=i<UE_ARRAY_COUNT(StatArt) ? LoadObject<UTexture2D>(nullptr,StatArt[i]) : nullptr;
        bHasArt[i]=Art!=nullptr;
        auto* Outline=Art ? Art : EWHudIcon::Make(i,true);auto* Fill=Art ? Art : EWHudIcon::Make(i,false);
        IconTextures.Add(Outline);IconTextures.Add(Fill);
        Style.BackgroundImage.SetResourceObject(Outline);
        Style.BackgroundImage.DrawAs=ESlateBrushDrawType::Image;
        Style.BackgroundImage.TintColor=FSlateColor(Art ? FLinearColor(.16f,.16f,.17f,.85f) : FLinearColor(.8f,.82f,.85f));
        Style.FillImage.SetResourceObject(Fill);Style.FillImage.DrawAs=ESlateBrushDrawType::Image;
        Style.FillImage.TintColor=FSlateColor(FLinearColor::White);
        Bar->SetWidgetStyle(Style);Bar->SetBorderPadding(FVector2D::ZeroVector);
        Bar->SetBarFillStyle(EProgressBarFillStyle::Mask);
        Bar->SetBarFillType(EProgressBarFillType::BottomToTop);
        Box->SetContent(Bar);
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
        auto Font = Label->GetFont(); Font.Size=16; Label->SetFont(Font);
        Label->SetJustification(ETextJustify::Center);
        Label->SetShadowOffset(FVector2D(1,1));Label->SetShadowColorAndOpacity(FLinearColor::Black);
        Column->AddChildToVerticalBox(Label);
        Labels.Add(Label); Bars.Add(Bar);
    }
    auto* Notices = WidgetTree->ConstructWidget<UVerticalBox>();
    NoticePanel=Notices;
    auto* NoticeSlot = Canvas->AddChildToCanvas(Notices);
    NoticeSlot->SetAnchors(FAnchors(1.f,1.f));
    NoticeSlot->SetAlignment(FVector2D(1,1));
    NoticeSlot->SetOffsets(FMargin(-18,-24,320,140));
    for (int32 i=0;i<4;++i)
    {
        auto* Warning = WidgetTree->ConstructWidget<UTextBlock>();
        auto Font=Warning->GetFont(); Font.Size=16; Warning->SetFont(Font);
        Warning->SetJustification(ETextJustify::Right);
        Warning->SetAutoWrapText(true);
        Notices->AddChildToVerticalBox(Warning);
        Warnings.Add(Warning);
    }
}

void UEWSurvivalWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry,DeltaTime);
    const float Dpi=UWidgetLayoutLibrary::GetViewportScale(this);
    const float ReadableScale=FMath::Max(1.f,.8f/FMath::Max(Dpi,.01f));
    Panel->SetRenderTransformPivot(FVector2D(0,1));Panel->SetRenderScale(FVector2D(ReadableScale));
    NoticePanel->SetRenderTransformPivot(FVector2D(1,1));NoticePanel->SetRenderScale(FVector2D(ReadableScale));
    // On narrow screens put the side HUD above the centered hotbar instead of covering slots.
    const bool Stack=Geometry.GetLocalSize().X*.5f-304.f*ReadableScale < 18.f+320.f*ReadableScale+12.f;
    const float Lift=Stack ? 92.f*ReadableScale+14.f : 0.f;
    CastChecked<UCanvasPanelSlot>(Panel->Slot)->SetOffsets(FMargin(18,-122-Lift,320,104));
    CastChecked<UCanvasPanelSlot>(NoticePanel->Slot)->SetOffsets(FMargin(-18,-24-Lift,320,140));

    const auto* Pawn=Cast<AEWCharacter>(GetOwningPlayerPawn());
    auto* Survival=Pawn ? Pawn->GetSurvivalComponent() : nullptr;
    if (PreviousSurvival.Get()!=Survival)
    {
        PreviousSurvival=Survival;
        for (int32 i=0;i<3;++i) { WasEmpty[i]=false; WarningRemaining[i]=0.f; }
        BlinkTime=0.f;
        LastExhaustionCount=Survival ? Survival->GetStaminaExhaustionCount() : 0;
    }
    Panel->SetVisibility(Survival ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (!Survival)
    {
        DisplayedSummary.Reset();
        for (const auto& Label : Labels) Label->SetText(FText::GetEmpty());
        for (const auto& Warning : Warnings) Warning->SetText(FText::GetEmpty());
        for (const auto& Warning : EffectWarnings) Warning->SetText(FText::GetEmpty());
        return;
    }
    BlinkTime+=DeltaTime;
    const float Values[]={Survival->GetHealth(),Survival->GetStamina(),Survival->GetHunger(),Survival->GetHydration(),Survival->GetCarriedWeight()};
    const float Maxima[]={Survival->GetMaxHealth(),Survival->GetMaxStamina(),100.f,100.f,Survival->GetMaxCarryWeight()};
    const TCHAR* Names[]={TEXT("Health"),TEXT("Stamina"),TEXT("Food"),TEXT("Hydration"),TEXT("Weight")};
    const FLinearColor Colors[]={FLinearColor(.85f,.2f,.2f),FLinearColor(1.f,.85f,.05f),FLinearColor(1.f,.45f,.05f),FLinearColor(.2f,.65f,1.f),FLinearColor(.55f,.55f,.58f)};
    DisplayedSummary.Reset();
    for (int32 i=0;i<5;++i)
    {
        FString Text;
        if (i==2 || i==3) Text=FString::Printf(TEXT("%s %.0f%%"),Names[i],Values[i]);
        else if (i==4) Text=FString::Printf(TEXT("Weight %.1f / %.1f kg"),Values[i],Maxima[i]);
        else Text=FString::Printf(TEXT("%s %.0f / %.0f"),Names[i],Values[i],Maxima[i]);
        if (!DisplayedSummary.IsEmpty()) DisplayedSummary+=TEXT("\n");
        DisplayedSummary+=Text;
        const float Fraction=Maxima[i]>0.f ? Values[i]/Maxima[i] : 0.f;
        Labels[i]->SetText(FText::FromString(FString::Printf(TEXT("%.0f%%"),Fraction*100.f)));
        Bars[i]->SetToolTipText(FText::FromString(Text));
        Bars[i]->SetPercent(Maxima[i]>0.f ? FMath::Clamp(Values[i]/Maxima[i],0.f,1.f) : 0.f);
        Bars[i]->SetFillColorAndOpacity(bHasArt[i] ? FLinearColor::White : Colors[i]);
    }
    const int32 Indices[]={2,3,1};
    const bool bNewExhaustion=LastExhaustionCount!=Survival->GetStaminaExhaustionCount();
    LastExhaustionCount=Survival->GetStaminaExhaustionCount();
    const TCHAR* Messages[]={TEXT("You are hungry!"),TEXT("You are thirsty!"),TEXT("You are out of stamina!")};
    const FLinearColor WarningColors[]={FLinearColor::Red,FLinearColor::Yellow,FLinearColor::White};
    for (int32 i=0;i<3;++i)
    {
        const int32 Stat=Indices[i];
        const bool bEmpty=Values[Stat]<=KINDA_SMALL_NUMBER;
        WarningRemaining[i]=FMath::Max(0.f,WarningRemaining[i]-DeltaTime);
        if ((bEmpty && !WasEmpty[i]) || (i==2 && bNewExhaustion)) WarningRemaining[i]=1.5f;
        WasEmpty[i]=bEmpty;
        Warnings[i]->SetText((i<2 ? bEmpty : WarningRemaining[i]>0.f) ? FText::FromString(Messages[i]) : FText::GetEmpty());
        Warnings[i]->SetColorAndOpacity(FSlateColor(WarningColors[i]));
        Labels[Stat]->SetColorAndOpacity(FSlateColor(bEmpty ? WarningColors[i] : FLinearColor::White));

    }
    const bool Overweight=Survival->GetCarriedWeight()>Survival->GetMaxCarryWeight();
    Warnings[3]->SetText(Overweight ? FText::FromString(TEXT("Over encumbered")) : FText::GetEmpty());
    Warnings[3]->SetColorAndOpacity(FSlateColor(FLinearColor(1.f,.65f,.2f)));
    const auto Effects=Survival->GetDebuffNotices();
    const auto* GameState=GetWorld()->GetGameState();
    const double Now=GameState ? GameState->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
    int32 Visible=0;
    for (const auto& Effect : Effects)
    {
        if (Effect.ExpiresAt>=0. && Effect.ExpiresAt<=Now) continue;
        if (Visible==EffectWarnings.Num())
        {
            auto* Warning=WidgetTree->ConstructWidget<UTextBlock>();
            auto Font=Warning->GetFont();Font.Size=16;Warning->SetFont(Font);
            Warning->SetJustification(ETextJustify::Right);Warning->SetAutoWrapText(true);
            NoticePanel->AddChildToVerticalBox(Warning);EffectWarnings.Add(Warning);
        }
        FString Text=Effect.Label.ToString();
        if (Effect.ExpiresAt>=0.)
        {
            const int32 Seconds=FMath::CeilToInt(Effect.ExpiresAt-Now);
            Text+=FString::Printf(TEXT(" %02d:%02d"),Seconds/60,Seconds%60);
        }
        EffectWarnings[Visible]->SetText(FText::FromString(Text));
        EffectWarnings[Visible++]->SetVisibility(ESlateVisibility::HitTestInvisible);
    }
    for (int32 I=Visible;I<EffectWarnings.Num();++I)
    { EffectWarnings[I]->SetText(FText::GetEmpty());EffectWarnings[I]->SetVisibility(ESlateVisibility::Collapsed); }
}

FText UEWSurvivalWidget::GetDisplayedSummary() const
{
    return FText::FromString(DisplayedSummary);
}
TArray<float> UEWSurvivalWidget::GetDisplayedFillFractions() const
{
    TArray<float> Result;
    for (const auto& Bar : Bars) Result.Add(Bar->GetPercent());
    return Result;
}
FText UEWSurvivalWidget::GetDisplayedWarnings() const
{
    FString Summary;
    for (const auto& Warning : Warnings) if (!Warning->GetText().IsEmpty())
    { if (!Summary.IsEmpty()) Summary+=TEXT("\n"); Summary+=Warning->GetText().ToString(); }
    for (const auto& Warning : EffectWarnings) if (!Warning->GetText().IsEmpty())
    { if (!Summary.IsEmpty()) Summary+=TEXT("\n"); Summary+=Warning->GetText().ToString(); }
    return FText::FromString(Summary);
}
