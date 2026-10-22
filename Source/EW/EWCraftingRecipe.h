#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EWCraftingRecipe.generated.h"

class UEWItemDefinition;

USTRUCT(BlueprintType)
struct FEWCraftingIngredient
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    TObjectPtr<UEWItemDefinition> Item = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1"))
    int32 Quantity = 1;
};

/** Exact-item recipes; species substitution must be explicitly authored later. */
UCLASS(BlueprintType)
class EW_API UEWCraftingRecipe : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    TArray<FEWCraftingIngredient> Ingredients;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    TObjectPtr<UEWItemDefinition> Output = nullptr;
    /** Seconds the work takes (owner, October 22: crafting takes several seconds). Materials are used up only when it finishes. Cooking is 5 to 12 s by recipe. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Crafting", meta=(ClampMin="0"))
    float CraftSeconds = 4.f;
};
