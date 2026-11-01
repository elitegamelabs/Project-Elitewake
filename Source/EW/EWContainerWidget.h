#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWContainerWidget.generated.h"

class UTextBlock;
class UVerticalBox;
class UEWInventoryComponent;
class UEWRecipeButton;

/**
 * Functional first-pass container screen: the survivor's inventory beside a container (a ship's hold).
 * Clicking a stack asks the server to move it across. Final layout and controller navigation come
 * with the menu art pass.
 */
UCLASS()
class EW_API UEWContainerWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void SetContainer(AActor* InContainer);
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeOnInitialized() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;
protected:
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
    virtual FReply NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event) override;
private:
    UPROPERTY(Transient) TWeakObjectPtr<AActor> Container;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Title;
    /** The container column's heading ("Hold", "Strongbox"...). */
    UPROPERTY(Transient) TObjectPtr<UTextBlock> HoldHeading;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> CarriedSummary;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> HoldSummary;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> CarriedList;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> HoldList;
    UPROPERTY(Transient) TArray<TObjectPtr<UEWRecipeButton>> CarriedRows;
    UPROPERTY(Transient) TArray<TObjectPtr<UEWRecipeButton>> HoldRows;
    int32 CursorColumn = 0;          // 0 carried, 1 hold
    int32 CursorRow = 0;
    int32 StickX = 0, StickY = 0;
    float StickRepeat = 0.f;
    /** One step of the d-pad, arrows or left stick: Up/Down along a list, Left/Right across to the other list. */
    void StepCursor(int32 Dx, int32 Dy);
    void ShowCursor();
public:
    /** Test hooks. */
    UFUNCTION(BlueprintPure, Category="Container") int32 GetCursorColumn() const { return CursorColumn; }
    UFUNCTION(BlueprintPure, Category="Container") int32 GetCursorRow() const { return CursorRow; }
    UFUNCTION(BlueprintCallable, Category="Container") void StepCursorForTest(int32 Dx, int32 Dy) { StepCursor(Dx, Dy); }
    UFUNCTION(BlueprintCallable, Category="Container") void MoveAtCursor();
private:
    FString Signature;
    float RefreshRemaining = 0.f;
    float OutOfReachSeconds = 0.f;
    UFUNCTION() void Move(int32 Code);
    void Refresh();
    UEWInventoryComponent* CarriedInventory() const;
    UEWInventoryComponent* HoldInventory() const;
    void Close();
};
