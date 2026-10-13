#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "Characters/EWAppearance.h"
#include "EWTitleGameMode.generated.h"

class AEWCharacterPreview;
class UEWCharacterCreatorWidget;
class UEWTitleWidget;

/** The title map's rules: no survivor, just the title controller. */
UCLASS()
class EW_API AEWTitleGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AEWTitleGameMode();
};

/**
 * Runs the front of the game: the title screen, then the character creator (a survivor on the dock in the title
 * map, seen by the camera tagged CreatorCamera, standing at the point tagged PreviewSpot), then Set Sail opens the
 * coast with the chosen look, which is kept and saved by the game instance.
 */
UCLASS()
class EW_API AEWTitlePlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintPure, Category="Title")
    UEWTitleWidget* GetTitleWidget() const { return Title; }
    UFUNCTION(BlueprintPure, Category="Title")
    UEWCharacterCreatorWidget* GetCreatorWidget() const { return Creator; }
    UFUNCTION(BlueprintPure, Category="Title")
    AEWCharacterPreview* GetPreview() const { return Preview; }
    /** Where Set Sail goes. */
    static inline const TCHAR* JourneyMap = TEXT("/Game/Elitewake/Maps/Lvl_CoastalPlayground");
    static inline const TCHAR* TitleArt = TEXT("/Game/Elitewake/UI/Title/T_TitleScreen_v1.T_TitleScreen_v1");
    static inline const TCHAR* RosterPath = TEXT("/Game/Elitewake/Characters/DA_BodyRoster.DA_BodyRoster");
    /** Set by tests so Set Sail records the choice without leaving the title map. */
    UPROPERTY(BlueprintReadWrite, Category="Title")
    bool bStayOnSetSail = false;
    UFUNCTION(BlueprintPure, Category="Title")
    bool HasSetSail() const { return bSetSail; }
private:
    void ShowTitle();
    void ShowCreator();
    void SetSail();
    UPROPERTY(Transient) TObjectPtr<UEWTitleWidget> Title;
    UPROPERTY(Transient) TObjectPtr<UEWCharacterCreatorWidget> Creator;
    UPROPERTY(Transient) TObjectPtr<AEWCharacterPreview> Preview;
    UPROPERTY(Transient) TObjectPtr<UEWBodyRoster> Roster;
    bool bSetSail = false;
};
