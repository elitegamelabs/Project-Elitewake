#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWOptionsWidget.generated.h"
class UButton;
class UTextBlock;

/** Escape's in-game OPTIONS menu: SAVE GAME (single player only) and MAIN MENU (back to the ELITEWAKE title). */
UCLASS()
class EW_API UEWOptionsWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Options") int32 GetSelected() const { return Selected; }
    UFUNCTION(BlueprintPure, Category="Options") bool IsSaveShown() const;
    UFUNCTION(BlueprintPure, Category="Options") FText GetStatus() const;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    UFUNCTION() void SaveGame();
    UFUNCTION() void MainMenu();
    UFUNCTION() void HoverSave() { Selected = 0; }
    UFUNCTION() void HoverMenu() { Selected = 1; }
    UPROPERTY(Transient) TObjectPtr<UButton> SaveButton;
    UPROPERTY(Transient) TObjectPtr<UButton> MenuButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Status;
    int32 Selected = 0;
};
