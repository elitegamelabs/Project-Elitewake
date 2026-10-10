#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWObjectiveWidget.generated.h"

class UBorder;
class UTextBlock;
class USizeBox;

/** Read-only current objective; does not expose Journal or completion controls. */
UCLASS()
class EW_API UEWObjectiveWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Objectives") bool IsObjectiveVisible() const;
    UFUNCTION(BlueprintPure, Category="Objectives") FText GetDisplayedDescription() const;
    UFUNCTION(BlueprintPure, Category="Objectives") FText GetDisplayedCount() const;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
private:
    UPROPERTY(Transient) TObjectPtr<UBorder> Panel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Description;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Count;
    UPROPERTY(Transient) TObjectPtr<USizeBox> WidthBox;
};
