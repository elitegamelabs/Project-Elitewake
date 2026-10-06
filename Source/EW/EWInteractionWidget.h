#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWInteractionWidget.generated.h"

class UBorder;
class UTextBlock;
class UProgressBar;

/** Local read-only targeting and server-timed hold presentation. */
UCLASS()
class EW_API UEWInteractionWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Interaction") FText GetDisplayedPrompt() const;
    UFUNCTION(BlueprintPure, Category="Interaction") float GetDisplayedProgress() const;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
private:
    UPROPERTY(Transient) TObjectPtr<UBorder> Panel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Prompt;
    UPROPERTY(Transient) TObjectPtr<UProgressBar> Progress;
};
