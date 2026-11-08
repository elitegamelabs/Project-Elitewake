#include "EWMapWidget.h"

#include "EWExplorationComponent.h"
#include "EWPlayerController.h"
#include "EWGameState.h"
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
#include "World/EWNorth.h"
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
#include "WaterBodyActor.h"
#include "WaterZoneActor.h"

namespace
{
    constexpr float MinMapViewWidth = 2500.f;
    // Keep the overview wide enough to fit every island; zoom-in still clamps to this map's overview.
    constexpr float MaxMapViewWidth = 40000000.f;
    // A top-down scene capture draws nothing past about 2.5 km from the camera, and the sea floor lies 1.5 km under the sea: 600 m up sees both.
    constexpr float MapCaptureHeight = 60000.f;
    // The sea on the map (owner, November 1: a deep blue ocean round the islands): below the sea surface the map shows
    // water, lighter over the shelves and darkening with depth to the open ocean (tuning).
    constexpr float SeaSurfaceZ = -65.f;                 // world_terrain.SEA
    constexpr float FullDepth = 6000.f;                  // cm below the surface where the deep colour is reached
    const FLinearColor ShallowSea(.07f, .26f, .45f), DeepSea(.012f, .06f, .17f);
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
        PlayerMarkerSlot->SetZOrder(20);

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
    Capture = GetWorld()->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), FVector::ZeroVector, FRotator(-90.f, EWNorth::NorthYaw, 0.f), Params);
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
    // The water surface is left out of the picture: under it the seabed's depth tells sea from land.
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        if (It->IsA<AWaterBody>() || It->IsA<AWaterZone>()) Camera->HiddenActors.Add(*It);

    // How far down the camera sees at every point, from a second capture of the same view.
    DepthTarget = NewObject<UTextureRenderTarget2D>(this);
    DepthTarget->RenderTargetFormat = RTF_R32f;
    DepthTarget->InitAutoFormat(1024, 1024);
    DepthTarget->UpdateResourceImmediate(true);
    DepthCapture = GetWorld()->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), FVector::ZeroVector, FRotator(-90.f, EWNorth::NorthYaw, 0.f), Params);
    if (DepthCapture)
    {
        DepthCapture->SetReplicates(false);
        auto* Depth = DepthCapture->GetCaptureComponent2D();
        Depth->TextureTarget = DepthTarget;
        Depth->ProjectionType = ECameraProjectionMode::Orthographic;
        Depth->OrthoWidth = CurrentViewWidth;
        Depth->CaptureSource = ESceneCaptureSource::SCS_SceneDepth;
        Depth->bCaptureEveryFrame = false;
        Depth->bCaptureOnMovement = false;
        Depth->HiddenActors = Camera->HiddenActors;
    }
    // The picture shown: the captured land with the sea painted over it (ComposeMap).
    MapTexture = UTexture2D::CreateTransient(1024, 1024, PF_B8G8R8A8);
    MapTexture->SRGB = false;            // the capture's bytes are linear, as the old capture material showed them
    MapTexture->NeverStream = true;
    MapTexture->UpdateResource();

    // The capture's alpha is 0, which an image would draw as nothing: a UI material shows its colour at full opacity.
    FSlateBrush Brush;
    Brush.DrawAs = ESlateBrushDrawType::Image;
    Brush.ImageSize = FVector2D(1024, 1024);
    if (DepthCapture && MapTexture) Brush.SetResourceObject(MapTexture);
    else if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Elitewake/UI/Map/M_MapCapture_v1.M_MapCapture_v1")))
    {
        MapMaterial = UMaterialInstanceDynamic::Create(Base, this);
        MapMaterial->SetTextureParameterValue(TEXT("Map"), RenderTarget);
        Brush.SetResourceObject(MapMaterial);
    }
    else Brush.SetResourceObject(RenderTarget);
    MapImage->SetBrush(Brush);

    InitializeWorldOverview();
    CaptureRemaining = 0.f;
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

    // Dragging the picture right shows more of what lies to the west (+X); dragging it down, more of the north (+Y).
    MapCenter.X += (Delta.X / Size.X) * CurrentViewWidth;
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
    // Right is east, up is north (World/EWNorth.h).
    const FVector2D Off = EWNorth::EastNorth(Location - MapCenter);
    const float X = FMath::Clamp((Off.X / CurrentViewWidth + .5f) * Size.X, 12.f, Size.X - 12.f);
    const float Y = FMath::Clamp((.5f - Off.Y / CurrentViewWidth) * Size.Y, 12.f, Size.Y - 12.f);
    PlayerMarkerSlot->SetPosition(FVector2D(X, Y));
    PlayerMarker->SetRenderTransformAngle(EWNorth::BearingOfYaw(Pawn->GetActorRotation().Yaw));
}

void UEWMapWidget::PositionShipMarkers()
{
    if (!MapCanvas || !MapImage || !WidgetTree || !GetWorld()) return;
    const AEWGameState* State = GetWorld()->GetGameState<AEWGameState>();
    const int32 Count = State ? State->ShipsOnMap.Num() : 0;
    const FVector2D Size = MapImage->GetCachedGeometry().GetLocalSize();
    if (Size.X <= 1.f || Size.Y <= 1.f || CurrentViewWidth <= 0.f) return;

    while (ShipMarkers.Num() < Count)
    {
        UTextBlock* Marker = WidgetTree->ConstructWidget<UTextBlock>();
        Marker->SetText(FText::FromString(TEXT("▲")));
        Marker->SetColorAndOpacity(FLinearColor(1.f, .67f, .13f));
        Marker->SetShadowOffset(FVector2D(1.5f, 1.5f));
        Marker->SetShadowColorAndOpacity(FLinearColor::Black);
        Marker->SetVisibility(ESlateVisibility::HitTestInvisible);
        auto Font = Marker->GetFont();
        Font.Size = 22;
        Marker->SetFont(Font);
        UCanvasPanelSlot* MarkerSlot = MapCanvas->AddChildToCanvas(Marker);
        MarkerSlot->SetAlignment(FVector2D(.5f, .5f));
        MarkerSlot->SetAutoSize(true);
        MarkerSlot->SetZOrder(10);
        ShipMarkers.Add(Marker);
        // Her name under the marker, upright (the marker itself turns with her heading).
        UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>();
        Label->SetColorAndOpacity(FLinearColor(1.f, .9f, .7f));
        Label->SetShadowOffset(FVector2D(1.5f, 1.5f));
        Label->SetShadowColorAndOpacity(FLinearColor::Black);
        Label->SetVisibility(ESlateVisibility::Collapsed);
        auto LabelFont = Label->GetFont();
        LabelFont.Size = 15;
        Label->SetFont(LabelFont);
        UCanvasPanelSlot* LabelSlot = MapCanvas->AddChildToCanvas(Label);
        LabelSlot->SetAlignment(FVector2D(.5f, 0.f));
        LabelSlot->SetAutoSize(true);
        LabelSlot->SetZOrder(10);
        ShipNameLabels.Add(Label);
    }

    for (int32 Index = 0; Index < ShipMarkers.Num(); ++Index)
    {
        UTextBlock* Marker = ShipMarkers[Index];
        UTextBlock* Label = ShipNameLabels.IsValidIndex(Index) ? ShipNameLabels[Index].Get() : nullptr;
        if (Label) Label->SetVisibility(ESlateVisibility::Collapsed);
        if (Index >= Count)
        {
            Marker->SetVisibility(ESlateVisibility::Collapsed);
            continue;
        }
        const FEWShipMapEntry& Ship = State->ShipsOnMap[Index];
        const FVector2D Off = EWNorth::EastNorth(Ship.Location - MapCenter);
        const float X = (Off.X / CurrentViewWidth + .5f) * Size.X;
        const float Y = (.5f - Off.Y / CurrentViewWidth) * Size.Y;
        if (X < 0.f || X > Size.X || Y < 0.f || Y > Size.Y)
        {
            Marker->SetVisibility(ESlateVisibility::Collapsed);
            continue;
        }
        if (UCanvasPanelSlot* MarkerSlot = Cast<UCanvasPanelSlot>(Marker->Slot))
            MarkerSlot->SetPosition(FVector2D(X, Y));
        Marker->SetRenderTransformAngle(EWNorth::BearingOfYaw(Ship.Yaw));
        Marker->SetVisibility(ESlateVisibility::HitTestInvisible);
        if (Label && !Ship.Name.IsEmpty())
        {
            Label->SetText(FText::FromString(Ship.Name));
            if (UCanvasPanelSlot* LabelSlot = Cast<UCanvasPanelSlot>(Label->Slot)) LabelSlot->SetPosition(FVector2D(X, Y + 14.f));
            Label->SetVisibility(ESlateVisibility::HitTestInvisible);
        }
    }
}

TArray<FString> UEWMapWidget::GetShownShipNames() const
{
    TArray<FString> Out;
    for (const UTextBlock* Label : ShipNameLabels)
        if (Label && Label->GetVisibility() != ESlateVisibility::Collapsed) Out.Add(Label->GetText().ToString());
    return Out;
}

int32 UEWMapWidget::GetShipMarkerCount() const
{
    const AEWGameState* State = GetWorld() ? GetWorld()->GetGameState<AEWGameState>() : nullptr;
    return State ? State->ShipsOnMap.Num() : 0;
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

void UEWMapWidget::UpdateWorldExtent()
{
    // The whole map is open (owner, November 3: no fog): the explored square only sets how far the map zooms out.
    UEWExplorationComponent* Exploration = GetExploration();
    if (!Exploration) return;
    Exploration->EnsureBounds();
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
}

float UEWMapWidget::GetFogAlphaAtWorld(FVector Location) const
{
    return 0.f;      // the map has no fog (owner, November 3)
}

void UEWMapWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry, DeltaSeconds);
    const APawn* Pawn = GetOwningPlayerPawn();
    if (!Pawn || !Capture || !GetOwningPlayer()) return;

    if (!ControllerPanInput.IsNearlyZero())
    {
        // The right stick: right is east (-X), up is north (+Y).
        const FVector2D Normalized = ControllerPanInput.GetClampedToMaxSize(1.f);
        MapCenter.X -= Normalized.X * CurrentViewWidth * .72f * DeltaSeconds;
        MapCenter.Y += Normalized.Y * CurrentViewWidth * .72f * DeltaSeconds;
    }
    if (!FMath::IsNearlyZero(ControllerZoomInput)) AdjustZoom(ControllerZoomInput * DeltaSeconds * 3.f);

    CurrentViewWidth = FMath::FInterpTo(CurrentViewWidth, TargetViewWidth, DeltaSeconds, 8.f);
    if (auto* Camera = Capture->GetCaptureComponent2D()) Camera->OrthoWidth = CurrentViewWidth;
    if (DepthCapture) DepthCapture->GetCaptureComponent2D()->OrthoWidth = CurrentViewWidth;

    const FEWClimate Sample = AEWClimateRegion::SampleClimate(GetWorld(), Pawn->GetActorLocation());
    RegionTitle->SetText(AEWClimateRegion::RegionName(Sample.Region));
    Heading->SetText(FText::Format(NSLOCTEXT("Elitewake", "MapHeading", "Current region  |  Facing {0}°"),
        FText::AsNumber(FMath::RoundToInt(EWNorth::BearingOfYaw(Pawn->GetActorRotation().Yaw)) % 360)));
    PositionPlayerMarker(Pawn);
    PositionShipMarkers();
    UpdateScaleBar();
    UpdateWorldExtent();

    CaptureRemaining -= DeltaSeconds;
    if (CaptureRemaining > 0.f) return;
    CaptureRemaining = .5f;
    // Straight down, up the page being north.
    Capture->SetActorLocationAndRotation(MapCenter + FVector(0, 0, MapCaptureHeight), FRotator(-90.f, EWNorth::NorthYaw, 0.f));
    Capture->GetCaptureComponent2D()->CaptureScene();
    if (DepthCapture)
    {
        DepthCapture->SetActorLocationAndRotation(Capture->GetActorLocation(), Capture->GetActorRotation());
        DepthCapture->GetCaptureComponent2D()->CaptureScene();
        ComposeMap();
    }
}

void UEWMapWidget::ComposeMap()
{
    // Read back both captures (only while the map is open, twice a second) and paint the sea where the ground lies
    // below the surface: the land keeps its own colours.
    FTextureRenderTargetResource* ColourResource = RenderTarget ? RenderTarget->GameThread_GetRenderTargetResource() : nullptr;
    FTextureRenderTargetResource* DepthResource = DepthTarget ? DepthTarget->GameThread_GetRenderTargetResource() : nullptr;
    if (!ColourResource || !DepthResource || !MapTexture) return;
    if (!ColourResource->ReadPixels(ColourPixels) || !DepthResource->ReadLinearColorPixels(DepthPixels)) return;
    if (ColourPixels.Num() != DepthPixels.Num() || ColourPixels.Num() != 1024 * 1024) return;
    const float CameraZ = Capture->GetActorLocation().Z;
    for (int32 i = 0; i < ColourPixels.Num(); ++i)
    {
        const float Below = SeaSurfaceZ - (CameraZ - DepthPixels[i].R);     // cm under the sea surface (negative: land)
        FColor& Pixel = ColourPixels[i];
        if (Below > 0.f)
        {
            // A soft edge at the shore, then shallow to deep.
            const float Shore = FMath::Clamp(Below / 150.f, 0.f, 1.f);
            const FLinearColor Sea = FMath::Lerp(ShallowSea, DeepSea, FMath::Clamp(FMath::Sqrt(Below / FullDepth), 0.f, 1.f));
            const FLinearColor Land(Pixel.R / 255.f, Pixel.G / 255.f, Pixel.B / 255.f);
            Pixel = FMath::Lerp(Land, Sea, Shore).ToFColor(false);
        }
        Pixel.A = 255;
    }
    FTexture2DMipMap& Mip = MapTexture->GetPlatformData()->Mips[0];
    void* Data = Mip.BulkData.Lock(LOCK_READ_WRITE);
    FMemory::Memcpy(Data, ColourPixels.GetData(), ColourPixels.Num() * sizeof(FColor));
    Mip.BulkData.Unlock();
    MapTexture->UpdateResource();
}

void UEWMapWidget::NativeDestruct()
{
    if (Capture) Capture->Destroy();
    Capture = nullptr;
    if (DepthCapture) DepthCapture->Destroy();
    DepthCapture = nullptr;
    DepthTarget = nullptr;
    MapTexture = nullptr;
    RenderTarget = nullptr;
    MapMaterial = nullptr;
    Super::NativeDestruct();
}

bool UEWMapWidget::HasMapCapture() const
{
    return Capture && RenderTarget && MapImage;
}

FLinearColor UEWMapWidget::ProbeMapPixel(FVector2D Uv) const
{
    if (MapTexture && ColourPixels.Num() == 1024 * 1024)
    {
        const int32 X = FMath::Clamp(int32(Uv.X * 1024), 0, 1023), Y = FMath::Clamp(int32(Uv.Y * 1024), 0, 1023);
        const FColor& C = ColourPixels[Y * 1024 + X];
        return FLinearColor(C.R / 255.f, C.G / 255.f, C.B / 255.f, 1.f);
    }
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
