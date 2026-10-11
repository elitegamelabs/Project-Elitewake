#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWCompanyWidget.generated.h"
class UTextBlock;
class UEditableTextBox;
class UVerticalBox;
UCLASS()
class EW_API UEWCompanyWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry,float Delta) override;
private:
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Roster;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Result;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> TargetLabel;
    UPROPERTY(Transient) TObjectPtr<UEditableTextBox> NameInput;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> People;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Policies;
    TArray<int32> Targets;
    int32 SelectedTarget=INDEX_NONE;
    FString PeopleSignature;
    float RefreshRemaining=0;
    UFUNCTION() void Action(int32 Index);
    void Refresh();
};
