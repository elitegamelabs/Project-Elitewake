#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWDialogueWidget.generated.h"

class AEWTownsfolk;
class UEWRecipeButton;
class UTextBlock;
class UVerticalBox;

/**
 * The dialogue window (owner, October 30: each Freeport NPC has a simple dialogue window). A panel low on the screen: the person's
 * name and role, what they say, and their choices as numbered buttons (click, or press 1 to 9; Up/Down and Enter, or the D-pad and A,
 * also work). Leave (Escape, E, Tab, or the controller's B) closes it, and walking out of reach closes it too. The choices are
 * refreshed from replicated state twice a second, so stock, prices and the purse stay current; a choice goes to the server, whose
 * answer replaces what the person says.
 */
UCLASS()
class EW_API UEWDialogueWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void SetSpeaker(AEWTownsfolk* NewSpeaker);
    void ShowReply(const FText& Reply);
    UFUNCTION(BlueprintPure, Category="Dialogue") AEWTownsfolk* GetSpeaker() const { return Speaker.Get(); }
    UFUNCTION(BlueprintPure, Category="Dialogue") FText GetShownLine() const;
    UFUNCTION(BlueprintPure, Category="Dialogue") int32 GetShownOptionCount() const { return Keys.Num(); }
    /** Choose the shown choice at Index (0-based); false when it is closed to the survivor now. */
    UFUNCTION(BlueprintCallable, Category="Dialogue") bool Choose(int32 Index);
    UFUNCTION(BlueprintCallable, Category="Dialogue") void Close();
    /** A choice that asks for text (a ship's name): its box is open. */
    UFUNCTION(BlueprintPure, Category="Dialogue") bool IsAskingForText() const { return !TextKey.IsNone(); }
    UFUNCTION(BlueprintPure, Category="Dialogue") FString GetEnteredText() const;
    /** Fills the box with a ship name nobody bears (the Suggest button, the controller's X). */
    UFUNCTION(BlueprintCallable, Category="Dialogue") void SuggestText();
    /** Sends what is in the box (Register, Enter, the controller's A). */
    UFUNCTION(BlueprintCallable, Category="Dialogue") void SubmitText();
    UFUNCTION(BlueprintCallable, Category="Dialogue") void CancelText();
    /** Types into the box (checks). */
    UFUNCTION(BlueprintCallable, Category="Dialogue") void SetEnteredText(const FString& Text);
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    UFUNCTION() void OnOptionPressed(int32 Index) { Choose(Index); }
    UFUNCTION() void OnTextButton(int32 Index);
    UFUNCTION() void OnTextCommitted(const FText& Text, ETextCommit::Type How);
    void RefreshOptions();
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> TextPanel;
    UPROPERTY(Transient) TObjectPtr<class UEditableTextBox> TextBox;
    TArray<bool> AsksText;
    FName TextKey;
    int32 SuggestSeed = 0;
    /** The last choice came from a controller: the name box keeps the window's focus so A, X and B work. */
    bool bChosenByPad = false;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> TextPrompt;
    UPROPERTY(Transient) TObjectPtr<UEWRecipeButton> SuggestButton;
    TArray<FText> Prompts;
    TArray<bool> Suggests;
    bool bTextSuggests = false;
    TWeakObjectPtr<AEWTownsfolk> Speaker;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> LineText;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> OptionList;
    UPROPERTY(Transient) TArray<TObjectPtr<UEWRecipeButton>> Buttons;
    TArray<FName> Keys;
    TArray<bool> Enabled;
    TArray<FString> ShownLabels;
    int32 Cursor = 0;
    float RefreshClock = 0.f;
};
