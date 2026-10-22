// Copyright Elite Game Labs. All Rights Reserved.

#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
#include "World/EWSnowfall.h"

void UEWSurvivalComponent::SetDebuffNotice(FName Id, FText Label, float DurationSeconds)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || Id.IsNone() || !FMath::IsFinite(DurationSeconds)) return;
    if (DurationSeconds==0.f || Label.IsEmpty()) { ClearDebuffNotice(Id);return; }
    if (DurationSeconds>0.f && !GetWorld()) return;
    FEWDebuffNotice* Notice=DebuffNotices.FindByPredicate([Id](const FEWDebuffNotice& N){ return N.Id==Id; });
    if (!Notice) Notice=&DebuffNotices.AddDefaulted_GetRef();
    Notice->Id=Id;Notice->Label=Label;
    Notice->ExpiresAt=DurationSeconds<0.f ? -1. : GetWorld()->GetTimeSeconds()+DurationSeconds;
    NotifyStatsChanged();
}
void UEWSurvivalComponent::ClearDebuffNotice(FName Id)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    if (DebuffNotices.RemoveAll([Id](const FEWDebuffNotice& N){return N.Id==Id;})>0) NotifyStatsChanged();
}

UEWSurvivalComponent::UEWSurvivalComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void UEWSurvivalComponent::BeginPlay()
{
	Super::BeginPlay();
	AActor* Owner = GetOwner();
	if (Owner && GetNetMode() != NM_DedicatedServer && !Owner->FindComponentByClass<UEWSnowfallComponent>())
	{
		UEWSnowfallComponent* Snow = NewObject<UEWSnowfallComponent>(Owner, TEXT("Snowfall"));
		Snow->RegisterComponent();
	}
}

void UEWSurvivalComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UEWSurvivalComponent, MaxHealth);
    DOREPLIFETIME_CONDITION(UEWSurvivalComponent, DebuffNotices, COND_OwnerOnly);
	DOREPLIFETIME(UEWSurvivalComponent, Health);
	DOREPLIFETIME(UEWSurvivalComponent, MaxStamina);
    DOREPLIFETIME_CONDITION(UEWSurvivalComponent, StaminaExhaustionCount, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWSurvivalComponent, DamageEventCount, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWSurvivalComponent, LastDamageAmount, COND_OwnerOnly);
	DOREPLIFETIME(UEWSurvivalComponent, Stamina);
	DOREPLIFETIME(UEWSurvivalComponent, Hunger);
	DOREPLIFETIME(UEWSurvivalComponent, Hydration);
	DOREPLIFETIME(UEWSurvivalComponent, BodyTemperatureCelsius);
	DOREPLIFETIME(UEWSurvivalComponent, Climate);
	DOREPLIFETIME(UEWSurvivalComponent, FeltTemperature);
	DOREPLIFETIME(UEWSurvivalComponent, TargetBodyTemperature);
	DOREPLIFETIME(UEWSurvivalComponent, CarriedWeight);
	DOREPLIFETIME(UEWSurvivalComponent, MaxCarryWeight);
}

void UEWSurvivalComponent::UpdateStamina(bool bIsSprinting, float DeltaSeconds)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f)
	{
		return;
	}

	const float PreviousStamina = Stamina;
	const float Delta = bIsSprinting
		? -SprintStaminaDrainRate * DeltaSeconds
		: StaminaRecoveryRate * DeltaSeconds;
	Stamina = FMath::Clamp(Stamina + Delta, 0.0f, MaxStamina);
    if (PreviousStamina > KINDA_SMALL_NUMBER && Stamina <= KINDA_SMALL_NUMBER)
        StaminaExhaustionCount = StaminaExhaustionCount == MAX_int32 ? 0 : StaminaExhaustionCount + 1;

	if (!FMath::IsNearlyEqual(PreviousStamina, Stamina))
	{
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::ApplyDamage(float DamageAmount)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !FMath::IsFinite(DamageAmount) || DamageAmount <= 0.0f)
	{
		return;
	}

	const float Before = Health;
	Health = FMath::Clamp(Health - DamageAmount, 0.0f, MaxHealth);
	// One flash per hit of a point or more; the slow drain of cold or hunger adds up until it is worth showing.
	PendingSmallDamage += Before - Health;
	if (PendingSmallDamage >= 1.f || (Health <= KINDA_SMALL_NUMBER && PendingSmallDamage > 0.f))
	{
		LastDamageAmount = PendingSmallDamage;
		PendingSmallDamage = 0.f;
		DamageEventCount = DamageEventCount == MAX_int32 ? 1 : DamageEventCount + 1;
	}
	NotifyStatsChanged();
}

void UEWSurvivalComponent::SetStatBonuses(float MaxHealthBonus, float MaxStaminaBonus, float MaxCarryBonus, float InClimateResistance)
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) return;
	if (BaseMaxHealth < 0.f) { BaseMaxHealth = MaxHealth; BaseMaxStamina = MaxStamina; BaseMaxCarry = MaxCarryWeight; }
	const float NewMaxHealth = BaseMaxHealth + FMath::Max(0.f, MaxHealthBonus);
	if (NewMaxHealth > MaxHealth && !IsDead()) Health += NewMaxHealth - MaxHealth;
	MaxHealth = NewMaxHealth;
	Health = FMath::Min(Health, MaxHealth);
	const float NewMaxStamina = BaseMaxStamina + FMath::Max(0.f, MaxStaminaBonus);
	if (NewMaxStamina > MaxStamina) Stamina += NewMaxStamina - MaxStamina;
	MaxStamina = NewMaxStamina;
	Stamina = FMath::Min(Stamina, MaxStamina);
	MaxCarryWeight = BaseMaxCarry + FMath::Max(0.f, MaxCarryBonus);
	ClimateResistance = FMath::Clamp(InClimateResistance, 0.f, .9f);
	NotifyStatsChanged();
}

void UEWSurvivalComponent::Revive(float HealthFraction, float MinNeedFraction)
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) return;
	Health = FMath::Clamp(MaxHealth * FMath::Clamp(HealthFraction, .01f, 1.f), 1.f, MaxHealth);
	const float Floor = FMath::Clamp(MinNeedFraction, 0.f, 1.f) * 100.f;
	Hunger = FMath::Max(Hunger, Floor);
	Hydration = FMath::Max(Hydration, Floor);
	Stamina = FMath::Max(Stamina, MaxStamina * FMath::Clamp(MinNeedFraction, 0.f, 1.f));
	BodyTemperatureCelsius = NormalBody;
	PendingSmallDamage = 0.f;
	NotifyStatsChanged();
}

void UEWSurvivalComponent::RestoreHealth(float RestoreAmount)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !FMath::IsFinite(RestoreAmount) || RestoreAmount <= 0.0f)
	{
		return;
	}

	Health = FMath::Clamp(Health + RestoreAmount, 0.0f, MaxHealth);
	NotifyStatsChanged();
}

void UEWSurvivalComponent::SetHunger(float NewHunger)
{
	if (GetOwner() && GetOwner()->HasAuthority() && FMath::IsFinite(NewHunger))
	{
		Hunger = FMath::Clamp(NewHunger, 0.0f, 100.0f);
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::SetHydration(float NewHydration)
{
	if (GetOwner() && GetOwner()->HasAuthority() && FMath::IsFinite(NewHydration))
	{
		Hydration = FMath::Clamp(NewHydration, 0.0f, 100.0f);
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::UpdateClimate(const FEWClimate& Here, bool bInWater, float Insulation, float DeltaSeconds)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || DeltaSeconds <= 0.f) return;
    const bool bRegionChanged = Climate.Region != Here.Region;
    Climate = Here;
    FeltTemperature = bInWater ? Here.WaterTemperature : Here.AirTemperature;
    // Cold: the shortfall below comfort that clothing does not answer pulls the body down; water pulls harder.
    const float Shortfall = FMath::Max(0.f, ComfortLow - FeltTemperature - Insulation * WarmthPerInsulation);
    // Heat: in hot, humid air, clothing traps heat; bare skin keeps cool (owner: removing clothing relieves it).
    const float Excess = FMath::Max(0.f, FeltTemperature - ComfortHigh);
    TargetBodyTemperature = NormalBody - Shortfall * ColdPull * (bInWater ? WaterChill : 1.f)
        + Excess * HeatPush * Insulation * Here.Humidity / 100.f;
    BodyTemperatureCelsius = FMath::FInterpConstantTo(BodyTemperatureCelsius, TargetBodyTemperature, DeltaSeconds, BodyRate);
    if (IsFreezing()) ApplyDamage(FreezeDamage * DeltaSeconds * (1.f - ClimateResistance));
    if (IsOverheating()) ApplyDamage(HeatDamage * DeltaSeconds * (1.f - ClimateResistance));
    // The condition notices, held while they last.
    auto Notice = [this](FName Id, bool bOn, const FText& Label)
    {
        const bool bShown = DebuffNotices.ContainsByPredicate([Id](const FEWDebuffNotice& N) { return N.Id == Id; });
        if (bOn && !bShown) SetDebuffNotice(Id, Label, -1.f);
        else if (!bOn && bShown) ClearDebuffNotice(Id);
    };
    Notice(TEXT("Freezing"), IsFreezing(), NSLOCTEXT("Elitewake", "Freezing", "Freezing: find warmth or warm clothing"));
    Notice(TEXT("Cold"), !IsFreezing() && TargetBodyTemperature < NormalBody - .5f,
        NSLOCTEXT("Elitewake", "Cold", "Cold: your body is cooling"));
    Notice(TEXT("Overheating"), IsOverheating(), NSLOCTEXT("Elitewake", "Overheating", "Overheating: remove clothing or find cooler air"));
    Notice(TEXT("Warming"), !IsOverheating() && TargetBodyTemperature > NormalBody + .5f,
        NSLOCTEXT("Elitewake", "Warming", "Hot and humid: your body is warming"));
    NotifyStatsChanged();
    (void)bRegionChanged;
}

void UEWSurvivalComponent::SetBodyTemperature(float NewBodyTemperatureCelsius)
{
	if (GetOwner() && GetOwner()->HasAuthority() && FMath::IsFinite(NewBodyTemperatureCelsius))
	{
		BodyTemperatureCelsius = NewBodyTemperatureCelsius;
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::SetCarriedWeight(float NewCarriedWeight)
{
	if (GetOwner() && GetOwner()->HasAuthority() && FMath::IsFinite(NewCarriedWeight))
	{
		CarriedWeight = FMath::Max(0.0f, NewCarriedWeight);
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::OnRep_SurvivalStats()
{
	NotifyStatsChanged();
}

void UEWSurvivalComponent::NotifyStatsChanged()
{
	OnSurvivalStatsChanged.Broadcast();
}
