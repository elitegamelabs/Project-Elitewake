#include "EWEquipmentComponent.h"
#include "EWInventoryComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"

UEWEquipmentComponent::UEWEquipmentComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UEWEquipmentComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UEWEquipmentComponent, Entries);
}

bool UEWEquipmentComponent::IsValidSlot(EEWEquipmentSlot Slot)
{
    return Slot > EEWEquipmentSlot::None && Slot <= EEWEquipmentSlot::OffHand;
}

UEWItemDefinition* UEWEquipmentComponent::GetEquippedItem(EEWEquipmentSlot Slot) const
{
    const auto* Entry = Entries.FindByPredicate([Slot](const FEWEquipmentEntry& E) { return E.Slot == Slot; });
    return Entry ? Entry->ItemDefinition.Get() : nullptr;
}

float UEWEquipmentComponent::GetTotalWeight() const
{
    float Weight = 0.f;
    for (const auto& Entry : Entries) if (Entry.ItemDefinition) Weight += Entry.ItemDefinition->UnitWeight;
    return FMath::Max(0.f, Weight);
}

EEWEquipmentResult UEWEquipmentComponent::EquipItem(UEWItemDefinition* Item, EEWEquipmentSlot Slot)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return EEWEquipmentResult::NotAuthority;
    if (bTransferInProgress) return EEWEquipmentResult::Busy;
    if (!IsValid(Item)) return EEWEquipmentResult::InvalidItem;
    if (!IsValidSlot(Slot) || Item->EquipmentSlot != Slot) return EEWEquipmentResult::InvalidSlot;
    UEWInventoryComponent* Inventory = GetOwner()->FindComponentByClass<UEWInventoryComponent>();
    if (!Inventory || !Inventory->HasItem(Item)) return EEWEquipmentResult::NotOwned;
    if (Inventory->bEquipmentTransferInProgress) return EEWEquipmentResult::Busy;
    UEWItemDefinition* Previous = GetEquippedItem(Slot);
    if (Previous == Item) return EEWEquipmentResult::AlreadyEquipped;
    TGuardValue<bool> EquipmentGuard(bTransferInProgress, true);
    TGuardValue<bool> InventoryGuard(Inventory->bEquipmentTransferInProgress, true);
    TArray<FEWInventoryEntry> PlannedInventory = Inventory->Entries;
    if (UEWInventoryComponent::RemoveFromEntries(PlannedInventory, Item, 1) != 1) return EEWEquipmentResult::NotOwned;
    if (Previous && UEWInventoryComponent::AddToEntries(PlannedInventory, Inventory->MaxSlots, Previous, 1) != 1)
        return EEWEquipmentResult::InventoryFull;
    auto* Entry = Entries.FindByPredicate([Slot](const FEWEquipmentEntry& E) { return E.Slot == Slot; });
    if (!Entry) { Entry = &Entries.AddDefaulted_GetRef(); Entry->Slot = Slot; }
    Entry->ItemDefinition = Item;
    Inventory->Entries = MoveTemp(PlannedInventory);
    Inventory->HandleInventoryChanged(); // Both containers and carried weight are final before events.
    OnEquipmentChanged.Broadcast();
    GetOwner()->ForceNetUpdate();
    return EEWEquipmentResult::Success;
}

EEWEquipmentResult UEWEquipmentComponent::UnequipItem(EEWEquipmentSlot Slot)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return EEWEquipmentResult::NotAuthority;
    if (bTransferInProgress) return EEWEquipmentResult::Busy;
    if (!IsValidSlot(Slot)) return EEWEquipmentResult::InvalidSlot;
    UEWItemDefinition* Item = GetEquippedItem(Slot);
    if (!Item) return EEWEquipmentResult::EmptySlot;
    UEWInventoryComponent* Inventory = GetOwner()->FindComponentByClass<UEWInventoryComponent>();
    if (!Inventory) return EEWEquipmentResult::InventoryFull;
    if (Inventory->bEquipmentTransferInProgress) return EEWEquipmentResult::Busy;
    TGuardValue<bool> EquipmentGuard(bTransferInProgress, true);
    TGuardValue<bool> InventoryGuard(Inventory->bEquipmentTransferInProgress, true);
    TArray<FEWInventoryEntry> PlannedInventory = Inventory->Entries;
    if (UEWInventoryComponent::AddToEntries(PlannedInventory, Inventory->MaxSlots, Item, 1) != 1)
        return EEWEquipmentResult::InventoryFull;
    Entries.RemoveAll([Slot](const FEWEquipmentEntry& E) { return E.Slot == Slot; });
    Inventory->Entries = MoveTemp(PlannedInventory);
    Inventory->HandleInventoryChanged();
    OnEquipmentChanged.Broadcast();
    GetOwner()->ForceNetUpdate();
    return EEWEquipmentResult::Success;
}

void UEWEquipmentComponent::OnRep_Entries()
{
    OnEquipmentChanged.Broadcast();
}
