// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "World/EWClimateRegion.h"
#include "EWSurvivalComponent.generated.h"

class FLifetimeProperty;

/** HUD state supplied by authoritative gameplay effects. */
USTRUCT(BlueprintType)
struct FEWDebuffNotice
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) FName Id;
    UPROPERTY(BlueprintReadOnly) FText Label;
    /** Negative means condition-driven; otherwise synchronized server game time. */
    UPROPERTY(BlueprintReadOnly) double ExpiresAt = -1.;
};

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
	/** Adds the falling snow (World/EWSnowfall) wherever the game is drawn; it shows only for the player's own survivor. */
	virtual void BeginPlay() override;

	/** Raised whenever a replicated or authoritative survival value changes. */
	UPROPERTY(BlueprintAssignable, Category="Survival")
	FEWOnSurvivalStatsChanged OnSurvivalStatsChanged;

    /** Authority only. Negative persists until cleared; zero clears. */
    UFUNCTION(BlueprintCallable, Category="Survival|Effects")
    void SetDebuffNotice(FName Id, FText Label, float DurationSeconds);
    UFUNCTION(BlueprintCallable, Category="Survival|Effects")
    void ClearDebuffNotice(FName Id);
    UFUNCTION(BlueprintPure, Category="Survival|Effects")
    TArray<FEWDebuffNotice> GetDebuffNotices() const { return DebuffNotices; }

	/** Advance stamina on the authority based on current sprint state. */
	void UpdateStamina(bool bIsSprinting, float DeltaSeconds);

	UFUNCTION(BlueprintCallable, Category="Survival|Health")
	void ApplyDamage(float DamageAmount);

	UFUNCTION(BlueprintCallable, Category="Survival|Health")
	void RestoreHealth(float RestoreAmount);

	/** True once health has run out; the survivor stays dead until the server revives them (owner, October 22: death and respawn). */
	UFUNCTION(BlueprintPure, Category="Survival|Health")
	bool IsDead() const { return Health <= KINDA_SMALL_NUMBER; }
	/** Authority only. Brings a dead survivor back: health to the given fraction, and hunger, thirst and stamina to at least the given fraction of full. */
	UFUNCTION(BlueprintCallable, Category="Survival|Health")
	void Revive(float HealthFraction = 1.f, float MinNeedFraction = .5f);
	/** Authority only. What the stat points add (owner, October 22): to maximum health, stamina and carry weight, and the fraction of cold and heat damage turned aside. A
	 *  raised maximum health also heals by the amount it grew. Safe to call again with new totals. */
	void SetStatBonuses(float MaxHealthBonus, float MaxStaminaBonus, float MaxCarryBonus, float ClimateResistance);
	/** Counts every hit of a point or more (smaller ones add up first), so a HUD can flash once per hit; LastDamageAmount is that hit's size. */
	UFUNCTION(BlueprintPure, Category="Survival|Health")
	int32 GetDamageEventCount() const { return DamageEventCount; }
	UFUNCTION(BlueprintPure, Category="Survival|Health")
	float GetLastDamageAmount() const { return LastDamageAmount; }

	UFUNCTION(BlueprintCallable, Category="Survival|Needs")
	void SetHunger(float NewHunger);

	/** Authority: a step of time on the needs (owner, October 22). Hunger empties in about 45 minutes and thirst in about 25 of ordinary activity; sprinting, heat and
	 *  cold quicken them and food sickness quickens thirst. At zero, health falls gradually. Also counts food sickness down. */
	UFUNCTION(BlueprintCallable, Category="Survival|Needs")
	void UpdateNeeds(bool bIsSprinting, float DeltaSeconds);
	/** Authority: food sickness for this long (default three minutes). It never kills by itself. */
	UFUNCTION(BlueprintCallable, Category="Survival|Needs")
	void ContractFoodSickness(float Seconds = 180.f);
	UFUNCTION(BlueprintCallable, Category="Survival|Needs")
	void CureFoodSickness();
	UFUNCTION(BlueprintPure, Category="Survival|Needs")
	bool IsFoodSick() const { return FoodSicknessLeft > 0.f; }
	UFUNCTION(BlueprintPure, Category="Survival|Needs")
	float GetFoodSicknessLeft() const { return FoodSicknessLeft; }
	/** Authority: a step of time on the body's own mending (Phase 1 slice 4: recovery from injury). Fed and watered (both at
	 *  WellFedAbove or more), free of food sickness and unhurt for HurtPause seconds, health slowly comes back; resting by a lit
	 *  fire (bByFire) it comes back FireMendFactor times as fast. */
	UFUNCTION(BlueprintCallable, Category="Survival|Health")
	void UpdateRecovery(bool bByFire, float DeltaSeconds);
	static constexpr float MendSeconds = 15.f * 60.f;   // s from empty to full health, fed and watered (tuning)
	static constexpr float FireMendFactor = 3.f;        // by a lit fire: full in five minutes (tuning)
	static constexpr float WellFedAbove = 40.f;         // hunger and thirst at or above this let the body mend (tuning)
	static constexpr float HurtPause = 10.f;            // s after any hurt before mending starts, so a fight is not healed mid-way

	/** Working rules from the owner's design decisions of October 22. */
	static constexpr float HungerEmptySeconds = 45.f * 60.f;
	static constexpr float ThirstEmptySeconds = 25.f * 60.f;
	static constexpr float SprintNeedFactor = 1.5f;     // exertion
	static constexpr float HotThirstFactor = 1.5f;      // overheating
	static constexpr float ColdHungerFactor = 1.3f;     // freezing
	static constexpr float SickThirstFactor = 1.5f;     // food sickness: thirst depletion +50%
	static constexpr float SickStaminaFactor = .7f;     // food sickness: stamina regeneration -30%
	static constexpr float StarvationDamage = .25f;     // health per second at zero hunger
	static constexpr float DehydrationDamage = .35f;    // health per second at zero thirst

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
	/** The climate where the survivor is, and the temperature they feel (the water's when swimming). */
	UFUNCTION(BlueprintPure, Category="Survival|Temperature")
	FEWClimate GetClimate() const { return Climate; }
	UFUNCTION(BlueprintPure, Category="Survival|Temperature")
	float GetFeltTemperature() const { return FeltTemperature; }
	/** Where body temperature is heading in this climate, with this clothing. */
	UFUNCTION(BlueprintPure, Category="Survival|Temperature")
	float GetTargetBodyTemperature() const { return TargetBodyTemperature; }
	UFUNCTION(BlueprintPure, Category="Survival|Temperature")
	bool IsFreezing() const { return BodyTemperatureCelsius <= FreezingBelow; }
	UFUNCTION(BlueprintPure, Category="Survival|Temperature")
	bool IsOverheating() const { return BodyTemperatureCelsius >= OverheatingAbove; }
	/** Authority: a step of time in this climate. Cold below comfort pulls the body down, and clothing
	 *  (Insulation) holds it up; heat in humid air with clothing on pushes it up. Freezing and overheating harm. */
	void UpdateClimate(const FEWClimate& Here, bool bInWater, float Insulation, float DeltaSeconds, float HeatMultiplier = 1.f);
    /** The armor heat multiplier last applied while overheating (for checks). */
    UFUNCTION(BlueprintPure, Category="Survival|Temperature") float GetLastHeatMultiplier() const { return LastHeatMultiplier; }
    float LastHeatMultiplier = 1.f;

	/** Working climate rules (tuning; the owner's thresholds and damage rates are open). */
	static constexpr float NormalBody = 37.f;
	static constexpr float ComfortLow = 12.f;       // felt C below which the body cools
	static constexpr float ComfortHigh = 27.f;      // felt C above which clothing traps heat
	static constexpr float ColdPull = .14f;         // body C lost per felt C below comfort, unclothed
	static constexpr float WaterChill = 1.6f;       // water draws heat away this much faster than air
	static constexpr float WarmthPerInsulation = 22.f;  // felt C of cold that one unit of insulation answers
	static constexpr float HeatPush = .09f;         // body C gained per felt C above comfort, per unit of insulation, at full humidity
	static constexpr float BodyRate = .05f;         // body C per second toward where it is heading
	static constexpr float FreezingBelow = 35.f;
	static constexpr float OverheatingAbove = 39.f;
	static constexpr float FreezeDamage = .6f;      // health per second while freezing
	static constexpr float HeatDamage = .3f;        // health per second while overheating

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

	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Temperature")
	FEWClimate Climate;
	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Temperature")
	float FeltTemperature = 22.0f;
	UPROPERTY(VisibleInstanceOnly, ReplicatedUsing=OnRep_SurvivalStats, Category="Survival|Temperature")
	float TargetBodyTemperature = 37.0f;

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
    /** Server only: seconds of food sickness left. */
    float FoodSicknessLeft = 0.f;
    UPROPERTY(ReplicatedUsing=OnRep_SurvivalStats)
    TArray<FEWDebuffNotice> DebuffNotices;
    friend class UEWInventoryComponent;
    UPROPERTY(ReplicatedUsing=OnRep_SurvivalStats)
    int32 StaminaExhaustionCount = 0;
    UPROPERTY(ReplicatedUsing=OnRep_SurvivalStats)
    int32 DamageEventCount = 0;
    UPROPERTY(Replicated)
    float LastDamageAmount = 0.f;
    float PendingSmallDamage = 0.f;
    /** Server only: seconds since the last hurt of any kind (mending waits for HurtPause). */
    float SinceHurt = HurtPause;
    float BaseMaxHealth = -1.f, BaseMaxStamina = -1.f, BaseMaxCarry = -1.f;
    float ClimateResistance = 0.f;
	void NotifyStatsChanged();
};
