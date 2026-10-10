#include "EWMapWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
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
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

TSharedRef<SWidget> UEWMapWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Panel = WidgetTree->ConstructWidget<UBorder>();
        Panel->SetBrushColor(FLinearColor(.015f,.025f,.035f,.97f));
        Panel->SetPadding(FMargin(28)); WidgetTree->RootWidget = Panel;
        auto* Content = WidgetTree->ConstructWidget<UVerticalBox>(); Panel->SetContent(Content);
        auto* Title = WidgetTree->ConstructWidget<UTextBlock>();
        Title->SetText(NSLOCTEXT("Elitewake","MapTitle","SURROUNDING AREA"));
        auto Font = Title->GetFont(); Font.Size = 26; Title->SetFont(Font);
        Content->AddChildToVerticalBox(Title);
        Heading = WidgetTree->ConstructWidget<UTextBlock>();
        Font.Size = 16; Heading->SetFont(Font); Content->AddChildToVerticalBox(Heading);
        auto* Scale = WidgetTree->ConstructWidget<UScaleBox>(); Scale->SetStretch(EStretch::ScaleToFit);
        auto* Overlay = WidgetTree->ConstructWidget<UOverlay>(); Scale->SetContent(Overlay);
        MapImage = WidgetTree->ConstructWidget<UImage>(); Overlay->AddChildToOverlay(MapImage);
        PlayerMarker=WidgetTree->ConstructWidget<UTextBlock>();
        PlayerMarker->SetText(FText::FromString(TEXT("\u25B2")));
        Font.Size=28; PlayerMarker->SetFont(Font); PlayerMarker->SetColorAndOpacity(FLinearColor(.1f,.85f,1.f));
        auto* MarkerSlot=Overlay->AddChildToOverlay(PlayerMarker); MarkerSlot->SetHorizontalAlignment(HAlign_Center); MarkerSlot->SetVerticalAlignment(VAlign_Center);
        Content->AddChildToVerticalBox(Scale)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto* Hint = WidgetTree->ConstructWidget<UTextBlock>();
        Hint->SetText(NSLOCTEXT("Elitewake","MapHint","M: Close map  |  Walking remains available  |  World continues"));
        Hint->SetFont(Font); Content->AddChildToVerticalBox(Hint);
    }
    return Super::RebuildWidget();
}

void UEWMapWidget::NativeConstruct()
{
    Super::NativeConstruct(); SetVisibility(ESlateVisibility::HitTestInvisible);
    if (!GetOwningPlayer() || !GetOwningPlayer()->IsLocalController()) return;
    RenderTarget = NewObject<UTextureRenderTarget2D>(this);
    RenderTarget->RenderTargetFormat = RTF_RGBA8;
    RenderTarget->InitAutoFormat(1024,1024);
    RenderTarget->UpdateResourceImmediate(true);
    FActorSpawnParameters Params; Params.Owner = GetOwningPlayer();
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    Capture = GetWorld()->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), FVector::ZeroVector, FRotator(-90,0,0), Params);
    if (!Capture) return;
    Capture->SetReplicates(false);
    auto* Camera = Capture->GetCaptureComponent2D();
    Camera->TextureTarget = RenderTarget;
    Camera->ProjectionType = ECameraProjectionMode::Orthographic;
    Camera->OrthoWidth = ViewWidth;
    Camera->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
    Camera->bCaptureEveryFrame = false; Camera->bCaptureOnMovement = false;
    Camera->ShowFlags.SetAtmosphere(false); Camera->ShowFlags.SetFog(false);
    FSlateBrush Brush; Brush.DrawAs=ESlateBrushDrawType::Image; Brush.SetResourceObject(RenderTarget); Brush.ImageSize = FVector2D(1024,1024);
    MapImage->SetBrush(Brush);
    CaptureRemaining = 0.f;
}

void UEWMapWidget::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry,DeltaSeconds);
    auto* Pawn = GetOwningPlayerPawn();
    if (!Pawn || !Capture) return;
    PlayerMarker->SetRenderTransformAngle(Pawn->GetActorRotation().Yaw);
    Heading->SetText(FText::Format(NSLOCTEXT("Elitewake","MapHeading","You are at the center · Facing {0}°"),
        FText::AsNumber(FMath::RoundToInt(FMath::Fmod(Pawn->GetActorRotation().Yaw+360.f,360.f)))));
    CaptureRemaining -= DeltaSeconds;
    if (CaptureRemaining > 0.f) return;
    CaptureRemaining = .5f;
    MapCenter = Pawn->GetActorLocation();
    Capture->SetActorLocation(MapCenter + FVector(0,0,8000));
    Capture->GetCaptureComponent2D()->CaptureScene();
}

void UEWMapWidget::NativeDestruct()
{
    if (Capture) Capture->Destroy();
    Capture = nullptr; RenderTarget = nullptr;
    Super::NativeDestruct();
}

bool UEWMapWidget::HasMapCapture() const { return Capture && RenderTarget && MapImage; }
