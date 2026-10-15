// Copyright Elite Game Labs. All Rights Reserved.

#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"

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

void UEWSurvivalComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UEWSurvivalComponent, MaxHealth);
    DOREPLIFETIME_CONDITION(UEWSurvivalComponent, DebuffNotices, COND_OwnerOnly);
	DOREPLIFETIME(UEWSurvivalComponent, Health);
	DOREPLIFETIME(UEWSurvivalComponent, MaxStamina);
    DOREPLIFETIME_CONDITION(UEWSurvivalComponent, StaminaExhaustionCount, COND_OwnerOnly);
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

	Health = FMath::Clamp(Health - DamageAmount, 0.0f, MaxHealth);
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
    if (IsFreezing()) ApplyDamage(FreezeDamage * DeltaSeconds);
    if (IsOverheating()) ApplyDamage(HeatDamage * DeltaSeconds);
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
