#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWForest.generated.h"

class AEWCharacter;
class AEWHarvestTree;
class UEWItemDefinition;
class UHierarchicalInstancedStaticMeshComponent;

/** A stand of one tree model on one island, drawn as instances so whole forests stay cheap (owner, November 6: dense,
 *  varied forests with open ground). Every instance is a real tree: the first hatchet blow on one replaces it with an
 *  AEWHarvestTree in the same place, size and lean, which then works, falls and fades exactly like any other tree.
 *  The instance stays hidden until it regrows (RegrowSeconds, CLAUDE.md 5.4), unless something stands in its place.
 *  Instances are laid out in the editor by Scripts/Setup/build_forests.py. Trunks block survivors and animals through a
 *  hidden cylinder per tree; the leaves never do. Which trees are down is replicated; it is not saved yet (a reload
 *  regrows them all). */
UCLASS()
class EW_API AEWForest : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWForest();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** The trees as drawn: aimed at by the Visibility trace, no physical collision. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Forest") TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Trees;
    /** One hidden upright cylinder per tree, the solid trunk (same index as Trees). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Forest") TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Trunks;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Forest") TObjectPtr<UEWItemDefinition> Wood;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Forest") TObjectPtr<UEWItemDefinition> Thatch;
    /** The trunk at scale 1 (cm), for this model; each tree's own scale widens and heightens it. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Forest") float TrunkRadius = 30.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Forest") float TrunkHalfHeight = 220.f;
    /** Wood and thatch in a tree at scale 1; a bigger tree holds more (girth squared times height), within the clamps. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Forest") int32 BaseWood = 12;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Forest") int32 BaseThatch = 4;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Forest|Tuning") float RegrowSeconds = 1200.f;

    /** Authority: the tree the survivor is aiming at, as a harvestable actor, or null when they aim at none of this
     *  stand's standing trees. */
    AEWHarvestTree* PromoteAimed(AEWCharacter* Survivor);
    /** Authority: replace instance Index with a harvestable tree. */
    AEWHarvestTree* Promote(int32 Index);
    UFUNCTION(BlueprintPure, Category="Forest") int32 GetTreeCount() const;
    UFUNCTION(BlueprintPure, Category="Forest") bool IsStanding(int32 Index) const { return !Removed.Contains(Index); }
    UFUNCTION(BlueprintPure, Category="Forest") int32 GetDownCount() const { return Removed.Num(); }
    /** Editor and tests: the tree's place, rotation and scale as authored. */
    UFUNCTION(BlueprintPure, Category="Forest") FTransform GetTreeTransform(int32 Index) const;
    /** Tests: let every felled tree regrow now (if nothing stands in its place). */
    UFUNCTION(BlueprintCallable, Category="Forest") void RegrowAllNow();

    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override { return false; }
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override { return false; }

private:
    UPROPERTY(ReplicatedUsing=OnRep_Removed) TArray<int32> Removed;
    TMap<int32, double> RemovedAt;
    TSet<int32> Hidden;
    TArray<FTransform> Authored;
    double NextRegrowCheck = 0.0;
    UFUNCTION() void OnRep_Removed();
    void CaptureAuthored();
    void ShowInstance(int32 Index, bool bShow);
    void SyncHidden();
    bool PlaceIsClear(int32 Index) const;
};
