#pragma once
#include "CoreMinimal.h"
#include "EWStation.h"
#include "EWHarvestTree.generated.h"

class UEWItemDefinition;

/** Finite tool-harvested tree. Interact never grants yields; Attack uses server equipment.
 * Bare-hand punching is disabled pending the separate injury/treatment system.
 */
UCLASS(Blueprintable)
class EW_API AEWHarvestTree : public AEWStation
{
    GENERATED_BODY()
public:
    AEWHarvestTree();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Harvest") TObjectPtr<UEWItemDefinition> Wood;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Harvest") TObjectPtr<UEWItemDefinition> Thatch;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="0")) int32 WoodRemaining = 12;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="0")) int32 ThatchRemaining = 4;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="1")) int32 WoodPerStrike = 3;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="1")) int32 ThatchPerStrike = 1;
    UFUNCTION(BlueprintPure, Category="Harvest") bool CanHarvest(AEWCharacter* Survivor) const;
    UFUNCTION(BlueprintPure, Category="Harvest") bool CanAccessSource(AEWCharacter* Survivor) const;
    /** Authority-only native entry; validates aim, equipment and permissions again. */
    int32 TryHarvest(AEWCharacter* Survivor);
    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override { return false; }
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override { return false; }
private:
    bool bHarvesting = false;
};
