#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "EWTitleGameMode.generated.h"

class ACameraActor;
class AEWCharacterPreview;
class UEWBodyRoster;
class UEWCharacterCreatorWidget;
class UEWPortSelectWidget;
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

/**
 * The single-player front end (owner, November 7): the splash and main menu, then Single Player opens the Freeport choice
 * (the whole world, every island), Resume Game or Create New Survivor, the character creator, and Set Sail: the loading
 * screen and the coast, with a new survivor set down at the chosen Freeport.
 */
UCLASS()
class EW_API AEWTitlePlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    virtual void PlayerTick(float DeltaTime) override;

    UFUNCTION(BlueprintPure, Category="Title") UEWTitleWidget* GetTitleWidget() const { return Title; }
    UFUNCTION(BlueprintPure, Category="Title") UEWPortSelectWidget* GetPortSelectWidget() const { return PortSelect; }
    UFUNCTION(BlueprintPure, Category="Title") UEWCharacterCreatorWidget* GetCreatorWidget() const { return Creator; }
    UFUNCTION(BlueprintPure, Category="Title") AEWCharacterPreview* GetPreview() const { return Preview; }
    /** Where Single Player goes. */
    static inline const TCHAR* JourneyMap = TEXT("/Game/Elitewake/Maps/Lvl_CoastalPlayground");
    static inline const TCHAR* TitleArt = TEXT("/Game/Elitewake/UI/Title/T_ElitewakeStarterScreen_20261013.T_ElitewakeStarterScreen_20261013");
    static inline const TCHAR* PromptArt = TEXT("/Game/Elitewake/UI/Title/T_PressAnyKeyToStart_20261013_v2.T_PressAnyKeyToStart_20261013_v2");
    static inline const TCHAR* MainMenuArt = TEXT("/Game/Elitewake/UI/Title/T_MainMenu_20261013.T_MainMenu_20261013");
    static inline const TCHAR* TitleWaterMask = TEXT("/Game/Elitewake/UI/Title/T_TitleWaterMask_20261013.T_TitleWaterMask_20261013");
    static inline const TCHAR* TitleWaterMaterial = TEXT("/Game/Elitewake/UI/Title/M_TitleScreenWater_20261013.M_TitleScreenWater_20261013");
    static inline const TCHAR* WorldMapArt = TEXT("/Game/Elitewake/UI/FrontEnd/T_WorldMap_PortSelect.T_WorldMap_PortSelect");
    static inline const TCHAR* RosterPath = TEXT("/Game/Elitewake/Characters/DA_BodyRoster.DA_BodyRoster");
    /** Set by acceptance tests so Set Sail can be recorded without leaving the title map. */
    UPROPERTY(BlueprintReadWrite, Category="Title")
    bool bStayOnSetSail = false;
    UFUNCTION(BlueprintPure, Category="Title") bool HasSetSail() const { return bSetSail; }
    /** Set Sail resumed the survivor played before (else a new one). */
    UFUNCTION(BlueprintPure, Category="Title") bool DidResume() const { return bResumed; }
private:
    void ShowTitle();
    void ShowPortSelect();
    void ShowCreator();
    void LeaveCreator();
    void StartSinglePlayer();
    void SetSail(bool bResume);
    void Focus(class UUserWidget* Widget);
    void PlaceCreatorCamera(float DeltaTime);
    UPROPERTY(Transient) TObjectPtr<UEWTitleWidget> Title;
    UPROPERTY(Transient) TObjectPtr<UEWPortSelectWidget> PortSelect;
    UPROPERTY(Transient) TObjectPtr<UEWCharacterCreatorWidget> Creator;
    UPROPERTY(Transient) TObjectPtr<AEWCharacterPreview> Preview;
    UPROPERTY(Transient) TObjectPtr<ACameraActor> CreatorCamera;
    UPROPERTY(Transient) TObjectPtr<UEWBodyRoster> Roster;
    FTransform PreviewSpot = FTransform::Identity;
    float Zoom = 0.f, ZoomShown = 0.f;
    int32 ChosenPort = 0;
    bool bSetSail = false;
    bool bResumed = false;
};
