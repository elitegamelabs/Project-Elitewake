#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWItemDefinition.h"
#include "EWEquipmentComponent.generated.h"

UENUM(BlueprintType)
enum class EEWEquipmentResult : uint8
{
    Success, NotAuthority, Busy, InvalidItem, InvalidSlot, NotOwned, InventoryFull, AlreadyEquipped, EmptySlot
};

USTRUCT(BlueprintType)
struct FEWEquipmentEntry
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Equipment")
    EEWEquipmentSlot Slot = EEWEquipmentSlot::None;
    UPROPERTY(BlueprintReadOnly, Category="Equipment")
    TObjectPtr<UEWItemDefinition> ItemDefinition;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FEWOnEquipmentChanged);

/** Authoritative worn/held item units. Transfer plans commit together with inventory before notifications. */
UCLASS(ClassGroup=(Elitewake), BlueprintType, meta=(BlueprintSpawnableComponent))
class EW_API UEWEquipmentComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWEquipmentComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(BlueprintAssignable, Category="Equipment")
    FEWOnEquipmentChanged OnEquipmentChanged;
    UFUNCTION(BlueprintCallable, Category="Equipment")
    EEWEquipmentResult EquipItem(UEWItemDefinition* Item, EEWEquipmentSlot Slot);
    UFUNCTION(BlueprintCallable, Category="Equipment")
    EEWEquipmentResult UnequipItem(EEWEquipmentSlot Slot);
    UFUNCTION(BlueprintPure, Category="Equipment")
    UEWItemDefinition* GetEquippedItem(EEWEquipmentSlot Slot) const;
    /** Authority only: the item in Slot changes state where it is held (a waterskin filled or emptied); nothing
     *  moves in or out of the inventory. */
    bool ChangeEquippedState(EEWEquipmentSlot Slot, UEWItemDefinition* NewState);
    UFUNCTION(BlueprintPure, Category="Equipment")
    TArray<FEWEquipmentEntry> GetEquipmentEntries() const { return Entries; }
    UFUNCTION(BlueprintPure, Category="Equipment")
    float GetTotalWeight() const;
private:
    UPROPERTY(ReplicatedUsing=OnRep_Entries)
    TArray<FEWEquipmentEntry> Entries;
    UFUNCTION()
    void OnRep_Entries();
    bool bTransferInProgress = false;
    static bool IsValidSlot(EEWEquipmentSlot Slot);
};
