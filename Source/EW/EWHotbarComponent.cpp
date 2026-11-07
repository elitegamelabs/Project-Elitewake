#include "EWHotbarComponent.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"

UEWHotbarComponent::UEWHotbarComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
    Bindings.SetNum(SlotCount);
}

void UEWHotbarComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWHotbarComponent, Bindings, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWHotbarComponent, SelectedSlot, COND_OwnerOnly);
}

UEWItemDefinition* UEWHotbarComponent::GetBoundItem(int32 Slot) const
{
    return Bindings.IsValidIndex(Slot) ? Bindings[Slot].Get() : nullptr;
}

int32 UEWHotbarComponent::GetOwnedQuantity(const UEWItemDefinition* Item) const
{
    if (!Item || !GetOwner()) return 0;
    const auto* Inventory = GetOwner()->FindComponentByClass<UEWInventoryComponent>();
    const auto* Equipment = GetOwner()->FindComponentByClass<UEWEquipmentComponent>();
    int32 Quantity = Inventory ? Inventory->GetItemCount(Item) : 0;
    if (Equipment)
        for (const auto& Entry : Equipment->GetEquipmentEntries())
            if (Entry.ItemDefinition == Item) ++Quantity;
    return Quantity;
}

EEWHotbarResult UEWHotbarComponent::BindItem(int32 Slot, UEWItemDefinition* Item)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return EEWHotbarResult::NotAuthority;
    if (Slot < 0 || Slot >= SlotCount) return EEWHotbarResult::InvalidSlot;
    if (bOperationInProgress) return EEWHotbarResult::Busy;
    if (Item && !IsValid(Item)) return EEWHotbarResult::InvalidItem;
    if (Item && GetOwnedQuantity(Item) == 0) return EEWHotbarResult::NotOwned;
    TGuardValue<bool> Guard(bOperationInProgress, true);
    for (auto& Binding : Bindings) if (Item && Binding == Item) Binding = nullptr;
    Bindings[Slot] = Item;
    SelectedSlot = Slot;
    OnHotbarChanged.Broadcast();
    GetOwner()->ForceNetUpdate();
    return EEWHotbarResult::Success;
}

EEWHotbarResult UEWHotbarComponent::ActivateSlot(int32 Slot)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return EEWHotbarResult::NotAuthority;
    if (Slot < 0 || Slot >= SlotCount) return EEWHotbarResult::InvalidSlot;
    if (bOperationInProgress) return EEWHotbarResult::Busy;
    TGuardValue<bool> Guard(bOperationInProgress, true);
    SelectedSlot = Slot;
    const auto Activate = [this, Slot]() -> EEWHotbarResult
    {
        UEWItemDefinition* Item = GetBoundItem(Slot);
        if (!Item) return EEWHotbarResult::EmptySlot;
        if (!IsValid(Item)) return EEWHotbarResult::InvalidItem;
        if (GetOwnedQuantity(Item) == 0) return EEWHotbarResult::NotOwned;
        if (Item->bFoodConsumptionEnabled)
        {
            auto* Inventory = GetOwner()->FindComponentByClass<UEWInventoryComponent>();
            if (!Inventory) return EEWHotbarResult::UnsupportedAction;
            switch (Inventory->ConsumeFood(Item))
            {
                case EEWFoodUseResult::Success: return EEWHotbarResult::Success;
                case EEWFoodUseResult::NotOwned: return EEWHotbarResult::NotOwned;
                case EEWFoodUseResult::Busy: return EEWHotbarResult::Busy;
                case EEWFoodUseResult::NoBenefit: return EEWHotbarResult::NoBenefit;
                case EEWFoodUseResult::UnavailableSurvivor: return EEWHotbarResult::UnavailableSurvivor;
                default: return EEWHotbarResult::InvalidFood;
            }
        }
        if (Item->EquipmentSlot == EEWEquipmentSlot::None) return EEWHotbarResult::UnsupportedAction;
        auto* Equipment = GetOwner()->FindComponentByClass<UEWEquipmentComponent>();
        if (!Equipment) return EEWHotbarResult::UnsupportedAction;
        if (Equipment->GetEquippedItem(Item->EquipmentSlot) == Item) return EEWHotbarResult::Success;
        switch (Equipment->EquipItem(Item, Item->EquipmentSlot))
        {
            case EEWEquipmentResult::Success: return EEWHotbarResult::Success;
            case EEWEquipmentResult::AlreadyEquipped: return EEWHotbarResult::Success;
            case EEWEquipmentResult::InventoryFull: return EEWHotbarResult::InventoryFull;
            case EEWEquipmentResult::NotOwned: return EEWHotbarResult::NotOwned;
            case EEWEquipmentResult::Busy: return EEWHotbarResult::Busy;
            default: return EEWHotbarResult::UnsupportedAction;
        }
    };
    const EEWHotbarResult Result = Activate();
    OnHotbarChanged.Broadcast();
    GetOwner()->ForceNetUpdate();
    return Result;
}

void UEWHotbarComponent::OnRep_Hotbar()
{
    OnHotbarChanged.Broadcast();
}
