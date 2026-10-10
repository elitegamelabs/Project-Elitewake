#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWInteractionWidget.generated.h"

class UBorder;
class UTextBlock;
class UProgressBar;
class AEWInnTorchPickup;

/** Local read-only targeting and server-timed hold presentation. */
UCLASS()
class EW_API UEWInteractionWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Interaction") FText GetDisplayedPrompt() const;
    UFUNCTION(BlueprintPure, Category="Interaction") float GetDisplayedProgress() const;
    UFUNCTION(BlueprintPure, Category="Inn") FText GetInnMessage() const;
    UFUNCTION(BlueprintPure, Category="Inn") int32 GetHighlightedTorchCount() const { return HighlightedTorches.Num(); }
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& Clip,
        FSlateWindowElementList& Elements, int32 Layer, const FWidgetStyle& Style, bool bEnabled) const override;
private:
    UPROPERTY(Transient) TObjectPtr<UTextBlock> InnMessage;
    TArray<TWeakObjectPtr<AEWInnTorchPickup>> HighlightedTorches;
    UPROPERTY(Transient) TObjectPtr<UBorder> Panel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Prompt;
    UPROPERTY(Transient) TObjectPtr<UProgressBar> Progress;
};
