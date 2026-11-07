#include "Title/EWTitleGameMode.h"
#include "Title/EWCharacterCreatorWidget.h"
#include "Title/EWCharacterPreview.h"
#include "Title/EWFreeports.h"
#include "Title/EWPortSelectWidget.h"
#include "Title/EWTitleWidget.h"
#include "EWGameInstance.h"
#include "EWSurvivorSave.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/TargetPoint.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

AEWTitleGameMode::AEWTitleGameMode()
{
    DefaultPawnClass = nullptr;
    bStartPlayersAsSpectators = true;
    PlayerControllerClass = AEWTitlePlayerController::StaticClass();
}

void AEWTitlePlayerController::BeginPlay()
{
    Super::BeginPlay();
    if (!IsLocalController()) return;
    Roster = Cast<UEWBodyRoster>(FSoftObjectPath(RosterPath).TryLoad());
    bShowMouseCursor = true;
    ShowTitle();
}

void AEWTitlePlayerController::Focus(UUserWidget* Widget)
{
    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(Widget->TakeWidget());
    SetInputMode(Mode);
    // Establish focus after the full-screen widget has entered the viewport.
    Widget->SetUserFocus(this);
}

void AEWTitlePlayerController::ShowTitle()
{
    Title = CreateWidget<UEWTitleWidget>(this, UEWTitleWidget::StaticClass());
    if (!Title) return;
    Title->Art = Cast<UTexture2D>(FSoftObjectPath(TitleArt).TryLoad());
    Title->PromptArt = Cast<UTexture2D>(FSoftObjectPath(PromptArt).TryLoad());
    Title->MainMenuArt = Cast<UTexture2D>(FSoftObjectPath(MainMenuArt).TryLoad());
    Title->WaterMaskArt = Cast<UTexture2D>(FSoftObjectPath(TitleWaterMask).TryLoad());
    Title->WaterMaterial = Cast<UMaterialInterface>(FSoftObjectPath(TitleWaterMaterial).TryLoad());
    Title->OnSinglePlayer.BindUObject(this, &AEWTitlePlayerController::StartSinglePlayer);
    Title->AddToViewport(10);
    Focus(Title);
}

void AEWTitlePlayerController::StartSinglePlayer()
{
    if (!Title || Title->GetScreen() != EEWTitleScreen::MainMenu) return;
    ShowPortSelect();
}

void AEWTitlePlayerController::ShowPortSelect()
{
    if (Title) Title->SetVisibility(ESlateVisibility::Collapsed);
    if (!PortSelect)
    {
        PortSelect = CreateWidget<UEWPortSelectWidget>(this, UEWPortSelectWidget::StaticClass());
        PortSelect->MapArt = Cast<UTexture2D>(FSoftObjectPath(WorldMapArt).TryLoad());
        PortSelect->OnResume.BindLambda([this]() { SetSail(true); });
        PortSelect->OnCreateNew.BindUObject(this, &AEWTitlePlayerController::ShowCreator);
        PortSelect->OnBack.BindLambda([this]()
        {
            PortSelect->RemoveFromParent();
            if (Title) { Title->SetVisibility(ESlateVisibility::Visible); Focus(Title); }
        });
    }
    // Resume is offered only to a player who has played before: a survivor was saved.
    PortSelect->bCanResume = UEWSurvivorSave::HasSave();
    PortSelect->ResumeNote = FText::GetEmpty();
    if (PortSelect->bCanResume)
        if (const UEWSurvivorSave* Save = UEWSurvivorSave::LoadSave())
            PortSelect->ResumeNote = FText::FromString(FString::Printf(TEXT("Continue where you left off  ·  saved %s"),
                *Save->SavedAt.ToString(TEXT("%d %b, %H:%M"))));
    PortSelect->SelectPort(ChosenPort);
    if (!PortSelect->IsInViewport()) PortSelect->AddToViewport(11);
    Focus(PortSelect);
}

void AEWTitlePlayerController::ShowCreator()
{
    ChosenPort = PortSelect ? PortSelect->GetSelectedPort() : 0;
    if (PortSelect) PortSelect->RemoveFromParent();
    if (Title) Title->SetVisibility(ESlateVisibility::Collapsed);
    for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It) if (It->ActorHasTag(TEXT("CreatorCamera"))) CreatorCamera = *It;
    for (TActorIterator<ATargetPoint> It(GetWorld()); It; ++It) if (It->ActorHasTag(TEXT("PreviewSpot"))) PreviewSpot = It->GetActorTransform();
    if (!Preview) Preview = GetWorld()->SpawnActor<AEWCharacterPreview>(AEWCharacterPreview::StaticClass(), PreviewSpot);
    Zoom = ZoomShown = 0.f;
    if (CreatorCamera) { PlaceCreatorCamera(0.f); SetViewTarget(CreatorCamera); }

    Creator = CreateWidget<UEWCharacterCreatorWidget>(this, UEWCharacterCreatorWidget::StaticClass());
    Creator->Roster = Roster;
    // A new survivor starts from the first preset, a man; the player changes it from there.
    FEWAppearance Start;
    Start.ApplyPreset(0);
    Creator->Appearance = Start;
    Creator->OnChanged.BindLambda([this]() { if (Preview && Creator) Preview->ShowAppearance(Creator->GetAppearance(), Roster); });
    Creator->OnTurn.BindLambda([this](float Degrees) { if (Preview) Preview->Turn(Degrees); });
    Creator->OnZoom.BindLambda([this](float Step) { Zoom = FMath::Clamp(Zoom + Step * .2f, 0.f, 1.f); });
    Creator->OnSetSail.BindLambda([this]() { SetSail(false); });
    Creator->OnBack.BindUObject(this, &AEWTitlePlayerController::LeaveCreator);
    Creator->AddToViewport(11);
    Focus(Creator);
}

void AEWTitlePlayerController::LeaveCreator()
{
    if (Creator) { Creator->RemoveFromParent(); Creator = nullptr; }
    if (Preview) { Preview->Destroy(); Preview = nullptr; }
    ShowPortSelect();
}

void AEWTitlePlayerController::PlaceCreatorCamera(float DeltaTime)
{
    if (!CreatorCamera) return;
    ZoomShown = DeltaTime > 0.f ? FMath::FInterpTo(ZoomShown, Zoom, DeltaTime, 6.f) : Zoom;
    // Frame the survivor in the middle of the creator's preview box (the left half), whole at no zoom, the head at full.
    const float Fov = CreatorCamera->GetCameraComponent()->FieldOfView;
    // Whole, the frame scales with the survivor's height (the feet on the dock, the head clear of the box's top).
    const float Tall = Creator ? Creator->GetAppearance().Height : 1.f;
    const float Distance = FMath::Lerp(660.f * Tall, 170.f, ZoomShown);
    const float Height = FMath::Lerp(100.f * Tall, 160.f * Tall, ZoomShown);
    float BoxCentre = -.49f;      // the preview box's middle across the screen, -1 left to 1 right
    if (Creator)
    {
        const FVector4 Box = Creator->GetPreviewBox();
        const FVector2D Size = Creator->GetCachedGeometry().GetLocalSize();
        if (Size.X > 1.f) BoxCentre = (Box.X + Box.Z * .5f) / Size.X * 2.f - 1.f;
    }
    const float Across = BoxCentre * Distance * FMath::Tan(FMath::DegreesToRadians(Fov * .5f));
    const FVector Forward = PreviewSpot.GetRotation().GetForwardVector();
    const FVector Right = PreviewSpot.GetRotation().GetRightVector();
    // The camera stands in front of the survivor, looking back at them; the survivor's right is the camera's left, so to show
    // them left of centre the camera steps to their left (Across < 0).
    const FVector At = PreviewSpot.GetLocation() + Forward * Distance + Right * Across + FVector(0, 0, Height);
    CreatorCamera->SetActorLocationAndRotation(At, FRotator(-2.f, (-Forward).Rotation().Yaw, 0.f));
}

void AEWTitlePlayerController::PlayerTick(float DeltaTime)
{
    Super::PlayerTick(DeltaTime);
    if (Creator && CreatorCamera) PlaceCreatorCamera(DeltaTime);
}

void AEWTitlePlayerController::SetSail(bool bResume)
{
    if (bSetSail) return;
    bSetSail = true;
    bResumed = bResume;
    if (!bResume && PortSelect) ChosenPort = PortSelect->GetSelectedPort();
    auto* Instance = GetGameInstance<UEWGameInstance>();
    if (Instance)
    {
        if (!bResume && Creator) Instance->SetChosenAppearance(Creator->GetAppearance().Clamped(Roster));
        Instance->PrepareVoyage(bResume, FName(EWFreeports::List[ChosenPort].Id));
    }
    if (bStayOnSetSail) return;
    if (Creator) { Creator->RemoveFromParent(); Creator = nullptr; }
    if (PortSelect) PortSelect->RemoveFromParent();
    if (Title) { Title->RemoveFromParent(); Title = nullptr; }
    if (Instance) Instance->ShowLoadingScreen();
    SetInputMode(FInputModeGameOnly());
    bShowMouseCursor = false;
    // Let the loading screen draw once before the map load holds the game thread.
    FTimerHandle Open;
    GetWorldTimerManager().SetTimer(Open, FTimerDelegate::CreateWeakLambda(this, [this]()
    {
        UGameplayStatics::OpenLevel(this, FName(JourneyMap));
    }), .25f, false);
}
