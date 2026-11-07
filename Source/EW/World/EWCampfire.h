#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWCampfire.generated.h"

class AEWCharacter;
class UAudioComponent;
class UPointLightComponent;
class UStaticMeshComponent;
class UEWItemDefinition;

/** A campfire as a save keeps it: where it stands and how long it would still burn (0: burnt down to a cold ring). */
USTRUCT(BlueprintType)
struct FEWSavedCampfire
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Save") FTransform Transform;
    UPROPERTY(BlueprintReadOnly, Category="Save") float FuelLeft = 0.f;
};

/**
 * A campfire a survivor laid (CLAUDE.md Phase 1, minutes 10-15: fire, then a cooked meal). Placed from the Campfire item held in
 * the hand (Left Mouse / the right trigger, where its blue ghost shows), it burns on the wood it was laid with and on any wood
 * fed to it (E / X with Wood in the pack), lighting the ground warmly round it and crackling. Recipes that need a fire
 * (UEWCraftingRecipe::bNeedsFire: the cooked dishes) can be made only within reach of a lit one. Burnt down, it is a cold ring
 * of stones until fed again. Held E / X without wood takes it up again, as the Campfire item. Server-owned and replicated; kept
 * by the world-state save (single player Save Game and the server's world save). Sizes, times and the light are tuning.
 */
UCLASS()
class EW_API AEWCampfire : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWCampfire();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    static constexpr float StartingFuel = 600.f;     // s a newly laid fire burns (tuning)
    static constexpr float FuelPerWood = 180.f;      // s one piece of wood adds (tuning)
    static constexpr float MaxFuel = 1800.f;
    static constexpr float CookReach = 300.f;        // cm from the fire a survivor may cook (tuning)
    static constexpr float PlaceReach = 350.f;       // cm from the eye a fire may be laid
    static constexpr float MaxSlopeDegrees = 22.f;
    static constexpr float ClearRadius = 70.f;       // cm the ring needs free round it
    static constexpr float TakeUpSeconds = 1.5f;
    /** The fire's light: a warm pool for night, not an orange wash over daylight (tuning; the torch is 40). */
    static constexpr float GlowCandelas = 45.f;
    static constexpr float GlowRadius = 750.f;
    /** How much of it shows while the sun is up (tuning): a fire is a night light. */
    static constexpr float DaylightShare = .15f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Ring;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Flame;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UPointLightComponent> Glow;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UAudioComponent> Crackle;
    /** What feeds it, and what taking it up gives back. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Campfire") TObjectPtr<UEWItemDefinition> FuelItem;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Campfire") TSoftObjectPtr<UEWItemDefinition> CampfireItem;

    UFUNCTION(BlueprintPure, Category="Campfire") bool IsLit() const { return bLit; }
    UFUNCTION(BlueprintPure, Category="Campfire") float GetFuelLeft() const { return FuelLeft; }
    /** Authority: sets how long it burns (0 puts it out). */
    UFUNCTION(BlueprintCallable, Category="Campfire") void SetFuel(float Seconds);

    /** True if a lit fire is within CookReach of the actor (any machine: every fire and whether it burns replicate). */
    UFUNCTION(BlueprintPure, Category="Campfire") static bool IsLitFireNear(const AActor* Actor);
    /** Where a fire would be laid from the survivor's view: true with the spot if it may go there; false with bHit and the
     *  spot if it is looked at but may not (too steep, in water, in a safe harbour, crowded), false and no hit if nowhere. */
    static bool FindPlacement(const AEWCharacter* Survivor, FTransform& Out, bool& bHit);

    FEWSavedCampfire CaptureForSave() const;
    void RestoreSaved(const FEWSavedCampfire& Saved) { SetFuel(Saved.FuelLeft); }

    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const override;
    virtual EEWInteractionMode GetInteractionModeFor_Implementation(AEWCharacter* Survivor) const override;
    virtual float GetHoldDurationFor_Implementation(AEWCharacter* Survivor) const override { return TakeUpSeconds; }
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override;

private:
    UPROPERTY(ReplicatedUsing=OnRep_Lit) bool bLit = false;
    float FuelLeft = 0.f;
    UFUNCTION() void OnRep_Lit();
    void ShowFire();
    bool HasFuelFor(const AEWCharacter* Survivor) const;
};
