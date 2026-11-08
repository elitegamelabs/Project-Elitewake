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
    /** Entering or leaving a free port (AEWSafeZone): its name and rules under the region banner, fading. */
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ZoneBanner;
    float ZoneSeconds = 0.f;
    float ZoneCheck = 0.f;
    FString ShownZone;
    bool bZoneKnown = false;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> DiscoveryBanner;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DiscoveryHeading;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DiscoveryName;
    float DiscoverySeconds = 0.f;
public:
    /** The discovery being announced, as shown, for the checks (empty when none is). */
    UFUNCTION(BlueprintPure, Category="Survival|HUD") FText GetDisplayedDiscovery() const;
    /** The sextant's reading shown now (empty with none in hand), for the checks. */
    UFUNCTION(BlueprintPure, Category="Survival|HUD") FString GetDisplayedLatitude() const { return DisplayedLatitude; }
    FString DisplayedLatitude;
    /** The climate line and the region last announced, as shown, for the checks. */
    UFUNCTION(BlueprintPure, Category="Survival|HUD") FText GetDisplayedClimate() const;
    UFUNCTION(BlueprintPure, Category="Survival|HUD") FText GetDisplayedRegionBanner() const;
    UFUNCTION(BlueprintPure, Category="Survival|HUD") FText GetDisplayedZoneBanner() const;
};
