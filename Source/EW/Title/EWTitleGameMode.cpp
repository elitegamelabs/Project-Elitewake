#include "Title/EWTitleGameMode.h"
#include "Title/EWCharacterCreatorWidget.h"
#include "Title/EWCharacterPreview.h"
#include "Title/EWTitleWidget.h"
#include "EWGameInstance.h"
#include "Camera/CameraActor.h"
#include "Engine/TargetPoint.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

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

void AEWTitlePlayerController::ShowTitle()
{
    if (Creator) { Creator->RemoveFromParent(); Creator = nullptr; }
    if (Preview) { Preview->Destroy(); Preview = nullptr; }
    Title = CreateWidget<UEWTitleWidget>(this, UEWTitleWidget::StaticClass());
    Title->Art = Cast<UTexture2D>(FSoftObjectPath(TitleArt).TryLoad());
    Title->OnStartJourney.BindUObject(this, &AEWTitlePlayerController::ShowCreator);
    Title->AddToViewport(10);
    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(Title->TakeWidget());
    SetInputMode(Mode);
}

void AEWTitlePlayerController::ShowCreator()
{
    if (Title) { Title->RemoveFromParent(); Title = nullptr; }
    ACameraActor* Camera = nullptr;
    for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It) if (It->ActorHasTag(TEXT("CreatorCamera"))) Camera = *It;
    FTransform Spot = FTransform::Identity;
    for (TActorIterator<ATargetPoint> It(GetWorld()); It; ++It) if (It->ActorHasTag(TEXT("PreviewSpot"))) Spot = It->GetActorTransform();
    if (Camera) SetViewTarget(Camera);
    Preview = GetWorld()->SpawnActor<AEWCharacterPreview>(AEWCharacterPreview::StaticClass(), Spot);

    Creator = CreateWidget<UEWCharacterCreatorWidget>(this, UEWCharacterCreatorWidget::StaticClass());
    Creator->Roster = Roster;
    // Start from the look made last time, if any.
    if (const auto* Instance = Cast<UEWGameInstance>(GetGameInstance()); Instance && Instance->HasChosenAppearance())
        Creator->Appearance = Instance->GetChosenAppearance();
    Creator->OnChanged.BindLambda([this]() { if (Preview && Creator) Preview->ShowAppearance(Creator->GetAppearance(), Roster); });
    Creator->OnTurn.BindLambda([this](float Degrees) { if (Preview) Preview->Turn(Degrees); });
    Creator->OnSetSail.BindUObject(this, &AEWTitlePlayerController::SetSail);
    Creator->OnBack.BindUObject(this, &AEWTitlePlayerController::ShowTitle);
    Creator->AddToViewport(10);
    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(Creator->TakeWidget());
    SetInputMode(Mode);
}

void AEWTitlePlayerController::SetSail()
{
    if (bSetSail || !Creator) return;
    bSetSail = true;
    if (auto* Instance = Cast<UEWGameInstance>(GetGameInstance())) Instance->SetChosenAppearance(Creator->GetAppearance().Clamped(Roster));
    if (bStayOnSetSail) return;
    SetInputMode(FInputModeGameOnly());
    bShowMouseCursor = false;
    UGameplayStatics::OpenLevel(this, FName(JourneyMap));
}
