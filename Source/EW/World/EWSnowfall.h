#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWSnowfall.generated.h"

class UStaticMeshComponent;

/**
 * Snow falling round the survivor in the Winter region (owner: winter snow). Only for the player's own view: a field
 * of flakes (SM_Snowfall_v1, made by Scripts/Setup/build_snowfall.py) kept centred on the camera, whose material
 * makes them fall and drift and wraps them round the camera so the snow never runs out. Nothing is replicated: each
 * machine shows it for its own survivor from the replicated climate. Under a roof of any kind (a cave, a Port
 * building) the snow stops. DECIDED (delegated): it always snows in the Winter region until weather exists.
 */
UCLASS(ClassGroup=(Elitewake))
class EW_API UEWSnowfallComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWSnowfallComponent();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UFUNCTION(BlueprintPure, Category="Weather")
    bool IsSnowing() const { return bSnowing; }

private:
    bool ShouldSnow() const;
    bool UnderCover(const FVector& Eye) const;

    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Flakes;
    bool bSnowing = false;
    float CoverCheckIn = 0.f;
    bool bCovered = false;
};
