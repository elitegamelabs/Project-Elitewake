#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWSessionWidget.generated.h"
class UEditableTextBox;
class UTextBlock;
class UButton;
UCLASS()
class EW_API UEWSessionWidget : public UUserWidget
{
    GENERATED_BODY()
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry,float Delta) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry,const FKeyEvent& Event) override;
private:
    UFUNCTION() void Host();
    UFUNCTION() void Join();
    UFUNCTION() void Leave();
    UFUNCTION() void Close();
    UPROPERTY(Transient) TObjectPtr<UEditableTextBox> Address;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Status;
    UPROPERTY(Transient) TObjectPtr<UButton> HostButton;
    UPROPERTY(Transient) TObjectPtr<UButton> JoinButton;
    UPROPERTY(Transient) TObjectPtr<UButton> LeaveButton;
};
