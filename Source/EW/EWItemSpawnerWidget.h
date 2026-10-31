#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWItemSpawnerWidget.generated.h"
class UBorder;
class UScrollBox;
class UTextBlock;
class UEWItemDefinition;

/**
 * F9's item spawner (testing only, owner, October 30): every item that has a crafting recipe, then every other item, as tiles with
 * their icons. A click, or A on the tile the controller's cursor is on, gives the survivor one of it (the server adds it to their
 * pack). The d-pad or left stick moves the cursor; B, F9 or Escape closes. Not in shipping builds.
 */
UCLASS()
class EW_API UEWItemSpawnerWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category="Debug") int32 GetItemCount() const { return Items.Num(); }
    UFUNCTION(BlueprintPure, Category="Debug") int32 GetCraftableCount() const { return CraftableCount; }
    UFUNCTION(BlueprintPure, Category="Debug") int32 GetCursor() const { return Cursor; }
    UFUNCTION(BlueprintPure, Category="Debug") UEWItemDefinition* GetItem(int32 Index) const { return Items.IsValidIndex(Index) ? Items[Index] : nullptr; }
    UFUNCTION(BlueprintPure, Category="Debug") FText GetStatus() const;
    /** Gives one of the item at Index (as a click on its tile). */
    UFUNCTION(BlueprintCallable, Category="Debug") void Give(int32 Index);
    /** Every item, the craftable ones (a recipe's output) first, each group by name. */
    static void GatherItems(TArray<UEWItemDefinition*>& Out, int32& OutCraftable);
    static constexpr int32 Columns = 8;
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
private:
    UFUNCTION() void TilePressed(int32 Index) { Give(Index); }
    UFUNCTION() void TileHovered(int32 Index) { MoveCursor(Index); }
    void MoveCursor(int32 Index);
    /** Row and column of a tile, counting rows on through both groups. */
    void Place(int32 Index, int32& Row, int32& Column) const;
    int32 IndexAt(int32 Row, int32 Column) const;
    UPROPERTY(Transient) TArray<TObjectPtr<UEWItemDefinition>> Items;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> Rings;
    UPROPERTY(Transient) TObjectPtr<UScrollBox> Scroll;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Status;
    int32 CraftableCount = 0;
    int32 Cursor = 0;
};
