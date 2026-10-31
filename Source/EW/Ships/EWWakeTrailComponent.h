#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWWakeTrailComponent.generated.h"

class AEWShip;
class UInstancedStaticMeshComponent;

/**
 * The foam a ship leaves on the water (owner, October 16: a realistic, foamy, turbulent wake about 20 m behind a ship
 * moving forward, following its path and its shape, fading after it stops; see CLAUDE.md). Every machine lays its own:
 * as the ship makes way, a patch of churned foam is set on the sea at its
 * stern each metre; the patches stay where they were laid, so the trail follows every turn, spread wider as they age
 * and fade out over the last TrailLength of the ship's track, or a few seconds after it stops. Width scales with the
 * hull's beam and strength with speed. Sizes and times are tuning.
 */
UCLASS(ClassGroup=(Ship))
class EW_API UEWWakeTrailComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWWakeTrailComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    static constexpr float TrailLength = 2000.f;   // cm
    static constexpr float DropSpacing = 100.f;    // cm of travel between patches
    static constexpr float StopFadeSeconds = 4.f;

    /** For the checks: how many patches lie on the water now, and how far behind the stern the farthest one is (cm). */
    UFUNCTION(BlueprintPure, Category="Ship|Wake") int32 GetPatchCount() const { return Patches.Num(); }
    UFUNCTION(BlueprintPure, Category="Ship|Wake") float GetTrailReach() const;
    /** Where a patch lies (world), for the checks; index 0 is the oldest. */
    UFUNCTION(BlueprintPure, Category="Ship|Wake") FVector GetPatchLocation(int32 Index) const;

private:
    struct FPatch { FVector At; float Yaw = 0.f; float DroppedAt = 0.f; float Strength = 0.f; };
    TArray<FPatch> Patches;
    UPROPERTY(Transient) TObjectPtr<UInstancedStaticMeshComponent> Foam;
    float Travelled = 0.f;
    float SinceDrop = 0.f;
    /** Seconds since the last patch was laid: once the ship stops, the whole trail fades out. */
    float SinceLastPatch = 0.f;
    FVector LastStern = FVector::ZeroVector;
    bool bHasLast = false;
    AEWShip* Ship() const;
    FVector Stern(const AEWShip* S) const;
    void Redraw(float Beam);
};
