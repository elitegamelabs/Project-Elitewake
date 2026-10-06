#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWItemDefinition.h"
#include "EWHotbarComponent.generated.h"

UENUM(BlueprintType)
enum class EEWHotbarResult : uint8
{
    Success, NotAuthority, InvalidSlot, InvalidItem, NotOwned, EmptySlot, UnsupportedAction, InventoryFull, Busy
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FEWOnHotbarChanged);

/** Eight shortcuts to owned definitions, never extra item units or storage. */
UCLASS(ClassGroup=(Elitewake), BlueprintType, meta=(BlueprintSpawnableComponent))
class EW_API UEWHotbarComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    static constexpr int32 SlotCount = 8;
    UEWHotbarComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(BlueprintAssignable, Category="Hotbar")
    FEWOnHotbarChanged OnHotbarChanged;
    /** Null clears. A definition has one binding; reassignment moves its shortcut. Authority only. */
    UFUNCTION(BlueprintCallable, Category="Hotbar")
    EEWHotbarResult BindItem(int32 Slot, UEWItemDefinition* Item);
    /** Select and attempt its implemented action. Current action is M5F equipment transfer. */
    UFUNCTION(BlueprintCallable, Category="Hotbar")
    EEWHotbarResult ActivateSlot(int32 Slot);
    UFUNCTION(BlueprintPure, Category="Hotbar")
    UEWItemDefinition* GetBoundItem(int32 Slot) const;
    UFUNCTION(BlueprintPure, Category="Hotbar")
    int32 GetSelectedSlot() const { return SelectedSlot; }
    UFUNCTION(BlueprintPure, Category="Hotbar")
    int32 GetOwnedQuantity(const UEWItemDefinition* Item) const;
private:
    UPROPERTY(ReplicatedUsing=OnRep_Hotbar)
    TArray<TObjectPtr<UEWItemDefinition>> Bindings;
    UPROPERTY(ReplicatedUsing=OnRep_Hotbar)
    int32 SelectedSlot = INDEX_NONE;
    UFUNCTION()
    void OnRep_Hotbar();
    bool bOperationInProgress = false;
};
