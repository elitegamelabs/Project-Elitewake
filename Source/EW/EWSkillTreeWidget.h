#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "EWSkillTreeWidget.generated.h"
class UBorder;
class UCanvasPanel;
class UTextBlock;
class UVerticalBox;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FEWSkillStarPressed, int32, Index);

/** A star of the tree: a button that reports itself on click and on hover. */
UCLASS()
class UEWSkillStarButton : public UButton
{
    GENERATED_BODY()
public:
    UEWSkillStarButton() { InitIsFocusable(false); }
    int32 NodeIndex = 0;
    FEWSkillStarPressed OnStarClicked;
    FEWSkillStarPressed OnStarHovered;
    void Initialize(int32 Index) { NodeIndex = Index; OnClicked.AddDynamic(this, &UEWSkillStarButton::Clicked); OnHovered.AddDynamic(this, &UEWSkillStarButton::Hovered); }
private:
    UFUNCTION() void Clicked() { OnStarClicked.Broadcast(NodeIndex); }
    UFUNCTION() void Hovered() { OnStarHovered.Broadcast(NodeIndex); }
};

/**
 * The menu's Skills section: a constellation of stars joined by lines, with a panel on the right for the star under the mouse or picked with the arrows or
 * d-pad. Lit stars are gold, stars that can be lit now are bright, the rest dim. Enter, A or the Unlock button lights the picked star with a skill point.
 */
UCLASS()
class EW_API UEWSkillTreeWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;

    UFUNCTION(BlueprintPure, Category="Skills") int32 GetSelectedNode() const { return Selected; }
    UFUNCTION(BlueprintPure, Category="Skills") FName GetSelectedId() const;
    UFUNCTION(BlueprintPure, Category="Skills") int32 GetNodeCount() const;
    UFUNCTION(BlueprintPure, Category="Skills") FText GetDetailTitle() const;
    /** The materials the picked star's recipes need, as the panel prints them. */
    UFUNCTION(BlueprintPure, Category="Skills") FText GetDetailMaterials() const;
    UFUNCTION(BlueprintPure, Category="Skills") bool IsUnlockEnabled() const;
    UFUNCTION(BlueprintCallable, Category="Skills") void SelectNode(int32 Index);
    /** Picks the nearest star in that direction (screen directions: right +X, down +Y). */
    UFUNCTION(BlueprintCallable, Category="Skills") bool MoveSelection(FVector2D Direction);
    UFUNCTION(BlueprintCallable, Category="Skills") bool UnlockSelected();
private:
    UFUNCTION() void StarClicked(int32 Index) { SelectNode(Index); }
    UFUNCTION() void StarHovered(int32 Index) { SelectNode(Index); }
    UFUNCTION() void OnUnlockClicked() { UnlockSelected(); }
    void Refresh();
    UPROPERTY(Transient) TObjectPtr<UCanvasPanel> Sky;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> Stars;
    UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> StarGlyphs;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> Lines;
    TArray<TPair<int32, int32>> LineEnds;        // child, parent node indices of each line
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Title;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Body;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Materials;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PointsLine;
    UPROPERTY(Transient) TObjectPtr<UButton> UnlockButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> UnlockLabel;
    int32 Selected = 0;
    float RefreshClock = 0.f;
};
