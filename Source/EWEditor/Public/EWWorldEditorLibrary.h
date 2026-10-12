#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "EWWorldEditorLibrary.generated.h"

class AWaterBody;
class UWaterWavesAsset;

/** World-building steps that Unreal's stock Python bindings cannot reach. */
UCLASS()
class EWEDITOR_API UEWWorldEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Sets a Gerstner waves asset's simple generator, rebuilds its waves and returns the highest crest in cm
     *  (negative if the asset does not use the simple Gerstner generator). The caller saves the asset. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|World")
    static float ConfigureGerstnerSwell(UWaterWavesAsset* Waves, int32 NumWaves, float MinWavelength, float MaxWavelength,
        float MinAmplitude, float MaxAmplitude, float WindAngleDeg, float SpreadDeg);

    /** Points a water body at a shared waves asset. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|World")
    static bool SetWaterBodyWaves(AWaterBody* WaterBody, UWaterWavesAsset* Waves);

    /** Lets an actor's meshes render into overlapping water zones as terrain, so water knows its depth and shore. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|World")
    static bool AddWaterTerrain(AActor* Actor);

    /** Rebuilds a water body's shape, render data and its zone's mesh and info texture; returns what the water
     *  renderer decides about it, for diagnosing water that does not draw. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|World")
    static FString RebuildWaterBody(AWaterBody* WaterBody);
};
