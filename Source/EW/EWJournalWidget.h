#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Engine/DataAsset.h"
#include "EWJournalWidget.generated.h"
class UTextBlock;
class UVerticalBox;
class UButton;

/** One Journal page: a guide to some part of play. */
USTRUCT(BlueprintType)
struct FEWJournalEntry
{
    GENERATED_BODY()
    /** Groups pages in the list, such as "Ships" or "The coast". */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Journal")
    FText Section;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Journal")
    FText Title;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Journal", meta=(MultiLine=true))
    FText Body;
};

/** The pages the Journal shows, in order. */
UCLASS(BlueprintType)
class EW_API UEWJournalData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Journal")
    TArray<FEWJournalEntry> Entries;
};

/** The menu's Journal section: the list of pages on the left, the chosen page on the right. Read-only and local. */
UCLASS()
class EW_API UEWJournalWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    /** The pages shown. Until the Quartermaster's guidance is written, this is the playtest guide. */
    UPROPERTY(EditAnywhere, Category="Journal")
    TSoftObjectPtr<UEWJournalData> Journal = TSoftObjectPtr<UEWJournalData>(FSoftObjectPath(TEXT("/Game/Elitewake/Journal/DA_TestJournal.DA_TestJournal")));
    UFUNCTION(BlueprintPure, Category="Journal")
    int32 GetSelectedPage() const { return Selected; }
    UFUNCTION(BlueprintCallable, Category="Journal")
    void ShowPage(int32 Index);
    UFUNCTION(BlueprintPure, Category="Journal")
    FText GetShownTitle() const;
    UFUNCTION(BlueprintPure, Category="Journal")
    int32 GetPageCount() const { return Pages.Num(); }
private:
    UPROPERTY(Transient) TArray<FEWJournalEntry> Pages;
    UPROPERTY(Transient) TArray<TObjectPtr<UButton>> PageButtons;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PageTitle;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PageBody;
    int32 Selected = INDEX_NONE;
};
