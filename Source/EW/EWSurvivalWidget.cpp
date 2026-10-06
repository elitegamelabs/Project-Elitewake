#include "EWSurvivalWidget.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"

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
    Panel->SetPadding(FMargin(10));
    Panel->SetBrushColor(FLinearColor(.015f,.025f,.035f,.88f));
    auto* PanelSlot = Canvas->AddChildToCanvas(Panel);
    PanelSlot->SetAnchors(FAnchors(0.f,1.f));
    PanelSlot->SetOffsets(FMargin(12,-524,360,300));
    auto* Content = WidgetTree->ConstructWidget<UVerticalBox>();
    Panel->SetContent(Content);
    for (int32 i=0;i<5;++i)
    {
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
        auto Font = Label->GetFont(); Font.Size=22; Label->SetFont(Font);
        Content->AddChildToVerticalBox(Label);
        auto* Bar = WidgetTree->ConstructWidget<UProgressBar>();
        auto Style=Bar->GetWidgetStyle();
        Style.BackgroundImage.TintColor=FSlateColor(FLinearColor(.08f,.1f,.12f));
        Bar->SetWidgetStyle(Style);
        Content->AddChildToVerticalBox(Bar)->SetPadding(FMargin(0,2,0,8));
        Labels.Add(Label); Bars.Add(Bar);
    }
    auto* Notices = WidgetTree->ConstructWidget<UVerticalBox>();
    auto* NoticeSlot = Canvas->AddChildToCanvas(Notices);
    NoticeSlot->SetAnchors(FAnchors(.2f,0.f,.8f,0.f));
    NoticeSlot->SetOffsets(FMargin(0,16,0,160));
    for (int32 i=0;i<3;++i)
    {
        auto* Warning = WidgetTree->ConstructWidget<UTextBlock>();
        auto Font=Warning->GetFont(); Font.Size=26; Warning->SetFont(Font);
        Warning->SetJustification(ETextJustify::Center);
        Warning->SetAutoWrapText(true);
        Notices->AddChildToVerticalBox(Warning);
        Warnings.Add(Warning);
    }
}

void UEWSurvivalWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry,DeltaTime);
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
        for (const auto& Label : Labels) Label->SetText(FText::GetEmpty());
        for (const auto& Warning : Warnings) Warning->SetText(FText::GetEmpty());
        return;
    }
    BlinkTime+=DeltaTime;
    const float Values[]={Survival->GetHealth(),Survival->GetStamina(),Survival->GetHunger(),Survival->GetHydration(),Survival->GetCarriedWeight()};
    const float Maxima[]={Survival->GetMaxHealth(),Survival->GetMaxStamina(),100.f,100.f,Survival->GetMaxCarryWeight()};
    const TCHAR* Names[]={TEXT("Health"),TEXT("Stamina"),TEXT("Food"),TEXT("Hydration"),TEXT("Weight")};
    const FLinearColor Colors[]={FLinearColor(.85f,.2f,.2f),FLinearColor::White,FLinearColor(.3f,.8f,.35f),FLinearColor(.2f,.65f,1.f),FLinearColor(.6f,.75f,.85f)};
    for (int32 i=0;i<5;++i)
    {
        FString Text;
        if (i==2 || i==3) Text=FString::Printf(TEXT("%s %.0f%%"),Names[i],Values[i]);
        else if (i==4) Text=FString::Printf(TEXT("Weight %.1f / %.1f kg"),Values[i],Maxima[i]);
        else Text=FString::Printf(TEXT("%s %.0f / %.0f"),Names[i],Values[i],Maxima[i]);
        if (Labels[i]->GetText().ToString()!=Text) Labels[i]->SetText(FText::FromString(Text));
        Bars[i]->SetPercent(Maxima[i]>0.f ? FMath::Clamp(Values[i]/Maxima[i],0.f,1.f) : 0.f);
        Bars[i]->SetFillColorAndOpacity(Colors[i]);
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
        Warnings[i]->SetText(WarningRemaining[i]>0.f ? FText::FromString(Messages[i]) : FText::GetEmpty());
        Warnings[i]->SetColorAndOpacity(FSlateColor(WarningColors[i]));
        const bool bBright=bEmpty && FMath::Fmod(BlinkTime,1.f)<.5f;
        auto Style=Bars[Stat]->GetWidgetStyle();
        const FSlateColor Tint(bBright ? WarningColors[i] : FLinearColor(.08f,.1f,.12f));
        if (Style.BackgroundImage.TintColor!=Tint)
        {
            Style.BackgroundImage.TintColor=Tint;
            Bars[Stat]->SetWidgetStyle(Style);
        }
        Labels[Stat]->SetColorAndOpacity(FSlateColor(bEmpty ? WarningColors[i] : FLinearColor::White));
    }
}

FText UEWSurvivalWidget::GetDisplayedSummary() const
{
    FString Summary;
    for (const auto& Label : Labels) { if (!Summary.IsEmpty()) Summary+=TEXT("\n"); Summary+=Label->GetText().ToString(); }
    return FText::FromString(Summary);
}
FText UEWSurvivalWidget::GetDisplayedWarnings() const
{
    FString Summary;
    for (const auto& Warning : Warnings) if (!Warning->GetText().IsEmpty())
    { if (!Summary.IsEmpty()) Summary+=TEXT("\n"); Summary+=Warning->GetText().ToString(); }
    return FText::FromString(Summary);
}
