#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "EWTitleGameMode.generated.h"

class UEWTitleWidget;
class UMaterialInterface;
class UTexture2D;

/** The title map's rules: no survivor, just the title controller. */
UCLASS()
class EW_API AEWTitleGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AEWTitleGameMode();
};

/** Runs the splash and main menu, then opens the coastal game directly as a normal survivor. */
UCLASS()
class EW_API AEWTitlePlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintPure, Category="Title")
    UEWTitleWidget* GetTitleWidget() const { return Title; }
    /** Where Single Player goes. */
    static inline const TCHAR* JourneyMap = TEXT("/Game/Elitewake/Maps/Lvl_CoastalPlayground");
    static inline const TCHAR* TitleArt = TEXT("/Game/Elitewake/UI/Title/T_ElitewakeStarterScreen_20261013.T_ElitewakeStarterScreen_20261013");
    static inline const TCHAR* PromptArt = TEXT("/Game/Elitewake/UI/Title/T_PressAnyKeyToStart_20261013_v2.T_PressAnyKeyToStart_20261013_v2");
    static inline const TCHAR* MainMenuArt = TEXT("/Game/Elitewake/UI/Title/T_MainMenu_20261013.T_MainMenu_20261013");
    static inline const TCHAR* TitleWaterMask = TEXT("/Game/Elitewake/UI/Title/T_TitleWaterMask_20261013.T_TitleWaterMask_20261013");
    static inline const TCHAR* TitleWaterMaterial = TEXT("/Game/Elitewake/UI/Title/M_TitleScreenWater_20261013.M_TitleScreenWater_20261013");
    /** Set by acceptance tests so Single Player can be recorded without leaving the title map. */
    UPROPERTY(BlueprintReadWrite, Category="Title")
    bool bStayOnSetSail = false;
    UFUNCTION(BlueprintPure, Category="Title") bool HasSetSail() const { return bSetSail; }
private:
    void ShowTitle();
    UPROPERTY(Transient) TObjectPtr<UEWTitleWidget> Title;
    void StartSinglePlayer();
    bool bSetSail = false;
};
