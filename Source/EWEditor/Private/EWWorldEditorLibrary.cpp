#include "EWWorldEditorLibrary.h"
#include "GerstnerWaterWaves.h"
#include "WaterBodyActor.h"
#include "WaterBodyComponent.h"
#include "WaterZoneActor.h"
#include "Materials/Material.h"
#include "WaterWaves.h"

float UEWWorldEditorLibrary::ConfigureGerstnerSwell(UWaterWavesAsset* Waves, int32 NumWaves, float MinWavelength,
    float MaxWavelength, float MinAmplitude, float MaxAmplitude, float WindAngleDeg, float SpreadDeg)
{
    auto* Gerstner = Waves ? Cast<UGerstnerWaterWaves>(Waves->GetWaterWaves()) : nullptr;
    auto* Generator = Gerstner ? Cast<UGerstnerWaterWaveGeneratorSimple>(Gerstner->GerstnerWaveGenerator) : nullptr;
    if (!Generator) return -1.f;
    Waves->Modify();
    Gerstner->Modify();
    Generator->Modify();
    Generator->NumWaves = FMath::Max(1, NumWaves);
    Generator->MinWavelength = MinWavelength;
    Generator->MaxWavelength = FMath::Max(MinWavelength, MaxWavelength);
    Generator->MinAmplitude = MinAmplitude;
    Generator->MaxAmplitude = FMath::Max(MinAmplitude, MaxAmplitude);
    Generator->WindAngleDeg = WindAngleDeg;
    Generator->DirectionAngularSpreadDeg = SpreadDeg;
    Gerstner->RecomputeWaves(false);
    Waves->MarkPackageDirty();
    return Gerstner->GetMaxWaveHeight();
}

bool UEWWorldEditorLibrary::SetWaterBodyWaves(AWaterBody* WaterBody, UWaterWavesAsset* Waves)
{
    if (!WaterBody || !Waves) return false;
    WaterBody->Modify();
    auto* Reference = NewObject<UWaterWavesAssetReference>(WaterBody, NAME_None, RF_Transactional);
    Reference->SetWaterWavesAsset(Waves);
    WaterBody->SetWaterWaves(Reference);
    return WaterBody->GetWaterWaves() == Reference;
}

FString UEWWorldEditorLibrary::RebuildWaterBody(AWaterBody* WaterBody)
{
    UWaterBodyComponent* Body = WaterBody ? WaterBody->GetWaterBodyComponent() : nullptr;
    if (!Body) return TEXT("no water body");
    FOnWaterBodyChangedParams Params;
    Params.bShapeOrPositionChanged = true;
    Params.bUserTriggered = true;
    Body->UpdateAll(Params);
    Body->UpdateWaterBodyRenderData();
    AWaterZone* Zone = Body->GetWaterZone();
    if (Zone) Zone->MarkForRebuild(EWaterZoneRebuildFlags::All);
    const UMaterialInterface* Surface = Body->GetWaterMaterial();
    const UMaterial* Base = Surface ? Surface->GetMaterial_Concurrent() : nullptr;
    return FString::Printf(TEXT("zone=%s tiles=%d mesh=%d info=%d material=%s base=%s usedWithWater=%d"),
        Zone ? *Zone->GetName() : TEXT("none"), Body->ShouldGenerateWaterMeshTile(), Body->AffectsWaterMesh(),
        Body->AffectsWaterInfo(), Surface ? *Surface->GetPathName() : TEXT("none"), Base ? *Base->GetPathName() : TEXT("none"),
        Base ? Base->bUsedWithWater : -1);
}
