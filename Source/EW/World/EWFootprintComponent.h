#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWFootprintComponent.generated.h"

class UDecalComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;

/** What the ground under a footstep is, which decides how long its print lasts. */
UENUM(BlueprintType)
enum class EEWFootSurface : uint8
{
    Firm,   // grass and packed earth: the print fades within a few seconds
    Snow,   // Winter's snow: prints stay
    Mud,    // the Swamp's mud: prints stay
    Sand    // Desert sand and every island's beaches: prints stay
};

/**
 * A survivor's footprints (owner, October 26: black footprints on the Plains and on each island according to its weather,
 * so the player can retrace their steps for a moment). Every walking character leaves one print per stride, left and
 * right in turn, as a decal on the ground. On firm ground a print fades away in a few seconds. In snow, mud and sand a print
 * stays, but only the last six: each new print makes the oldest vanish, one at a time. Visual only; nothing is replicated
 * and a dedicated server makes none. Durations and sizes are tuning.
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class EW_API UEWFootprintComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWFootprintComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** The surface at a world location: snow in the Winter region, mud in the Swamp, sand in the Desert and on any beach. */
    static EEWFootSurface SurfaceAt(const UObject* WorldContext, const FVector& Location);

    /** How many prints are showing, and how many of those stay (for the checks). */
    UFUNCTION(BlueprintPure, Category="Footprints") int32 GetPrintCount() const { return Prints.Num(); }
    UFUNCTION(BlueprintPure, Category="Footprints") int32 GetLastingPrintCount() const;
    UFUNCTION(BlueprintPure, Category="Footprints") int32 GetPrintsMade() const { return PrintsMade; }
    UFUNCTION(BlueprintPure, Category="Footprints") EEWFootSurface GetLastSurface() const { return LastSurface; }

    /** Tuning. */
    static constexpr int32 MaxLastingPrints = 6;
    static constexpr float FirmFadeSeconds = 3.5f;
    static constexpr float LastingSeconds = 90.f;
    static constexpr float VanishSeconds = .5f;

private:
    struct FPrint
    {
        TWeakObjectPtr<UDecalComponent> Decal;
        TWeakObjectPtr<UMaterialInstanceDynamic> Material;
        float Age = 0.f;
        float Lifetime = 0.f;       // seconds until it has gone
        float Vanishing = -1.f;     // time left of a quick fade-out, once pushed out by newer prints
        bool bLasting = false;
        float Opacity = 1.f;
    };
    TArray<FPrint> Prints;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PrintMaterial;
    FVector LastPrintAt = FVector::ZeroVector;
    bool bHavePrint = false;
    bool bRightFoot = false;
    int32 PrintsMade = 0;
    EEWFootSurface LastSurface = EEWFootSurface::Firm;

    void MakePrint();
    void UpdatePrints(float DeltaSeconds);
};
