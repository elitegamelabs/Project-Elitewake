#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWContainerWidget.generated.h"

class UTextBlock;
class UVerticalBox;
class UEWInventoryComponent;

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
private:
    UPROPERTY(Transient) TWeakObjectPtr<AActor> Container;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Title;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> CarriedSummary;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> HoldSummary;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> CarriedList;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> HoldList;
    FString Signature;
    float RefreshRemaining = 0.f;
    float OutOfReachSeconds = 0.f;
    UFUNCTION() void Move(int32 Code);
    void Refresh();
    UEWInventoryComponent* CarriedInventory() const;
    UEWInventoryComponent* HoldInventory() const;
    void Close();
};
