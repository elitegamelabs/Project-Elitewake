#include "EWMapWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "Components/ScaleBox.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "World/EWClimateRegion.h"

namespace
{
    constexpr float MinMapViewWidth = 2500.f;
    // The five regions span roughly 200 km from the outer Winter/Swamp shores to Desert/Jungle.
    // Keep the overview wide enough to fit every island; zoom-in still clamps to this map's overview.
    constexpr float MaxMapViewWidth = 40000000.f;
    constexpr float MapCaptureHeight = 400000.f;
}

TSharedRef<SWidget> UEWMapWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Panel = WidgetTree->ConstructWidget<UBorder>();
        Panel->SetBrushColor(FLinearColor(.015f, .025f, .035f, .97f));
        Panel->SetPadding(FMargin(28));
        WidgetTree->RootWidget = Panel;

        auto* Content = WidgetTree->ConstructWidget<UVerticalBox>();
        Panel->SetContent(Content);

        RegionTitle = WidgetTree->ConstructWidget<UTextBlock>();
        RegionTitle->SetText(NSLOCTEXT("Elitewake", "MapTitle", "WORLD MAP"));
        auto Font = RegionTitle->GetFont();
        Font.Size = 26;
        RegionTitle->SetFont(Font);
        Content->AddChildToVerticalBox(RegionTitle);

        Heading = WidgetTree->ConstructWidget<UTextBlock>();
        Font.Size = 16;
        Heading->SetFont(Font);
        Content->AddChildToVerticalBox(Heading);

        auto* Scale = WidgetTree->ConstructWidget<UScaleBox>();
        Scale->SetStretch(EStretch::ScaleToFit);
        auto* Overlay = WidgetTree->ConstructWidget<UOverlay>();
        Scale->SetContent(Overlay);

        MapImage = WidgetTree->ConstructWidget<UImage>();
        Overlay->AddChildToOverlay(MapImage);
        MapCanvas = WidgetTree->ConstructWidget<UCanvasPanel>();
        Overlay->AddChildToOverlay(MapCanvas);

        PlayerMarker = WidgetTree->ConstructWidget<UTextBlock>();
        PlayerMarker->SetText(FText::FromString(TEXT("▲")));
        Font.Size = 28;
        PlayerMarker->SetFont(Font);
        PlayerMarker->SetColorAndOpacity(FLinearColor(.1f, .85f, 1.f));
        PlayerMarkerSlot = MapCanvas->AddChildToCanvas(PlayerMarker);
        PlayerMarkerSlot->SetAlignment(FVector2D(.5f, .5f));
        PlayerMarkerSlot->SetAutoSize(true);

        Content->AddChildToVerticalBox(Scale)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

        MapHint = WidgetTree->ConstructWidget<UTextBlock>();
        MapHint->SetText(NSLOCTEXT("Elitewake", "MapHint", "M: Close map  |  Drag: pan  |  Wheel / triggers: zoom  |  Right stick: pan"));
        MapHint->SetFont(Font);
        Content->AddChildToVerticalBox(MapHint);
    }
    return Super::RebuildWidget();
}

void UEWMapWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::Visible);
    if (!GetOwningPlayer() || !GetOwningPlayer()->IsLocalController() || !GetWorld()) return;

    RenderTarget = NewObject<UTextureRenderTarget2D>(this);
    RenderTarget->RenderTargetFormat = RTF_RGBA8;
    RenderTarget->InitAutoFormat(1024, 1024);
    RenderTarget->UpdateResourceImmediate(true);

    FActorSpawnParameters Params;
    Params.Owner = GetOwningPlayer();
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    Capture = GetWorld()->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), FVector::ZeroVector, FRotator(-90, 0, 0), Params);
    if (!Capture) return;

    Capture->SetReplicates(false);
    auto* Camera = Capture->GetCaptureComponent2D();
    Camera->TextureTarget = RenderTarget;
    Camera->ProjectionType = ECameraProjectionMode::Orthographic;
    Camera->OrthoWidth = CurrentViewWidth;
    Camera->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
    Camera->bCaptureEveryFrame = false;
    Camera->bCaptureOnMovement = false;
    Camera->ShowFlags.SetAtmosphere(false);
    Camera->ShowFlags.SetFog(false);

    FSlateBrush Brush;
    Brush.DrawAs = ESlateBrushDrawType::Image;
    Brush.SetResourceObject(RenderTarget);
    Brush.ImageSize = FVector2D(1024, 1024);
    MapImage->SetBrush(Brush);

    InitializeWorldOverview();
    CaptureRemaining = 0.f;
}

void UEWMapWidget::InitializeWorldOverview()
{
    if (!GetWorld() || bHasInitializedView) return;

    FVector2D Min(TNumericLimits<float>::Max(), TNumericLimits<float>::Max());
    FVector2D Max(TNumericLimits<float>::Lowest(), TNumericLimits<float>::Lowest());
    bool bFoundRegion = false;

    for (TActorIterator<AEWClimateRegion> It(GetWorld()); It; ++It)
    {
        const FVector Location = It->GetActorLocation();
        const FVector2D Radii = It->Radii;
        Min.X = FMath::Min(Min.X, Location.X - Radii.X);
        Min.Y = FMath::Min(Min.Y, Location.Y - Radii.Y);
        Max.X = FMath::Max(Max.X, Location.X + Radii.X);
        Max.Y = FMath::Max(Max.Y, Location.Y + Radii.Y);
        bFoundRegion = true;
    }

    if (bFoundRegion)
    {
        MapCenter = FVector((Min.X + Max.X) * .5f, (Min.Y + Max.Y) * .5f, 0.f);
        OverviewViewWidth = FMath::Max(Max.X - Min.X, Max.Y - Min.Y) * 1.12f;
    }
    else if (const APawn* Pawn = GetOwningPlayerPawn())
    {
        MapCenter = Pawn->GetActorLocation();
        OverviewViewWidth = 60000.f;
    }

    OverviewViewWidth = FMath::Clamp(OverviewViewWidth, MinMapViewWidth, MaxMapViewWidth);
    CurrentViewWidth = TargetViewWidth = OverviewViewWidth;
    bHasInitializedView = true;
}

void UEWMapWidget::AdjustZoom(float Direction)
{
    if (FMath::IsNearlyZero(Direction)) return;
    TargetViewWidth = FMath::Clamp(TargetViewWidth * FMath::Exp(-Direction * .28f), MinMapViewWidth, OverviewViewWidth);
}

void UEWMapWidget::PanByScreenDelta(const FVector2D& Delta)
{
    if (!MapImage) return;
    const FVector2D Size = MapImage->GetCachedGeometry().GetLocalSize();
    if (Size.X <= 1.f || Size.Y <= 1.f) return;

    MapCenter.X -= (Delta.X / Size.X) * CurrentViewWidth;
    MapCenter.Y += (Delta.Y / Size.Y) * CurrentViewWidth;
}

bool UEWMapWidget::IsPointerOverMap(const FVector2D& ScreenPosition) const
{
    return MapImage && MapImage->GetCachedGeometry().IsUnderLocation(ScreenPosition);
}

FReply UEWMapWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() == EKeys::LeftMouseButton && IsPointerOverMap(Event.GetScreenSpacePosition()))
    {
        bMousePanning = true;
        LastMousePosition = Event.GetScreenSpacePosition();
        return FReply::Handled().CaptureMouse(TakeWidget());
    }
    return Super::NativeOnMouseButtonDown(Geometry, Event);
}

FReply UEWMapWidget::NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (bMousePanning && Event.GetEffectingButton() == EKeys::LeftMouseButton)
    {
        bMousePanning = false;
        return FReply::Handled().ReleaseMouseCapture();
    }
    return Super::NativeOnMouseButtonUp(Geometry, Event);
}

FReply UEWMapWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (bMousePanning)
    {
        const FVector2D Position = Event.GetScreenSpacePosition();
        PanByScreenDelta(Position - LastMousePosition);
        LastMousePosition = Position;
        return FReply::Handled();
    }
    return Super::NativeOnMouseMove(Geometry, Event);
}

FReply UEWMapWidget::NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (IsPointerOverMap(Event.GetScreenSpacePosition()))
    {
        AdjustZoom(Event.GetWheelDelta());
        return FReply::Handled();
    }
    return Super::NativeOnMouseWheel(Geometry, Event);
}

void UEWMapWidget::PositionPlayerMarker(const APawn* Pawn)
{
    if (!Pawn || !MapImage || !PlayerMarkerSlot) return;
    const FVector2D Size = MapImage->GetCachedGeometry().GetLocalSize();
    if (Size.X <= 1.f || Size.Y <= 1.f) return;

    const FVector Location = Pawn->GetActorLocation();
    const float HalfWidth = CurrentViewWidth * .5f;
    const float X = FMath::Clamp(((Location.X - MapCenter.X) / CurrentViewWidth + .5f) * Size.X, 12.f, Size.X - 12.f);
    const float Y = FMath::Clamp((.5f - (Location.Y - MapCenter.Y) / CurrentViewWidth) * Size.Y, 12.f, Size.Y - 12.f);
    PlayerMarkerSlot->SetPosition(FVector2D(X, Y));
    PlayerMarker->SetRenderTransformAngle(Pawn->GetActorRotation().Yaw);
}

void UEWMapWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    const APawn* Pawn = GetOwningPlayerPawn();
    if (!Pawn || !Capture || !GetOwningPlayer()) return;

    if (!ControllerPanInput.IsNearlyZero())
    {
        const FVector2D Normalized = ControllerPanInput.GetClampedToMaxSize(1.f);
        MapCenter.X += Normalized.X * CurrentViewWidth * .72f * DeltaSeconds;
        MapCenter.Y += Normalized.Y * CurrentViewWidth * .72f * DeltaSeconds;
    }
    if (!FMath::IsNearlyZero(ControllerZoomInput)) AdjustZoom(ControllerZoomInput * DeltaSeconds * 3.f);

    CurrentViewWidth = FMath::FInterpTo(CurrentViewWidth, TargetViewWidth, DeltaSeconds, 8.f);
    if (auto* Camera = Capture->GetCaptureComponent2D()) Camera->OrthoWidth = CurrentViewWidth;

    const FEWClimate Sample = AEWClimateRegion::SampleClimate(GetWorld(), Pawn->GetActorLocation());
    RegionTitle->SetText(AEWClimateRegion::RegionName(Sample.Region));
    Heading->SetText(FText::Format(NSLOCTEXT("Elitewake", "MapHeading", "Current region  |  Facing {0}°"),
        FText::AsNumber(FMath::RoundToInt(FMath::Fmod(Pawn->GetActorRotation().Yaw + 360.f, 360.f)))));
    PositionPlayerMarker(Pawn);

    CaptureRemaining -= DeltaSeconds;
    if (CaptureRemaining > 0.f) return;
    CaptureRemaining = .5f;
    Capture->SetActorLocation(MapCenter + FVector(0, 0, MapCaptureHeight));
    Capture->GetCaptureComponent2D()->CaptureScene();
}

void UEWMapWidget::NativeDestruct()
{
    if (Capture) Capture->Destroy();
    Capture = nullptr;
    RenderTarget = nullptr;
    Super::NativeDestruct();
}

bool UEWMapWidget::HasMapCapture() const
{
    return Capture && RenderTarget && MapImage;
}

FText UEWMapWidget::GetRegionTitle() const
{
    return RegionTitle ? RegionTitle->GetText() : FText::GetEmpty();
}

FText UEWMapWidget::GetHeadingText() const
{
    return Heading ? Heading->GetText() : FText::GetEmpty();
}

FText UEWMapWidget::GetMapHintText() const
{
    return MapHint ? MapHint->GetText() : FText::GetEmpty();
}
