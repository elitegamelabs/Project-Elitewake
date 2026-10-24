#include "EWMapWidget.h"

#include "EWExplorationComponent.h"
#include "EWPlayerController.h"
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
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "World/EWClimateRegion.h"

namespace
{
    constexpr float MinMapViewWidth = 2500.f;
    // Keep the overview wide enough to fit every island; zoom-in still clamps to this map's overview.
    constexpr float MaxMapViewWidth = 40000000.f;
    // A top-down scene capture draws nothing past about 2.5 km from the camera, and the sea floor lies 1.5 km under the sea: 600 m up sees both.
    constexpr float MapCaptureHeight = 60000.f;
}

UEWExplorationComponent* UEWMapWidget::GetExploration() const
{
    const auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    return Controller ? Controller->GetExploration() : nullptr;
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
        FogImage = WidgetTree->ConstructWidget<UImage>();
        FogImage->SetVisibility(ESlateVisibility::HitTestInvisible);
        Overlay->AddChildToOverlay(FogImage);
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

        // The top of the map is the world's +X, which the compass calls north.
        NorthLabel = WidgetTree->ConstructWidget<UTextBlock>();
        NorthLabel->SetText(NSLOCTEXT("Elitewake", "MapNorth", "N"));
        NorthLabel->SetColorAndOpacity(FLinearColor(.95f, .9f, .7f));
        { auto F = NorthLabel->GetFont(); F.Size = 22; F.TypefaceFontName = FName("Bold"); NorthLabel->SetFont(F); }
        NorthLabel->SetShadowOffset(FVector2D(1.5f, 1.5f)); NorthLabel->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, .9f));
        auto* NorthSlot = MapCanvas->AddChildToCanvas(NorthLabel);
        NorthSlot->SetAnchors(FAnchors(.5f, 0.f)); NorthSlot->SetAlignment(FVector2D(.5f, 0.f)); NorthSlot->SetAutoSize(true); NorthSlot->SetPosition(FVector2D(0.f, 6.f));

        // A scale bar in the lower left corner of the picture.
        ScaleBar = WidgetTree->ConstructWidget<UBorder>();
        ScaleBar->SetBrushColor(FLinearColor(.95f, .9f, .75f, .95f));
        ScaleBarSlot = MapCanvas->AddChildToCanvas(ScaleBar);
        ScaleBarSlot->SetAnchors(FAnchors(0.f, 1.f)); ScaleBarSlot->SetAlignment(FVector2D(0.f, 1.f)); ScaleBarSlot->SetAutoSize(false);
        ScaleBarSlot->SetPosition(FVector2D(18.f, -18.f)); ScaleBarSlot->SetSize(FVector2D(120.f, 5.f));
        ScaleLabel = WidgetTree->ConstructWidget<UTextBlock>();
        ScaleLabel->SetColorAndOpacity(FLinearColor(.95f, .9f, .75f));
        { auto F = ScaleLabel->GetFont(); F.Size = 16; ScaleLabel->SetFont(F); }
        ScaleLabel->SetShadowOffset(FVector2D(1.5f, 1.5f)); ScaleLabel->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, .9f));
        auto* ScaleLabelSlot = MapCanvas->AddChildToCanvas(ScaleLabel);
        ScaleLabelSlot->SetAnchors(FAnchors(0.f, 1.f)); ScaleLabelSlot->SetAlignment(FVector2D(0.f, 1.f)); ScaleLabelSlot->SetAutoSize(true); ScaleLabelSlot->SetPosition(FVector2D(18.f, -30.f));

        Content->AddChildToVerticalBox(Scale)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

        MapHint = WidgetTree->ConstructWidget<UTextBlock>();
        MapHint->SetText(NSLOCTEXT("Elitewake", "MapHint", "M / Esc / Start: close  |  Drag / right stick: pan  |  Wheel / triggers: zoom"));
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
    // The world's own colours, without light or shadow: a single captured frame has no time to settle an exposure, so the lit picture came out black.
    Camera->CaptureSource = ESceneCaptureSource::SCS_BaseColor;
    Camera->bCaptureEveryFrame = false;
    Camera->bCaptureOnMovement = false;
    Camera->ShowFlags.SetAtmosphere(false);
    Camera->ShowFlags.SetFog(false);

    // The capture's alpha is 0, which an image would draw as nothing: a UI material shows its colour at full opacity.
    FSlateBrush Brush;
    Brush.DrawAs = ESlateBrushDrawType::Image;
    Brush.ImageSize = FVector2D(1024, 1024);
    if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Elitewake/UI/Map/M_MapCapture_v1.M_MapCapture_v1")))
    {
        MapMaterial = UMaterialInstanceDynamic::Create(Base, this);
        MapMaterial->SetTextureParameterValue(TEXT("Map"), RenderTarget);
        Brush.SetResourceObject(MapMaterial);
    }
    else Brush.SetResourceObject(RenderTarget);
    MapImage->SetBrush(Brush);

    // The mist: a texture redrawn from what the survivor has seen. Its edge texels clamp, so past the world the mist simply goes on.
    FogTexture = UTexture2D::CreateTransient(FogSize, FogSize, PF_B8G8R8A8);
    FogTexture->SRGB = true;
    FogTexture->Filter = TF_Bilinear;
    FogTexture->AddressX = TA_Clamp; FogTexture->AddressY = TA_Clamp;
    FogTexture->NeverStream = true;
    FogTexture->UpdateResource();
    FSlateBrush FogBrush;
    FogBrush.DrawAs = ESlateBrushDrawType::Image;
    FogBrush.ImageSize = FVector2D(1024, 1024);
    FogBrush.SetResourceObject(FogTexture);
    FogImage->SetBrush(FogBrush);

    InitializeWorldOverview();
    CaptureRemaining = 0.f;
    FogClock = 10.f;
    FogRevisionDrawn = -1;
}

void UEWMapWidget::InitializeWorldOverview()
{
    if (!GetWorld() || bHasInitializedView) return;

    if (UEWExplorationComponent* Exploration = GetExploration())
    {
        // The map and its mist cover the same square.
        Exploration->EnsureBounds();
        const FVector2D Min = Exploration->GetBoundsMin();
        const float Size = Exploration->GetBoundsSize();
        MapCenter = FVector(Min.X + Size * .5f, Min.Y + Size * .5f, 0.f);
        OverviewViewWidth = Size;
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

    // Dragging the picture right shows more of what lies to the left: -Y; dragging it down shows what lies above: +X.
    MapCenter.Y -= (Delta.X / Size.X) * CurrentViewWidth;
    MapCenter.X += (Delta.Y / Size.Y) * CurrentViewWidth;
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
    // Right is +Y, up is +X.
    const float X = FMath::Clamp(((Location.Y - MapCenter.Y) / CurrentViewWidth + .5f) * Size.X, 12.f, Size.X - 12.f);
    const float Y = FMath::Clamp((.5f - (Location.X - MapCenter.X) / CurrentViewWidth) * Size.Y, 12.f, Size.Y - 12.f);
    PlayerMarkerSlot->SetPosition(FVector2D(X, Y));
    PlayerMarker->SetRenderTransformAngle(Pawn->GetActorRotation().Yaw);
}

void UEWMapWidget::UpdateScaleBar()
{
    if (!ScaleBarSlot || !ScaleLabel || !MapImage) return;
    const FVector2D Size = MapImage->GetCachedGeometry().GetLocalSize();
    if (Size.X <= 1.f) return;
    // A round distance (1, 2, 5 times a power of ten metres) that makes a bar about a fifth of the picture wide.
    const double WantedMetres = CurrentViewWidth / 100.0 * .2;
    const double Power = FMath::Pow(10.0, FMath::FloorToDouble(FMath::LogX(10.0, FMath::Max(1.0, WantedMetres))));
    double Metres = Power;
    for (double Step : {2.0, 5.0, 10.0}) if (Power * Step <= WantedMetres) Metres = Power * Step;
    ScaleBarSlot->SetSize(FVector2D(float(Metres * 100.0 / CurrentViewWidth) * Size.X, 5.f));
    ScaleLabel->SetText(Metres >= 1000.0 ? FText::Format(NSLOCTEXT("Elitewake", "ScaleKm", "{0} km"), FText::AsNumber(Metres / 1000.0))
        : FText::Format(NSLOCTEXT("Elitewake", "ScaleM", "{0} m"), FText::AsNumber(Metres)));
}

FText UEWMapWidget::GetScaleText() const
{
    return ScaleLabel ? ScaleLabel->GetText() : FText::GetEmpty();
}

void UEWMapWidget::UpdateFog(float DeltaSeconds)
{
    UEWExplorationComponent* Exploration = GetExploration();
    if (!Exploration || !FogTexture || !FogImage) return;
    Exploration->EnsureBounds();
    // Redraw the mist when something new is cleared, and a few times a second for the drifting cloud.
    FogClock += DeltaSeconds;
    if (FogClock >= .2f || Exploration->GetRevision() != FogRevisionDrawn)
    {
        FogClock = 0.f;
        FogRevisionDrawn = Exploration->GetRevision();
        Exploration->BuildFog(FogSize, GetWorld()->GetTimeSeconds(), FogPixels);
        FTexture2DMipMap& Mip = FogTexture->GetPlatformData()->Mips[0];
        void* Data = Mip.BulkData.Lock(LOCK_READ_WRITE);
        FMemory::Memcpy(Data, FogPixels.GetData(), FogPixels.Num() * sizeof(FColor));
        Mip.BulkData.Unlock();
        FogTexture->UpdateResource();
    }
    // The part of the mist image under the picture: the world square the mist covers, and the window the map shows within it.
    const float Size = Exploration->GetBoundsSize();
    if (Size <= 0.f) return;
    // The edge has grown: a map showing the whole world grows with it.
    if (!FMath::IsNearlyEqual(Size, OverviewViewWidth, 1.f))
    {
        const bool bWhole = TargetViewWidth >= OverviewViewWidth * .999f;
        const float Old = OverviewViewWidth;
        OverviewViewWidth = Size;
        if (bWhole) { TargetViewWidth = Size; CurrentViewWidth = Size * CurrentViewWidth / Old; }
        else TargetViewWidth = FMath::Min(TargetViewWidth, Size);
    }
    const FVector2D Min = Exploration->GetBoundsMin();
    const float Half = CurrentViewWidth * .5f;
    const float U0 = (MapCenter.Y - Half - Min.Y) / Size, U1 = (MapCenter.Y + Half - Min.Y) / Size;
    const float V0 = 1.f - (MapCenter.X + Half - Min.X) / Size, V1 = 1.f - (MapCenter.X - Half - Min.X) / Size;
    FSlateBrush Brush = FogImage->GetBrush();
    Brush.SetUVRegion(FBox2f(FVector2f(U0, V0), FVector2f(U1, V1)));
    FogImage->SetBrush(Brush);
}

float UEWMapWidget::GetFogAlphaAtWorld(FVector Location) const
{
    const UEWExplorationComponent* Exploration = GetExploration();
    if (!Exploration || FogPixels.Num() != FogSize * FogSize || Exploration->GetBoundsSize() <= 0.f) return 1.f;
    const FVector2D Min = Exploration->GetBoundsMin();
    const float Size = Exploration->GetBoundsSize();
    const int32 X = FMath::Clamp(int32((Location.Y - Min.Y) / Size * FogSize), 0, FogSize - 1);
    const int32 Y = FMath::Clamp(int32((1.f - (Location.X - Min.X) / Size) * FogSize), 0, FogSize - 1);
    return FogPixels[Y * FogSize + X].A / 255.f;
}

void UEWMapWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    const APawn* Pawn = GetOwningPlayerPawn();
    if (!Pawn || !Capture || !GetOwningPlayer()) return;

    if (!ControllerPanInput.IsNearlyZero())
    {
        // The right stick: right is +Y, up is +X.
        const FVector2D Normalized = ControllerPanInput.GetClampedToMaxSize(1.f);
        MapCenter.Y += Normalized.X * CurrentViewWidth * .72f * DeltaSeconds;
        MapCenter.X += Normalized.Y * CurrentViewWidth * .72f * DeltaSeconds;
    }
    if (!FMath::IsNearlyZero(ControllerZoomInput)) AdjustZoom(ControllerZoomInput * DeltaSeconds * 3.f);

    CurrentViewWidth = FMath::FInterpTo(CurrentViewWidth, TargetViewWidth, DeltaSeconds, 8.f);
    if (auto* Camera = Capture->GetCaptureComponent2D()) Camera->OrthoWidth = CurrentViewWidth;

    const FEWClimate Sample = AEWClimateRegion::SampleClimate(GetWorld(), Pawn->GetActorLocation());
    RegionTitle->SetText(AEWClimateRegion::RegionName(Sample.Region));
    Heading->SetText(FText::Format(NSLOCTEXT("Elitewake", "MapHeading", "Current region  |  Facing {0}°"),
        FText::AsNumber(FMath::RoundToInt(FMath::Fmod(Pawn->GetActorRotation().Yaw + 360.f, 360.f)))));
    PositionPlayerMarker(Pawn);
    UpdateScaleBar();
    UpdateFog(DeltaSeconds);

    CaptureRemaining -= DeltaSeconds;
    if (CaptureRemaining > 0.f) return;
    CaptureRemaining = .5f;
    // Straight down, up the page being the world's +X.
    Capture->SetActorLocationAndRotation(MapCenter + FVector(0, 0, MapCaptureHeight), FRotator(-90.f, 0.f, 0.f));
    Capture->GetCaptureComponent2D()->CaptureScene();
}

void UEWMapWidget::NativeDestruct()
{
    if (Capture) Capture->Destroy();
    Capture = nullptr;
    RenderTarget = nullptr;
    MapMaterial = nullptr;
    FogTexture = nullptr;
    Super::NativeDestruct();
}

bool UEWMapWidget::HasMapCapture() const
{
    return Capture && RenderTarget && MapImage;
}

FLinearColor UEWMapWidget::ProbeMapPixel(FVector2D Uv) const
{
    if (!RenderTarget || !GetWorld()) return FLinearColor::Black;
    const int32 X = FMath::Clamp(int32(Uv.X * RenderTarget->SizeX), 0, RenderTarget->SizeX - 1), Y = FMath::Clamp(int32(Uv.Y * RenderTarget->SizeY), 0, RenderTarget->SizeY - 1);
    return UKismetRenderingLibrary::ReadRenderTargetPixel(const_cast<UEWMapWidget*>(this), RenderTarget, X, Y);
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
