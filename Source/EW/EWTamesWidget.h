// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWTamesWidget.generated.h"

class UBorder;
class UProgressBar;
class UTextBlock;
class UVerticalBox;

/** One tamed creature as the Tames section shows it. Taming is not in the game yet, so the list is sample data (owner, October 25). */
struct FEWTameEntry
{
    FString Name;
    FString Species;
    int32 Level = 1;
    int32 Experience = 0;
    int32 ExperienceForNext = 100;
    FString Sire, Dam;
    FString SireSire, SireDam, DamSire, DamDam;
    int32 Generation = 1;
    float Health = 0.f, Stamina = 0.f, Food = 0.f, Weight = 0.f, Attack = 0.f, Speed = 0.f;
};

/**
 * The menu's Tames section: the player's tamed creatures on the left; picking one shows its picture, its lineage and its stats and level on the right.
 * Mouse clicks, the up/down arrows or d-pad pick a creature; the picked row wears a gold ring.
 */
UCLASS()
class EW_API UEWTamesWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual TSharedRef<SWidget> RebuildWidget() override;

    UFUNCTION(BlueprintPure, Category="Tames") int32 GetTameCount() const { return Tames.Num(); }
    UFUNCTION(BlueprintPure, Category="Tames") int32 GetSelectedTame() const { return Selected; }
    UFUNCTION(BlueprintPure, Category="Tames") FText GetShownName() const;
    UFUNCTION(BlueprintPure, Category="Tames") FText GetShownLineage() const;
    UFUNCTION(BlueprintPure, Category="Tames") FText GetShownLevel() const;
    UFUNCTION(BlueprintCallable, Category="Tames") void SelectTame(int32 Index);
    /** Up/down arrows or d-pad. */
    UFUNCTION(BlueprintCallable, Category="Tames") void MoveSelection(int32 Delta) { SelectTame(Selected + Delta); }

private:
    UFUNCTION() void RowPressed(int32 Index) { SelectTame(Index); }
    void Refresh();
    TArray<FEWTameEntry> Tames;
    int32 Selected = 0;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> Rings;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> SpeciesText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> LevelText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ImageGlyph;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ImageCaption;
    UPROPERTY(Transient) TObjectPtr<UProgressBar> ExperienceBar;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> LineageText;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> StatValues;
    UPROPERTY(Transient) TArray<TObjectPtr<UProgressBar>> StatBars;
};
