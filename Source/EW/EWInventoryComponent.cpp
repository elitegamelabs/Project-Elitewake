// Copyright Elite Game Labs. All Rights Reserved.

#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWEquipmentComponent.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"

UEWInventoryComponent::UEWInventoryComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void UEWInventoryComponent::BeginPlay()
{
	Super::BeginPlay();

	if (GetOwner() && GetOwner()->HasAuthority())
	{
		RefreshSurvivalWeight();
	}
}

void UEWInventoryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UEWInventoryComponent, Entries);
}

int32 UEWInventoryComponent::AddItem(UEWItemDefinition* ItemDefinition, int32 Quantity)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !ItemDefinition || Quantity <= 0 || bEquipmentTransferInProgress)
	{
		return 0;
	}
    const int32 Added = AddToEntries(Entries, MaxSlots, ItemDefinition, Quantity);
    if (Added > 0) HandleInventoryChanged();
    return Added;
}

int32 UEWInventoryComponent::AddToEntries(TArray<FEWInventoryEntry>& Entries, int32 MaxSlots, UEWItemDefinition* ItemDefinition, int32 Quantity)
{
	const int32 MaxStackSize = FMath::Max(1, ItemDefinition->MaxStackSize);
	int32 Remaining = Quantity;

	for (FEWInventoryEntry& Entry : Entries)
	{
		if (Entry.ItemDefinition == ItemDefinition && Entry.Quantity < MaxStackSize)
		{
			const int32 AddedToStack = FMath::Min(Remaining, MaxStackSize - Entry.Quantity);
			Entry.Quantity += AddedToStack;
			Remaining -= AddedToStack;

			if (Remaining <= 0)
			{
				break;
			}
		}
	}

	while (Remaining > 0 && Entries.Num() < MaxSlots)
	{
		FEWInventoryEntry& NewEntry = Entries.AddDefaulted_GetRef();
		NewEntry.ItemDefinition = ItemDefinition;
		NewEntry.Quantity = FMath::Min(Remaining, MaxStackSize);
		Remaining -= NewEntry.Quantity;
	}

    return Quantity - Remaining;
}

int32 UEWInventoryComponent::RemoveItem(UEWItemDefinition* ItemDefinition, int32 Quantity)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !ItemDefinition || Quantity <= 0 || bEquipmentTransferInProgress)
	{
		return 0;
	}
    const int32 Removed = RemoveFromEntries(Entries, ItemDefinition, Quantity);
    if (Removed > 0) HandleInventoryChanged();
    return Removed;
}

int32 UEWInventoryComponent::RemoveFromEntries(TArray<FEWInventoryEntry>& Entries, UEWItemDefinition* ItemDefinition, int32 Quantity)
{
	int32 Remaining = Quantity;
	for (int32 Index = Entries.Num() - 1; Index >= 0 && Remaining > 0; --Index)
	{
		FEWInventoryEntry& Entry = Entries[Index];
		if (Entry.ItemDefinition != ItemDefinition)
		{
			continue;
		}

		const int32 RemovedFromStack = FMath::Min(Remaining, Entry.Quantity);
		Entry.Quantity -= RemovedFromStack;
		Remaining -= RemovedFromStack;

		if (Entry.Quantity <= 0)
		{
			Entries.RemoveAt(Index);
		}
	}

    return Quantity - Remaining;
}

int32 UEWInventoryComponent::GetItemCount(const UEWItemDefinition* ItemDefinition) const
{
	if (!ItemDefinition)
	{
		return 0;
	}

	int32 Total = 0;
	for (const FEWInventoryEntry& Entry : Entries)
	{
		if (Entry.ItemDefinition == ItemDefinition)
		{
			Total += Entry.Quantity;
		}
	}
	return Total;
}

bool UEWInventoryComponent::HasItem(const UEWItemDefinition* ItemDefinition, int32 Quantity) const
{
	return Quantity <= 0 || GetItemCount(ItemDefinition) >= Quantity;
}

float UEWInventoryComponent::GetTotalWeight() const
{
	float TotalWeight = 0.0f;
	for (const FEWInventoryEntry& Entry : Entries)
	{
		if (Entry.ItemDefinition && Entry.Quantity > 0)
		{
			TotalWeight += Entry.ItemDefinition->UnitWeight * Entry.Quantity;
		}
	}
	return FMath::Max(0.0f, TotalWeight);
}

void UEWInventoryComponent::OnRep_Entries()
{
	OnInventoryChanged.Broadcast();
}

void UEWInventoryComponent::HandleInventoryChanged()
{
	RefreshSurvivalWeight();
	OnInventoryChanged.Broadcast();
}

void UEWInventoryComponent::RefreshSurvivalWeight()
{
	if (AActor* Owner = GetOwner())
	{
		if (UEWSurvivalComponent* SurvivalComponent = Owner->FindComponentByClass<UEWSurvivalComponent>())
		{
            const UEWEquipmentComponent* Equipment = Owner->FindComponentByClass<UEWEquipmentComponent>();
			SurvivalComponent->SetCarriedWeight(GetTotalWeight() + (Equipment ? Equipment->GetTotalWeight() : 0.f));
		}
	}
}
