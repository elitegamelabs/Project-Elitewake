#pragma once

#include "Blueprint/UserWidget.h"
#include "EWSurvivalWidget.generated.h"

class UEWSurvivalComponent;
class UTextBlock;
class UProgressBar;
class UBorder;

/** Local read-only HUD for the possessed survivor's authoritative values. */
UCLASS()
class EW_API UEWSurvivalWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    /** The actual rendered labels, also useful for accessibility and verification. */
    UFUNCTION(BlueprintPure, Category="Survival|HUD")
    FText GetDisplayedSummary() const;
    UFUNCTION(BlueprintPure, Category="Survival|HUD")
    FText GetDisplayedWarnings() const;
    virtual void NativeConstruct() override;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
private:
    void BuildWidgetTree();
    UPROPERTY(Transient)
    TObjectPtr<UBorder> Panel;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> Labels;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UProgressBar>> Bars;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> Warnings;
    TWeakObjectPtr<UEWSurvivalComponent> PreviousSurvival;
    bool WasEmpty[3] = {};
    float WarningRemaining[3] = {};
    float BlinkTime = 0.f;
    int32 LastExhaustionCount = 0;
};
