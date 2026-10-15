#pragma once

#include "Blueprint/UserWidget.h"
#include "EWSurvivalWidget.generated.h"

class UEWSurvivalComponent;
class UTextBlock;
class UProgressBar;
class UBorder;
class UTexture2D;
class UVerticalBox;

/** Local read-only HUD for the possessed survivor's authoritative values. */
UCLASS()
class EW_API UEWSurvivalWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    /** Current icon values expressed as text for accessibility and verification. */
    UFUNCTION(BlueprintPure, Category="Survival|HUD")
    FText GetDisplayedSummary() const;
    UFUNCTION(BlueprintPure, Category="Survival|HUD")
    FText GetDisplayedWarnings() const;
    /** Actual rendered icon fills, for accessibility and acceptance checks. */
    UFUNCTION(BlueprintPure, Category="Survival|HUD")
    TArray<float> GetDisplayedFillFractions() const;
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
    UPROPERTY(Transient) TArray<TObjectPtr<UTexture2D>> IconTextures;
    FString DisplayedSummary;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> NoticePanel;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> EffectWarnings;
    bool WasEmpty[3] = {};
    bool bHasArt[5] = {};
    float WarningRemaining[3] = {};
    float BlinkTime = 0.f;
    int32 LastExhaustionCount = 0;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ClimateLine;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> RegionBanner;
    float BannerSeconds = 0.f;
    int32 ShownRegion = -1;
public:
    /** The climate line and the region last announced, as shown, for the checks. */
    UFUNCTION(BlueprintPure, Category="Survival|HUD") FText GetDisplayedClimate() const;
    UFUNCTION(BlueprintPure, Category="Survival|HUD") FText GetDisplayedRegionBanner() const;
};
