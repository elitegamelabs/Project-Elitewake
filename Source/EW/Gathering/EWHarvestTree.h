#pragma once
#include "CoreMinimal.h"
#include "EWStation.h"
#include "EWHarvestTree.generated.h"

class UEWItemDefinition;
class UMaterialInstanceDynamic;
class UMaterialInterface;

/** Finite tool-harvested tree. Interact never grants yields; Attack uses server equipment.
 * Bare-hand punching is disabled pending the separate injury/treatment system.
 */
UCLASS(Blueprintable)
class EW_API AEWHarvestTree : public AEWStation
{
    GENERATED_BODY()
public:
    AEWHarvestTree();
    virtual void Tick(float DeltaSeconds) override;
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
    /** Authority-only environmental knockdown. The stump pivot stays at the ground while the tree tips over. */
    UFUNCTION(BlueprintCallable, Category="Harvest") bool Fell(FVector Direction);
    UFUNCTION(BlueprintPure, Category="Harvest") bool IsFelled() const { return bFelled; }
    /** The fall style this tree uses, picked from its species (the trunk mesh name): Oak, Ash, Birch, Spruce, Palm or Default. */
    UFUNCTION(BlueprintPure, Category="Harvest") FName GetFallStyleName() const;
    /** The last strike of a hatchet: the tree tips over away from the survivor, then lies a moment and disappears. Authority only.
     *  Hits that leave wood in the tree only shake it. */
    UFUNCTION(BlueprintCallable, Category="Harvest") bool CutDown(AEWCharacter* Survivor);
    /** Tuning (owner, October 27: it stays a few seconds, then fades over 3 s): seconds a tree lies on the ground after it lands
     *  before it starts to fade, and how long the fade takes. It is removed when the fade ends. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest|Tuning", meta=(ClampMin="0")) float RemoveDelay = 4.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest|Tuning", meta=(ClampMin="0.1")) float FadeSeconds = 3.f;
    UFUNCTION(BlueprintPure, Category="Harvest") bool IsFading() const { return bFading; }
    /** 1 = solid, 0 = gone: the Fade value on the tree's materials (the tree materials dither away by it). */
    UFUNCTION(BlueprintPure, Category="Harvest") float GetFade() const { return FadeAlpha; }
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest|Tuning", meta=(ClampMin="0.1")) float FallDuration = 2.f;
    virtual void PlayHitShake(const FVector& Direction, float Degrees) override;
    /** Authority, loading a save (M7): what is left of the tree, and if it was lying where it fell, lay it there at once. */
    void RestoreSaved(int32 InWood, int32 InThatch, bool bLying, const FTransform& Where);
    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override { return false; }
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override { return false; }
private:
    bool bHarvesting = false;
    UPROPERTY(ReplicatedUsing=OnRep_Felled, BlueprintReadOnly, Category="Harvest", meta=(AllowPrivateAccess="true")) bool bFelled = false;
    FQuat FallStartRotation = FQuat::Identity;
    FQuat FallTargetRotation = FQuat::Identity;
    float FallElapsed = 0.f;
    float FallSeconds = 2.f;          // this tree's own fall time: taller trees fall slower
    float LandElapsed = 0.f;          // seconds since it came down: the landing bounce, then the wait before it goes
    FVector FallDirection = FVector::ForwardVector;
    FVector FallTipAxis = FVector::RightVector;
    float FallEase = 2.f, FallSway = 0.f, FallBounce = 0.f, FallSecondsScale = 1.f;
    bool bRemoveAfterFall = false;
    UFUNCTION() void OnRep_Felled();
    UPROPERTY(ReplicatedUsing=OnRep_Fading) bool bFading = false;
    float FadeElapsed = 0.f;
    float FadeAlpha = 1.f;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInstanceDynamic>> FadeMaterials;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInterface>> FadeTwins;      // loaded when the tree goes over, so the fade itself does not stall
    void LoadFadeTwins();
    UFUNCTION() void OnRep_Fading();
    void StartFade();
    void UpdateFade(float DeltaSeconds);
    void ConfigureFelledCollision();
};
