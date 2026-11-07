#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWShipSurgeon.generated.h"

class UStaticMeshComponent;
class AEWCharacter;

/**
 * The ship's surgeon (design reference, Ships; Milestones "Permanent ship surgeon"): always aboard, at the operating table in the
 * first deck below the weather deck. Interact pays 15 Copper and treats the survivor: 25% of their maximum health comes back
 * gradually (it never goes past the maximum). The server takes the payment and does the healing; a survivor already under treatment
 * is not charged again, and a treatment stops if they walk away or die (the Copper is not refunded: tuning).
 * The figure is a placeholder (shapes from the engine) until the owner's art; the treatment "animation" is the surgeon leaning in.
 */
UCLASS()
class EW_API AEWShipSurgeon : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWShipSurgeon();
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return EEWInteractionMode::Press; }
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** Tuning: the price of one treatment, the share of maximum health it restores, how long it takes and how far a patient may stray. */
    static constexpr int64 TreatmentCost = 15;
    static constexpr float TreatmentHealFraction = .25f;
    static constexpr float TreatmentSeconds = 10.f;
    static constexpr float TreatmentReach = 450.f;

    UFUNCTION(BlueprintPure, Category="Surgeon") bool IsTreating() const { return bTreating; }
    UFUNCTION(BlueprintPure, Category="Surgeon") bool IsTreatingCharacter(const AEWCharacter* Character) const;
    UFUNCTION(BlueprintPure, Category="Surgeon") int32 GetTreatmentsGiven() const { return TreatmentsGiven; }

private:
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Body;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> Head;
    UPROPERTY(Replicated) bool bTreating = false;
    UPROPERTY(Replicated) int32 TreatmentsGiven = 0;
    struct FPatient { TWeakObjectPtr<AEWCharacter> Who; float Left = 0.f; float RatePerSecond = 0.f; };
    TArray<FPatient> Patients;
    float LeanAlpha = 0.f;
};
