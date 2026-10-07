// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWSurvivalComponent.generated.h"

class FLifetimeProperty;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FEWOnSurvivalStatsChanged);

/**
 * Server-authoritative survival values shared by gameplay and the future HUD.
 * Values are intentionally presentation-agnostic so UI can be replaced freely.
 */
UCLASS(ClassGroup=(Elitewake), BlueprintType, Blueprintable, meta=(BlueprintSpawnableComponent))
class EW_API UEWSurvivalComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEWSurvivalComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** Raised whenever a replicated or authoritative survival value changes. */
	UPROPERTY(BlueprintAssignable, Category="Survival")
	FEWOnSurvivalStatsChanged OnSurvivalStatsChanged;

	/** Advance stamina on the authority based on current sprint state. */
	void UpdateStamina(bool bIsSprinting, float DeltaSeconds);

	UFUNCTION(BlueprintCallable, Category="Survival|Health")
	void ApplyDamage(float DamageAmount);

	UFUNCTION(BlueprintCallable, Category="Survival|Health")
	void RestoreHealth(float RestoreAmount);

	UFUNCTION(BlueprintCallable, Category="Survival|Needs")
	void SetHunger(float NewHunger);

	UFUNCTION(BlueprintCallable, Category="Survival|Needs")
	void SetHydration(float NewHydration);

	UFUNCTION(BlueprintCallable, Category="Survival|Temperature")
	void SetBodyTemperature(float NewBodyTemperatureCelsius);

	UFUNCTION(BlueprintCallable, Category="Survival|Weight")
	void SetCarriedWeight(float NewCarriedWeight);

	UFUNCTION(BlueprintPure, Category="Survival|Stamina")
	bool CanSprint() const { return Stamina > KINDA_SMALL_NUMBER; }

	UFUNCTION(BlueprintPure, Category="Survival|Health")
	float GetHealth() const { return Health; }

	UFUNCTION(BlueprintPure, Category="Survival|Health")
	float GetMaxHealth() const { return MaxHealth; }

	UFUNCTION(BlueprintPure, Category="Survival|Stamina")
	float GetStamina() const { return Stamina; }

	UFUNCTION(BlueprintPure, Category="Survival|Stamina")
	float GetMaxStamina() const { return MaxStamina; }

    /** Retained exhaustion event so an owning HUD cannot miss a brief replicated zero. */
    UFUNCTION(BlueprintPure, Category="Survival|Stamina")
    int32 GetStaminaExhaustionCount() const { return StaminaExhaustionCount; }

	UFUNCTION(BlueprintPure, Category="Survival|Needs")
	float GetHunger() const { return Hunger; }

	UFUNCTION(BlueprintPure, Category="Survival|Needs")
	float GetHydration() const { return Hydration; }

	UFUNCTION(BlueprintPure, Category="Survival|Temperature")
	float GetBodyTemperature() const { return BodyTemperatureCelsius; }

	UFUNCTION(BlueprintPure, Category="Survival|Weight")
	float GetCarriedWeight() const { return CarriedWeight; }

	UFUNCTION(BlueprintPure, Category="Survival|Weight")
	float GetMaxCarryWeight() const { return MaxCarryWeight; }

protected:
	UPROPERTY(EditDefaultsOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Health", meta=(ClampMin="1.0"))
	float MaxHealth = 100.0f;

	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Health")
	float Health = 100.0f;

	UPROPERTY(EditDefaultsOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Stamina", meta=(ClampMin="1.0"))
	float MaxStamina = 100.0f;

	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Stamina")
	float Stamina = 100.0f;

	/** Fullness percentage. Zero means starving; 100 means full. */
	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Needs", meta=(ClampMin="0.0", ClampMax="100.0"))
	float Hunger = 100.0f;

	/** Hydration percentage. Zero means dehydrated; 100 means fully hydrated. */
	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Needs", meta=(ClampMin="0.0", ClampMax="100.0"))
	float Hydration = 100.0f;

	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Temperature", meta=(Units="Celsius"))
	float BodyTemperatureCelsius = 37.0f;

	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Weight", meta=(ClampMin="0.0", Units="kg"))
	float CarriedWeight = 0.0f;

	UPROPERTY(EditDefaultsOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Weight", meta=(ClampMin="0.0", Units="kg"))
	float MaxCarryWeight = 50.0f;

	UPROPERTY(EditDefaultsOnly, Category="Survival|Stamina", meta=(ClampMin="0.0"))
	float SprintStaminaDrainRate = 15.0f;

	UPROPERTY(EditDefaultsOnly, Category="Survival|Stamina", meta=(ClampMin="0.0"))
	float StaminaRecoveryRate = 10.0f;

	UFUNCTION()
	void OnRep_SurvivalStats();

private:
    friend class UEWInventoryComponent;
    UPROPERTY(ReplicatedUsing=OnRep_SurvivalStats)
    int32 StaminaExhaustionCount = 0;
	void NotifyStatsChanged();
};
