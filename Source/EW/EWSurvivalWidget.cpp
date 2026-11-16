#include "EWSurvivalWidget.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
#include "EWWalletComponent.h"
#include "EWHudIcon.h"
#include "GameFramework/GameStateBase.h"
#include "Components/SizeBox.h"
#include "Components/Image.h"
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
#include "World/EWClimateRegion.h"
#include "World/EWSafeZone.h"
#include "EWDiscoveryComponent.h"
#include "EWColourVision.h"
#include "EWEquipmentComponent.h"
#include "World/EWNorth.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "EWPlayerController.h"

namespace
{
    /** Painted status art, in HUD order. A missing texture falls back to the generated icon. */
    const TCHAR* const StatArt[]={
        TEXT("/Game/Elitewake/UI/HUD/T_Health_Matte_v2.T_Health_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Stamina_Matte_v2.T_Stamina_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Hunger_Matte_v2.T_Hunger_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Hydration_Matte_v2.T_Hydration_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Weight_Matte_v2.T_Weight_Matte_v2")};

    /** Empty space under and over the painted icon in its texture (fraction of the height), so the fill runs over the icon
        itself: a small loss of health then shows, and an empty stat shows nothing. Health, stamina, food, hydration, weight. */
    const float ArtBottom[]={.110f,.061f,.147f,.038f,.065f};
    const float ArtTop[]={.135f,.066f,.169f,.042f,.065f};
    const TCHAR* const MaritimeStats[] = {TEXT("Health"), TEXT("Stamina"), TEXT("Food"), TEXT("Water"), TEXT("Weight")};
    const FLinearColor Ivory = FLinearColor::FromSRGBColor(FColor(247, 232, 204));
    UTexture2D* LoadMaritimeIcon(const TCHAR* Name)
    {
        return LoadObject<UTexture2D>(nullptr, *FString::Printf(TEXT("/Game/Elitewake/UI/HUD/T_Maritime_%s.T_Maritime_%s"), Name, Name));
    }
    void SetWarningText(UTextBlock* Label, const FText& Text)
    {
        Label->SetText(Text);
        Label->GetParent()->SetVisibility(Text.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    }
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
        UTexture2D* Art=LoadMaritimeIcon(MaritimeStats[i]);
        const bool bMaritime = Art != nullptr;
        if (!Art) Art=LoadObject<UTexture2D>(nullptr,StatArt[i]);
        bHasArt[i]=Art!=nullptr;
        IconBottom[i] = bMaritime ? (i == 2 ? 15.f : 12.f) / 128.f : Art ? ArtBottom[i] : 0.f;
        IconSpan[i] = bMaritime ? (i == 2 ? 99.f : 104.f) / 128.f : Art ? 1.f - ArtBottom[i] - ArtTop[i] : 1.f;
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
        Label->SetColorAndOpacity(FSlateColor(Ivory));
        Label->SetShadowOffset(FVector2D(1,1));Label->SetShadowColorAndOpacity(FLinearColor::Black);
        Column->AddChildToVerticalBox(Label);
        Labels.Add(Label); Bars.Add(Bar);
    }
    // The right-side stack leaves the world visible and grows upward as conditions are added.
    RightPanel = WidgetTree->ConstructWidget<USizeBox>();
    RightPanel->SetWidthOverride(292.f);
    auto* RightSlot = Canvas->AddChildToCanvas(RightPanel);
    RightSlot->SetAnchors(FAnchors(1.f,1.f)); RightSlot->SetAlignment(FVector2D(1,1));
    RightSlot->SetAutoSize(true); RightSlot->SetPosition(FVector2D(-22.f,-126.f));
    auto* RightContent = WidgetTree->ConstructWidget<UVerticalBox>();
    RightPanel->SetContent(RightContent);
    NoticePanel = WidgetTree->ConstructWidget<UVerticalBox>();
    RightContent->AddChildToVerticalBox(NoticePanel)->SetPadding(FMargin(0,0,0,10));
    AirWarning = AddWarningRow(LoadMaritimeIcon(TEXT("Air")));
    for (const int32 Index : {2,3,1,4}) Warnings.Add(AddWarningRow(IconTextures[Index*2+1]));
    const auto AddEffectArt = [this](const TCHAR* Id, const TCHAR* Icon)
    {
        EffectArt.Add(FName(Id), LoadMaritimeIcon(Icon));
    };
    AddEffectArt(TEXT("Bleeding"), TEXT("Bleeding"));
    AddEffectArt(TEXT("Poison"), TEXT("Poison"));
    AddEffectArt(TEXT("Bandaging"), TEXT("Bandage"));
    AddEffectArt(TEXT("Freezing"), TEXT("Cold"));
    AddEffectArt(TEXT("Cold"), TEXT("Cold"));
    AddEffectArt(TEXT("Overheating"), TEXT("Heat"));
    AddEffectArt(TEXT("Warming"), TEXT("Heat"));
    AddEffectArt(TEXT("FoodSickness"), TEXT("FoodSickness"));

    ClimateLine = WidgetTree->ConstructWidget<UTextBlock>();
    {
        auto Font = ClimateLine->GetFont(); Font.Size = 14; ClimateLine->SetFont(Font);
        ClimateLine->SetShadowOffset(FVector2D(1,1)); ClimateLine->SetShadowColorAndOpacity(FLinearColor::Black);
        ClimateLine->SetJustification(ETextJustify::Right);
        ClimateLine->SetAutoWrapText(true);
        RightContent->AddChildToVerticalBox(ClimateLine);
    }
    // Entering a region: its name across the top, fading.
    RegionBanner = WidgetTree->ConstructWidget<UTextBlock>();
    {
        auto Font = RegionBanner->GetFont(); Font.Size = 34; Font.LetterSpacing = 400; RegionBanner->SetFont(Font);
        RegionBanner->SetJustification(ETextJustify::Center);
        RegionBanner->SetShadowOffset(FVector2D(2,2)); RegionBanner->SetShadowColorAndOpacity(FLinearColor(0,0,0,.7f));
        auto* BannerSlot = Canvas->AddChildToCanvas(RegionBanner);
        BannerSlot->SetAnchors(FAnchors(.5f,0.f)); BannerSlot->SetAlignment(FVector2D(.5f,0.f)); BannerSlot->SetAutoSize(true);
        BannerSlot->SetOffsets(FMargin(0,90,0,0));
    }
    ZoneBanner = WidgetTree->ConstructWidget<UTextBlock>();
    {
        auto Font = ZoneBanner->GetFont(); Font.Size = 18; Font.LetterSpacing = 120; ZoneBanner->SetFont(Font);
        ZoneBanner->SetJustification(ETextJustify::Center);
        ZoneBanner->SetColorAndOpacity(FSlateColor(FLinearColor(.95f, .82f, .5f)));
        ZoneBanner->SetShadowOffset(FVector2D(2,2)); ZoneBanner->SetShadowColorAndOpacity(FLinearColor(0,0,0,.7f));
        auto* ZoneSlot = Canvas->AddChildToCanvas(ZoneBanner);
        ZoneSlot->SetAnchors(FAnchors(.5f,0.f)); ZoneSlot->SetAlignment(FVector2D(.5f,0.f)); ZoneSlot->SetAutoSize(true);
        ZoneSlot->SetOffsets(FMargin(0,142,0,0));
        ZoneBanner->SetRenderOpacity(0.f);
    }
    // A new discovery (Part 8, 63): a small heading over its name, held a few seconds, then the next in turn.
    DiscoveryBanner = WidgetTree->ConstructWidget<UVerticalBox>();
    {
        DiscoveryHeading = WidgetTree->ConstructWidget<UTextBlock>();
        DiscoveryName = WidgetTree->ConstructWidget<UTextBlock>();
        for (UTextBlock* Line : {DiscoveryHeading.Get(), DiscoveryName.Get()})
        {
            const bool bHeading = Line == DiscoveryHeading;
            auto Font = Line->GetFont(); Font.Size = bHeading ? 16 : 30; Font.LetterSpacing = bHeading ? 300 : 80; Line->SetFont(Font);
            Line->SetJustification(ETextJustify::Center);
            Line->SetColorAndOpacity(FSlateColor(bHeading ? FLinearColor(.95f, .82f, .5f) : FLinearColor(1.f, .97f, .9f)));
            Line->SetShadowOffset(FVector2D(2,2)); Line->SetShadowColorAndOpacity(FLinearColor(0,0,0,.75f));
            DiscoveryBanner->AddChildToVerticalBox(Line)->SetHorizontalAlignment(HAlign_Center);
        }
        auto* DiscoverySlot = Canvas->AddChildToCanvas(DiscoveryBanner);
        DiscoverySlot->SetAnchors(FAnchors(.5f,0.f)); DiscoverySlot->SetAlignment(FVector2D(.5f,0.f)); DiscoverySlot->SetAutoSize(true);
        DiscoverySlot->SetOffsets(FMargin(0,190,0,0));
        DiscoveryBanner->SetRenderOpacity(0.f);
    }
}

UTextBlock* UEWSurvivalWidget::AddWarningRow(UTexture2D* Texture, UImage** OutIcon)
{
    auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
    auto* RowSlot = NoticePanel->AddChildToVerticalBox(Row);
    RowSlot->SetHorizontalAlignment(HAlign_Right);
    RowSlot->SetPadding(FMargin(0,2));
    auto* Warning = WidgetTree->ConstructWidget<UTextBlock>();
    auto Font = Warning->GetFont(); Font.Size = 15; Warning->SetFont(Font);
    Warning->SetJustification(ETextJustify::Right);
    Warning->SetWrapTextAt(246.f);
    Warning->SetShadowOffset(FVector2D(1,1));
    Warning->SetShadowColorAndOpacity(FLinearColor::Black);
    Warning->SetColorAndOpacity(FSlateColor(Ivory));
    Row->AddChildToHorizontalBox(Warning)->SetVerticalAlignment(VAlign_Center);
    auto* Size = WidgetTree->ConstructWidget<USizeBox>();
    Size->SetWidthOverride(31.f); Size->SetHeightOverride(31.f);
    auto* IconSlot = Row->AddChildToHorizontalBox(Size);
    IconSlot->SetPadding(FMargin(5,0,0,0));
    IconSlot->SetVerticalAlignment(VAlign_Center);
    auto* Icon = WidgetTree->ConstructWidget<UImage>();
    Size->SetContent(Icon);
    if (Texture) Icon->SetBrushFromTexture(Texture);
    Icon->SetVisibility(Texture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
    if (OutIcon) *OutIcon = Icon;
    Row->SetVisibility(ESlateVisibility::Collapsed);
    return Warning;
}

void UEWSurvivalWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry,DeltaTime);
    const float Dpi=UWidgetLayoutLibrary::GetViewportScale(this);
    const float ReadableScale=FMath::Max(1.f,.8f/FMath::Max(Dpi,.01f));
    Panel->SetRenderTransformPivot(FVector2D(0,1));Panel->SetRenderScale(FVector2D(ReadableScale));
    RightPanel->SetRenderTransformPivot(FVector2D(1,1));RightPanel->SetRenderScale(FVector2D(ReadableScale));
    // On narrow screens put the side HUD above the centered hotbar instead of covering slots.
    const bool Stack=Geometry.GetLocalSize().X*.5f-304.f*ReadableScale < 18.f+320.f*ReadableScale+12.f;
    const float Lift=Stack ? 92.f*ReadableScale+14.f : 0.f;
    CastChecked<UCanvasPanelSlot>(Panel->Slot)->SetOffsets(FMargin(18,-122-Lift,320,104));
    CastChecked<UCanvasPanelSlot>(RightPanel->Slot)->SetPosition(FVector2D(-22.f,-126.f-Lift));

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
    RightPanel->SetVisibility(Survival ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (!Survival)
    {
        DisplayedSummary.Reset();
        for (const auto& Label : Labels) Label->SetText(FText::GetEmpty());
        SetWarningText(AirWarning, FText::GetEmpty());
        for (const auto& Warning : Warnings) SetWarningText(Warning, FText::GetEmpty());
        for (const auto& Warning : EffectWarnings) SetWarningText(Warning, FText::GetEmpty());
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
        const float Level=Maxima[i]>0.f ? FMath::Clamp(Values[i]/Maxima[i],0.f,1.f) : 0.f;
        Bars[i]->SetPercent(IconBottom[i]+Level*IconSpan[i]);
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
        SetWarningText(Warnings[i], (i<2 ? bEmpty : WarningRemaining[i]>0.f) ? FText::FromString(Messages[i]) : FText::GetEmpty());
        Warnings[i]->SetColorAndOpacity(FSlateColor(WarningColors[i]));
        Labels[Stat]->SetColorAndOpacity(FSlateColor(bEmpty ? WarningColors[i] : FLinearColor::White));

    }
    {
        const FEWClimate C = Survival->GetClimate();
        const float Body = Survival->GetBodyTemperature();
        const bool bRegionIsHumid = C.Region == EEWRegion::Desert || C.Region == EEWRegion::Jungle || C.Region == EEWRegion::Swamp;
        const bool bSwimming = Pawn->GetCharacterMovement() && Pawn->GetCharacterMovement()->IsSwimming();
        FString Line = FString::Printf(TEXT("%s\n%s %.0f°C"), *AEWClimateRegion::RegionName(C.Region).ToString().ToUpper(),
            bSwimming ? TEXT("Water") : TEXT("Air"), Survival->GetFeltTemperature());
        if (bRegionIsHumid || C.Humidity >= 70.f) Line += FString::Printf(TEXT("\nHumidity %.0f%%"), C.Humidity);
        Line += FString::Printf(TEXT("\nBody %.1f°C"), Body);
        if (const AEWCharacter* Me = Cast<AEWCharacter>(GetOwningPlayerPawn()))
            if (const UEWWalletComponent* Purse = Me->GetWalletComponent()) Line += FString::Printf(TEXT("\nPurse %s"), *UEWWalletComponent::FormatShort(Purse->GetCopper()));
        // A sextant in hand reads the latitude (Part 8, 09); not under water, where there is no horizon.
        DisplayedLatitude.Reset();
        if (const AEWCharacter* Me = Cast<AEWCharacter>(GetOwningPlayerPawn()))
            if (const UEWEquipmentComponent* Worn = Me->GetEquipmentComponent())
                if (const UEWItemDefinition* Held = Worn->GetEquippedItem(EEWEquipmentSlot::MainHand); Held && Held->bSextant)
                {
                    const bool bUnder = Me->GetCharacterMovement() && Me->GetCharacterMovement()->IsSwimming()
                        && Me->GetActorLocation().Z < -150.f;
                    DisplayedLatitude = bUnder ? FString(TEXT("no horizon")) : EWNorth::FormatLatitude(EWNorth::LatitudeAt(Me->GetActorLocation()));
                    Line += FString::Printf(TEXT("\nSextant %s"), *DisplayedLatitude);
                }
        ClimateLine->SetText(FText::FromString(Line));
        // Blue as the body cools, white when comfortable, orange as it heats.
        const FLinearColor Cold = EWCue::Cold(), Hot = EWCue::Hot();
        const float Off = Body - UEWSurvivalComponent::NormalBody;
        ClimateLine->SetColorAndOpacity(FSlateColor(Off < -.3f ? FMath::Lerp(FLinearColor::White, Cold, FMath::Clamp(-Off / 2.f, 0.f, 1.f))
            : Off > .3f ? FMath::Lerp(Ivory, Hot, FMath::Clamp(Off / 2.f, 0.f, 1.f)) : Ivory));
        if (ShownRegion != int32(C.Region))
        {
            // The first reading names where the survivor is, too.
            ShownRegion = int32(C.Region);
            BannerSeconds = 4.f;
            RegionBanner->SetText(AEWClimateRegion::RegionName(C.Region));
        }
        BannerSeconds = FMath::Max(0.f, BannerSeconds - DeltaTime);
        RegionBanner->SetRenderOpacity(FMath::Clamp(BannerSeconds / 1.2f, 0.f, 1.f));
        // A free port's bounds, checked twice a second: announced on the way in and on the way out.
        if ((ZoneCheck -= DeltaTime) <= 0.f)
        {
            ZoneCheck = .5f;
            const APawn* Me = GetOwningPlayerPawn();
            const AEWSafeZone* Zone = Me ? AEWSafeZone::FindAt(this, Me->GetActorLocation()) : nullptr;
            const FString Name = Zone ? Zone->ZoneName.ToString() : FString();
            if (Me && (!bZoneKnown || Name != ShownZone))
            {
                if (Zone)
                {
                    TArray<FString> Rules;
                    if (Zone->bNoPvP) Rules.Add(TEXT("no fighting"));
                    if (Zone->bNoBuilding) Rules.Add(TEXT("no building"));
                    if (Zone->bNoHostiles) Rules.Add(TEXT("no beasts"));
                    ZoneBanner->SetText(FText::Format(NSLOCTEXT("Elitewake", "ZoneEnter", "{0}  ·  a free port: {1}"), Zone->ZoneName,
                        FText::FromString(FString::Join(Rules, TEXT(", ")))));
                    ZoneSeconds = 6.f;
                }
                else if (bZoneKnown)
                {
                    ZoneBanner->SetText(FText::Format(NSLOCTEXT("Elitewake", "ZoneLeave", "Leaving {0}  ·  the open sea's rules"), FText::FromString(ShownZone)));
                    ZoneSeconds = 4.f;
                }
                ShownZone = Name;
                bZoneKnown = true;
            }
        }
        ZoneSeconds = FMath::Max(0.f, ZoneSeconds - DeltaTime);
        ZoneBanner->SetRenderOpacity(FMath::Clamp(ZoneSeconds / 1.2f, 0.f, 1.f));
    }
    {
        DiscoverySeconds = FMath::Max(0.f, DiscoverySeconds - DeltaTime);
        const auto* PC = Cast<AEWPlayerController>(GetOwningPlayer());
        if (UEWDiscoveryComponent* Found = PC ? PC->GetDiscoveries() : nullptr)
        {
            FEWDiscovery Next;
            // The next one waits until this one has had its moment.
            if (DiscoverySeconds <= 1.f && Found->PopAnnouncement(Next))
            {
                DiscoverySeconds = 5.f;
                const FText Kind = Next.Kind == EEWPlaceKind::Creature ? NSLOCTEXT("Elitewake", "NewCreature", "NEW CREATURE")
                    : NSLOCTEXT("Elitewake", "Discovered", "DISCOVERED");
                DiscoveryHeading->SetText(Kind);
                DiscoveryName->SetText(Next.Name);
            }
        }
        DiscoveryBanner->SetRenderOpacity(FMath::Clamp(DiscoverySeconds / 1.2f, 0.f, 1.f));
    }
    const bool Overweight=Survival->GetCarriedWeight()>Survival->GetMaxCarryWeight();
    SetWarningText(Warnings[3], Overweight ? FText::FromString(TEXT("Over encumbered")) : FText::GetEmpty());
    Warnings[3]->SetColorAndOpacity(FSlateColor(FLinearColor(1.f,.65f,.2f)));
    const float Air = Survival->GetBreathSeconds();
    FText AirText;
    if (Survival->IsUnderwater())
    {
        const int32 Seconds = FMath::CeilToInt(Air);
        if (Air <= 0.f) AirText = FText::FromString(TEXT("Out of air — surface now"));
        else if (Air <= UEWSurvivalComponent::LowBreathSeconds)
            AirText = FText::FromString(FString::Printf(TEXT("Low air — surface now (%ds)"), Seconds));
        else AirText = FText::FromString(FString::Printf(TEXT("Air %ds"), Seconds));
    }
    SetWarningText(AirWarning, AirText);
    AirWarning->SetColorAndOpacity(FSlateColor(Air <= UEWSurvivalComponent::LowBreathSeconds ? EWCue::Cold() : Ivory));
    const auto Effects=Survival->GetDebuffNotices();
    const auto* GameState=GetWorld()->GetGameState();
    const double Now=GameState ? GameState->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
    int32 Visible=0;
    for (const auto& Effect : Effects)
    {
        if (Effect.ExpiresAt>=0. && Effect.ExpiresAt<=Now) continue;
        if (Visible==EffectWarnings.Num())
        {
            UImage* Icon = nullptr;
            EffectWarnings.Add(AddWarningRow(nullptr, &Icon));
            EffectIcons.Add(Icon);
        }
        FString Text=Effect.Label.ToString();
        if (Effect.ExpiresAt>=0.)
        {
            const int32 Seconds=FMath::CeilToInt(Effect.ExpiresAt-Now);
            Text+=FString::Printf(TEXT(" %02d:%02d"),Seconds/60,Seconds%60);
        }
        UTexture2D* Texture = EffectArt.FindRef(Effect.Id);
        UImage* Icon = EffectIcons[Visible];
        if (Icon->GetBrush().GetResourceObject() != Texture) Icon->SetBrushFromTexture(Texture);
        Icon->SetVisibility(Texture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
        SetWarningText(EffectWarnings[Visible++], FText::FromString(Text));
    }
    for (int32 I=Visible;I<EffectWarnings.Num();++I)
        SetWarningText(EffectWarnings[I], FText::GetEmpty());
}

FText UEWSurvivalWidget::GetDisplayedClimate() const
{
    return ClimateLine ? ClimateLine->GetText() : FText::GetEmpty();
}
FText UEWSurvivalWidget::GetDisplayedDiscovery() const
{
    return DiscoveryName && DiscoverySeconds > 0.f ? DiscoveryName->GetText() : FText::GetEmpty();
}
FText UEWSurvivalWidget::GetDisplayedZoneBanner() const
{
    return ZoneBanner && ZoneSeconds > 0.f ? ZoneBanner->GetText() : FText::GetEmpty();
}

FText UEWSurvivalWidget::GetDisplayedRegionBanner() const
{
    return RegionBanner && BannerSeconds > 0.f ? RegionBanner->GetText() : FText::GetEmpty();
}
FText UEWSurvivalWidget::GetDisplayedSummary() const
{
    return FText::FromString(DisplayedSummary);
}
TArray<float> UEWSurvivalWidget::GetDisplayedFillFractions() const
{
    TArray<float> Result;
    for (int32 i=0;i<Bars.Num();++i)
    {
        Result.Add(FMath::Clamp((Bars[i]->GetPercent()-IconBottom[i])/IconSpan[i],0.f,1.f));
    }
    return Result;
}
FText UEWSurvivalWidget::GetDisplayedWarnings() const
{
    FString Summary = AirWarning ? AirWarning->GetText().ToString() : FString();
    for (const auto& Warning : Warnings) if (!Warning->GetText().IsEmpty())
    { if (!Summary.IsEmpty()) Summary+=TEXT("\n"); Summary+=Warning->GetText().ToString(); }
    for (const auto& Warning : EffectWarnings) if (!Warning->GetText().IsEmpty())
    { if (!Summary.IsEmpty()) Summary+=TEXT("\n"); Summary+=Warning->GetText().ToString(); }
    return FText::FromString(Summary);
}
