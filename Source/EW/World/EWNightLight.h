#pragma once
#include "CoreMinimal.h"
#include "Engine/PointLight.h"
#include "EWNightLight.generated.h"

/**
 * A lamp that is lit only at night (owner, October 30: the Freeport's lanterns): a point light that checks the day-night clock
 * every second and shows itself from dusk to dawn. Every machine runs the same clock, so it needs no replication.
 */
UCLASS()
class EW_API AEWNightLight : public APointLight
{
    GENERATED_BODY()
public:
    AEWNightLight();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
};
