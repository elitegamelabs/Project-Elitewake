#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "EWWindSubsystem.generated.h"

/**
 * The world's wind. Ships read it on the server. It is constant until the weather system drives it.
 */
UCLASS()
class EW_API UEWWindSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    /** Direction the wind blows toward, as a world yaw in degrees. */
    UFUNCTION(BlueprintPure, Category="Wind")
    float GetWindYaw() const { return WindYaw; }
    UFUNCTION(BlueprintPure, Category="Wind")
    FVector GetWindDirection() const { return FRotator(0, WindYaw, 0).Vector(); }
    /** Server only. */
    UFUNCTION(BlueprintCallable, Category="Wind")
    void SetWindYaw(float NewYaw);

    /**
     * How much of a ship's sailing speed the wind allows for a given heading: 1 running straight
     * downwind, falling smoothly to MinUpwindFactor heading straight into the wind (tuning).
     */
    float GetHeadingFactor(const FVector& ShipForward) const;
    static constexpr float MinUpwindFactor = .3f;

private:
    float WindYaw = 45.f;
};
