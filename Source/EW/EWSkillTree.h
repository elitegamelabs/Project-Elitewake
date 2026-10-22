// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EWSkillTree.generated.h"

class UEWCraftingRecipe;

/**
 * One star of the constellation skill tree (owner, October 22). Unlocking it spends skill points, needs the stars it hangs from, adds the recipes it names to the
 * crafting menu, and may strengthen the survivor. Positions are on the star map, 0 to 1 across and down.
 */
USTRUCT(BlueprintType)
struct EW_API FEWSkillNode
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Skill") FName Id;
    UPROPERTY(BlueprintReadOnly, Category="Skill") FText Title;
    UPROPERTY(BlueprintReadOnly, Category="Skill") FText Description;
    UPROPERTY(BlueprintReadOnly, Category="Skill") FVector2D Position = FVector2D(.5, .5);
    /** Stars that must be lit first; the lines of the constellation run from these to this one. */
    UPROPERTY(BlueprintReadOnly, Category="Skill") TArray<FName> Requires;
    /** Skill points to light it; a free star is lit from the start. */
    UPROPERTY(BlueprintReadOnly, Category="Skill") int32 Cost = 1;
    UPROPERTY(BlueprintReadOnly, Category="Skill") TArray<TSoftObjectPtr<UEWCraftingRecipe>> Recipes;
    UPROPERTY(BlueprintReadOnly, Category="Skill") float MaxHealthBonus = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Skill") float MaxStaminaBonus = 0.f;
    UPROPERTY(BlueprintReadOnly, Category="Skill") float CarryBonus = 0.f;
};

/** The working skill tree. It lives in code until the owner approves a final tree; the recipes it unlocks are data assets. */
struct EW_API FEWSkillTree
{
    static const TArray<FEWSkillNode>& Nodes();
    static const FEWSkillNode* Find(FName Id);
};
