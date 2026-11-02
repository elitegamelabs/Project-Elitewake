#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWArrivalPromptWidget.generated.h"

class UBorder;
class URichTextBlock;

/** The arrival's one prompt at a time (UEWArrivalComponent; then Saltreach's town steps), low in the middle of the screen, clear of the crosshair, the
 *  interaction prompt and the hotbar. Gives way to any menu, death, the helm and the interaction prompt itself. */
UCLASS()
class EW_API UEWArrivalPromptWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Arrival") bool IsPromptVisible() const;
    UFUNCTION(BlueprintPure, Category="Arrival") FText GetDisplayedPrompt() const;
    /** Where the prompt sits: the fraction of the screen's height its middle is at (tuning). */
    static constexpr float HeightFraction = .76f;
    static constexpr int32 FontSize = 24;      // CLAUDE.md: primary text at least 24 px at 1920x1080
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
private:
    UPROPERTY(Transient) TObjectPtr<UBorder> Panel;
    /** Rich text: the controller's buttons are drawn as its own icons (FEWControllerIcons). */
    UPROPERTY(Transient) TObjectPtr<URichTextBlock> Prompt;
    /** The prompt as plain words (the button names spelled out), for GetDisplayedPrompt. */
    FText PlainPrompt;
};
