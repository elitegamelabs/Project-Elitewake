#include "Title/EWTitleGameMode.h"
#include "Title/EWTitleWidget.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"
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
    bShowMouseCursor = true;
    ShowTitle();
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
    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(Title->TakeWidget());
    SetInputMode(Mode);
    // Establish focus after the full-screen widget has entered the viewport.
    Title->SetUserFocus(this);
}

void AEWTitlePlayerController::StartSinglePlayer()
{
    if (bSetSail || !Title || Title->GetScreen() != EEWTitleScreen::MainMenu) return;
    bSetSail = true;
    if (bStayOnSetSail) return;
    Title->RemoveFromParent();
    Title = nullptr;
    SetInputMode(FInputModeGameOnly());
    bShowMouseCursor = false;
    UGameplayStatics::OpenLevel(this, FName(JourneyMap));
}
