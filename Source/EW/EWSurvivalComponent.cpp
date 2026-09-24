// Copyright Elite Game Labs. All Rights Reserved.

#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"

UEWSurvivalComponent::UEWSurvivalComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void UEWSurvivalComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UEWSurvivalComponent, MaxHealth);
	DOREPLIFETIME(UEWSurvivalComponent, Health);
	DOREPLIFETIME(UEWSurvivalComponent, MaxStamina);
	DOREPLIFETIME(UEWSurvivalComponent, Stamina);
	DOREPLIFETIME(UEWSurvivalComponent, Hunger);
	DOREPLIFETIME(UEWSurvivalComponent, Hydration);
	DOREPLIFETIME(UEWSurvivalComponent, BodyTemperatureCelsius);
	DOREPLIFETIME(UEWSurvivalComponent, CarriedWeight);
	DOREPLIFETIME(UEWSurvivalComponent, MaxCarryWeight);
}

void UEWSurvivalComponent::UpdateStamina(bool bIsSprinting, float DeltaSeconds)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || DeltaSeconds <= 0.0f)
	{
		return;
	}

	const float PreviousStamina = Stamina;
	const float Delta = bIsSprinting
		? -SprintStaminaDrainRate * DeltaSeconds
		: StaminaRecoveryRate * DeltaSeconds;
	Stamina = FMath::Clamp(Stamina + Delta, 0.0f, MaxStamina);

	if (!FMath::IsNearlyEqual(PreviousStamina, Stamina))
	{
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::ApplyDamage(float DamageAmount)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || DamageAmount <= 0.0f)
	{
		return;
	}

	Health = FMath::Clamp(Health - DamageAmount, 0.0f, MaxHealth);
	NotifyStatsChanged();
}

void UEWSurvivalComponent::RestoreHealth(float RestoreAmount)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || RestoreAmount <= 0.0f)
	{
		return;
	}

	Health = FMath::Clamp(Health + RestoreAmount, 0.0f, MaxHealth);
	NotifyStatsChanged();
}

void UEWSurvivalComponent::SetHunger(float NewHunger)
{
	if (GetOwner() && GetOwner()->HasAuthority())
	{
		Hunger = FMath::Clamp(NewHunger, 0.0f, 100.0f);
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::SetHydration(float NewHydration)
{
	if (GetOwner() && GetOwner()->HasAuthority())
	{
		Hydration = FMath::Clamp(NewHydration, 0.0f, 100.0f);
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::SetBodyTemperature(float NewBodyTemperatureCelsius)
{
	if (GetOwner() && GetOwner()->HasAuthority())
	{
		BodyTemperatureCelsius = NewBodyTemperatureCelsius;
		NotifyStatsChanged();
	}
}

void UEWSurvivalComponent::SetCarriedWeight(float NewCarriedWeight)
{
	if (GetOwner() && GetOwner()->HasAuthority())
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
