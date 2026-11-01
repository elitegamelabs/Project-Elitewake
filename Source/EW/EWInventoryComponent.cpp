// Copyright Elite Game Labs. All Rights Reserved.

#include "EWInventoryComponent.h"
#include "World/EWCampfire.h"
#include "EWItemDefinition.h"
#include "EWCraftingRecipe.h"
#include "EWEquipmentComponent.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"

UEWInventoryComponent::UEWInventoryComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 1.f;
	SetIsReplicatedByDefault(true);
}

void UEWInventoryComponent::BeginPlay()
{
	Super::BeginPlay();
    LastFoodClockSeconds = FPlatformTime::Seconds();

	if (GetOwner() && GetOwner()->HasAuthority())
	{
		RefreshSurvivalWeight();
        InitializeStartingRecipes();
	}
}

void UEWInventoryComponent::InitializeStartingRecipes()
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    for (const auto& Recipe : StartingRecipes) UnlockRecipe(Recipe.Get());
}

void UEWInventoryComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    RefreshFoodAge();
}

void UEWInventoryComponent::RefreshFoodAge()
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || bEquipmentTransferInProgress) return;
    const double Now = FPlatformTime::Seconds();
    const double Elapsed = LastFoodClockSeconds > 0. ? FMath::Max(0., Now - LastFoodClockSeconds) : 0.;
    LastFoodClockSeconds = Now;
    AdvanceFoodAge(static_cast<float>(Elapsed));
}

void UEWInventoryComponent::AdvanceFoodAge(float RealSeconds)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || bEquipmentTransferInProgress
        || !FMath::IsFinite(RealSeconds) || RealSeconds <= 0.f) return;
    TGuardValue<bool> Guard(bEquipmentTransferInProgress, true);
    bool bChanged = false;
    for (FEWInventoryEntry& Entry : Entries)
    {
        UEWItemDefinition* Food = Entry.ItemDefinition;
        if (!Food || Food->FoodKind != EEWFoodKind::Berry || !FMath::IsFinite(Food->FreshLifetimeSeconds)
            || Food->FreshLifetimeSeconds <= 0.f) continue;
        Entry.FoodAgeSeconds = FMath::Min(Food->FreshLifetimeSeconds, Entry.FoodAgeSeconds + RealSeconds);
        bChanged = true;
        if (Entry.FoodAgeSeconds < Food->FreshLifetimeSeconds) continue;
        UEWItemDefinition* Spoiled = Food->SpoiledItemDefinition;
        // Invalid authoring leaves expired, unusable food rather than losing units or enabling eating.
        if (!IsValid(Spoiled) || Spoiled == Food || Spoiled->ItemId.IsNone()
            || Spoiled->Category != EEWItemCategory::Resource || Spoiled->FoodKind != EEWFoodKind::None
            || Spoiled->bFoodConsumptionEnabled || Spoiled->EquipmentSlot != EEWEquipmentSlot::None
            || Spoiled->MaxStackSize != Food->MaxStackSize || Spoiled->UnitWeight != Food->UnitWeight) continue;
        Entry.ItemDefinition = Spoiled;
        Entry.FoodAgeSeconds = 0.f;
    }
    if (bChanged) { HandleInventoryChanged(); GetOwner()->ForceNetUpdate(); }
}

void UEWInventoryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UEWInventoryComponent, Entries);
    DOREPLIFETIME_CONDITION(UEWInventoryComponent, AvailableRecipes, COND_OwnerOnly);
}

int32 UEWInventoryComponent::AddItem(UEWItemDefinition* ItemDefinition, int32 Quantity)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !ItemDefinition || Quantity <= 0 || bEquipmentTransferInProgress)
	{
		return 0;
	}
    RefreshFoodAge();
    const int32 Added = AddToEntries(Entries, MaxSlots, ItemDefinition, Quantity);
    if (Added > 0) HandleInventoryChanged();
    return Added;
}

int32 UEWInventoryComponent::GetRoomFor(UEWItemDefinition* Item, int32 Quantity) const
{
    if (!Item || Quantity <= 0) return 0;
    TArray<FEWInventoryEntry> Trial = Entries;
    return AddToEntries(Trial, MaxSlots, Item, Quantity);
}

int32 UEWInventoryComponent::AddToEntries(TArray<FEWInventoryEntry>& Entries, int32 MaxSlots, UEWItemDefinition* ItemDefinition, int32 Quantity)
{
	const int32 MaxStackSize = FMath::Max(1, ItemDefinition->MaxStackSize);
	int32 Remaining = Quantity;

	for (FEWInventoryEntry& Entry : Entries)
	{
		if (Entry.ItemDefinition == ItemDefinition && Entry.Quantity < MaxStackSize)
		{
            // A later pickup gets its own lifetime; never refresh old food or prematurely expire new food.
            if (ItemDefinition->FoodKind == EEWFoodKind::Berry && ItemDefinition->FreshLifetimeSeconds > 0.f
                && Entry.FoodAgeSeconds > 0.f) continue;
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

void UEWInventoryComponent::SetMaxSlots(int32 NewMaxSlots)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    MaxSlots = FMath::Max3(1, NewMaxSlots, Entries.Num());
}

int32 UEWInventoryComponent::TransferEntryTo(UEWInventoryComponent* Destination, int32 EntryIndex, int32 Quantity)
{
    if (!Destination || Destination == this || Quantity <= 0 || !GetOwner() || !GetOwner()->HasAuthority()
        || !Destination->GetOwner() || !Destination->GetOwner()->HasAuthority()
        || bEquipmentTransferInProgress || Destination->bEquipmentTransferInProgress) return 0;
    // Bring both sides' food clocks up to date first, so ages and spoilage are current.
    RefreshFoodAge();
    Destination->RefreshFoodAge();
    if (!Entries.IsValidIndex(EntryIndex) || !Entries[EntryIndex].ItemDefinition || Entries[EntryIndex].Quantity <= 0) return 0;
    const FEWInventoryEntry Source = Entries[EntryIndex];
    UEWItemDefinition* Item = Source.ItemDefinition;
    const int32 Wanted = FMath::Min(Quantity, Source.Quantity);
    const int32 MaxStack = FMath::Max(1, Item->MaxStackSize);
    const bool bAgeing = Item->FoodKind == EEWFoodKind::Berry && Item->FreshLifetimeSeconds > 0.f && Source.FoodAgeSeconds > 0.f;

    // Stage the destination first; commit only what it accepted.
    TArray<FEWInventoryEntry> Staged = Destination->Entries;
    int32 Moved = 0;
    if (bAgeing)
    {
        // Ageing food never merges with other batches, so it keeps its own clock.
        while (Moved < Wanted && Staged.Num() < Destination->MaxSlots)
        {
            FEWInventoryEntry& Batch = Staged.AddDefaulted_GetRef();
            Batch.ItemDefinition = Item;
            Batch.Quantity = FMath::Min(Wanted - Moved, MaxStack);
            Batch.FoodAgeSeconds = Source.FoodAgeSeconds;
            Moved += Batch.Quantity;
        }
    }
    else Moved = AddToEntries(Staged, Destination->MaxSlots, Item, Wanted);
    if (Moved <= 0) return 0;

    TGuardValue<bool> SourceGuard(bEquipmentTransferInProgress, true);
    TGuardValue<bool> DestinationGuard(Destination->bEquipmentTransferInProgress, true);
    Entries[EntryIndex].Quantity -= Moved;
    if (Entries[EntryIndex].Quantity <= 0) Entries.RemoveAt(EntryIndex);
    Destination->Entries = MoveTemp(Staged);
    HandleInventoryChanged();
    Destination->HandleInventoryChanged();
    GetOwner()->ForceNetUpdate();
    Destination->GetOwner()->ForceNetUpdate();
    return Moved;
}

int32 UEWInventoryComponent::RemoveItem(UEWItemDefinition* ItemDefinition, int32 Quantity)
{
	if (!GetOwner() || !GetOwner()->HasAuthority() || !ItemDefinition || Quantity <= 0 || bEquipmentTransferInProgress)
	{
		return 0;
	}
    RefreshFoodAge();
    const int32 Removed = RemoveFromEntries(Entries, ItemDefinition, Quantity);
    if (Removed > 0) HandleInventoryChanged();
    return Removed;
}

EEWFoodUseResult UEWInventoryComponent::ConsumeFood(UEWItemDefinition* Item)
{
    AActor* Owner = GetOwner();
    if (!Owner || !Owner->HasAuthority()) return EEWFoodUseResult::NotAuthority;
    if (bEquipmentTransferInProgress) return EEWFoodUseResult::Busy;
    RefreshFoodAge();
    // Berries age and spoil (FreshLifetimeSeconds); the other foods do not. Any food may carry a sickness chance or cure sickness.
    const bool bAgeing = Item && Item->FoodKind == EEWFoodKind::Berry;
    if (!IsValid(Item) || Item->ItemId.IsNone() || !Item->bFoodConsumptionEnabled
        || Item->Category != EEWItemCategory::Consumable || Item->FoodKind == EEWFoodKind::None
        || Item->EquipmentSlot != EEWEquipmentSlot::None
        || !FMath::IsFinite(Item->FreshLifetimeSeconds) || (bAgeing && Item->FreshLifetimeSeconds <= 0.f)
        || !FMath::IsFinite(Item->HungerRestoreFraction) || !FMath::IsFinite(Item->HealthRestoreFraction) || !FMath::IsFinite(Item->SicknessChance)
        || Item->HungerRestoreFraction < 0.f || Item->HungerRestoreFraction > 1.f
        || Item->HealthRestoreFraction < -1.f || Item->HealthRestoreFraction > 1.f)
        return EEWFoodUseResult::InvalidFood;
    if (!HasItem(Item)) return EEWFoodUseResult::NotOwned;
    UEWSurvivalComponent* Survival = Owner->FindComponentByClass<UEWSurvivalComponent>();
    if (!Survival || Survival->GetHealth() <= 0.f) return EEWFoodUseResult::UnavailableSurvivor;
    const float Hunger = FMath::Clamp(Survival->Hunger + 100.f * Item->HungerRestoreFraction, 0.f, 100.f);
    const float Health = FMath::Clamp(Survival->Health + Survival->MaxHealth * Item->HealthRestoreFraction, 0.f, Survival->MaxHealth);
    const bool bCures = Item->bCuresFoodSickness && Survival->IsFoodSick();
    if (Hunger == Survival->Hunger && Health == Survival->Health && !bCures) return EEWFoodUseResult::NoBenefit;
    // The shared guard also blocks equipment transfers and nested food use during delegates.
    TGuardValue<bool> Guard(bEquipmentTransferInProgress, true);
    // Choose the oldest still-fresh stack. Expired/misconfigured stacks never qualify.
    int32 FoodIndex = INDEX_NONE;
    for (int32 Index = 0; Index < Entries.Num(); ++Index)
        if (Entries[Index].ItemDefinition == Item && Entries[Index].Quantity > 0
            && (!bAgeing || Entries[Index].FoodAgeSeconds < Item->FreshLifetimeSeconds)
            && (FoodIndex == INDEX_NONE || Entries[Index].FoodAgeSeconds > Entries[FoodIndex].FoodAgeSeconds)) FoodIndex = Index;
    if (FoodIndex == INDEX_NONE) return EEWFoodUseResult::InvalidFood;
    if (--Entries[FoodIndex].Quantity == 0) Entries.RemoveAt(FoodIndex);
    Survival->Hunger = Hunger;
    Survival->Health = Health;
    if (Item->bCuresFoodSickness) Survival->CureFoodSickness();
    if (Item->SicknessChance > 0.f && FMath::FRand() < Item->SicknessChance) Survival->ContractFoodSickness();
    // Contents and both food effects are final before weight/stat/inventory observers run.
    HandleInventoryChanged();
    Owner->ForceNetUpdate();
    return EEWFoodUseResult::Success;
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

bool UEWInventoryComponent::UnlockRecipe(UEWCraftingRecipe* Recipe)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || !IsValid(Recipe)) return false;
    AvailableRecipes.AddUnique(Recipe);
    OnInventoryChanged.Broadcast();
    GetOwner()->ForceNetUpdate();
    return true;
}

TArray<UEWCraftingRecipe*> UEWInventoryComponent::GetAvailableRecipes() const
{
    TArray<UEWCraftingRecipe*> Result;
    for (const auto& Recipe : AvailableRecipes) if (IsValid(Recipe)) Result.Add(Recipe.Get());
    return Result;
}

EEWCraftResult UEWInventoryComponent::CraftItem(UEWCraftingRecipe* Recipe)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return EEWCraftResult::NotAuthority;
    RefreshFoodAge();
    TArray<FEWInventoryEntry> Proposed;
    const EEWCraftResult Result = StageCraft(Recipe, Proposed);
    if (Result != EEWCraftResult::Success) return Result;
    TGuardValue<bool> Guard(bEquipmentTransferInProgress, true);
    Entries = MoveTemp(Proposed);
    HandleInventoryChanged();
    GetOwner()->ForceNetUpdate();
    return EEWCraftResult::Success;
}

EEWCraftResult UEWInventoryComponent::GetCraftReadiness(UEWCraftingRecipe* Recipe) const
{
    TArray<FEWInventoryEntry> Proposed;
    return StageCraft(Recipe, Proposed);
}

EEWCraftResult UEWInventoryComponent::StageCraft(UEWCraftingRecipe* Recipe, TArray<FEWInventoryEntry>& Proposed) const
{
    if (bEquipmentTransferInProgress) return EEWCraftResult::Busy;
    if (!IsValid(Recipe)) return EEWCraftResult::InvalidRecipe;
    if (!AvailableRecipes.Contains(Recipe)) return EEWCraftResult::Locked;
    const auto ValidItem = [](const UEWItemDefinition* Item)
    {
        return IsValid(Item) && !Item->ItemId.IsNone() && Item->MaxStackSize > 0
            && FMath::IsFinite(Item->UnitWeight) && Item->UnitWeight >= 0.f;
    };
    if (!ValidItem(Recipe->Output) || Recipe->Ingredients.IsEmpty()) return EEWCraftResult::InvalidRecipe;
    TMap<UEWItemDefinition*, int32> Costs;
    for (const auto& Ingredient : Recipe->Ingredients)
    {
        if (!ValidItem(Ingredient.Item) || Ingredient.Quantity <= 0) return EEWCraftResult::InvalidRecipe;
        int32& Total = Costs.FindOrAdd(Ingredient.Item);
        if (Ingredient.Quantity > MAX_int32 - Total) return EEWCraftResult::InvalidRecipe;
        Total += Ingredient.Quantity;
    }
    Proposed = Entries;
    for (const auto& Cost : Costs)
        if (RemoveFromEntries(Proposed, Cost.Key, Cost.Value) != Cost.Value)
            return EEWCraftResult::MissingIngredients;
    if (AddToEntries(Proposed, MaxSlots, Recipe->Output, 1) != 1) return EEWCraftResult::InventoryFull;
    if (Recipe->bNeedsFire && !AEWCampfire::IsLitFireNear(GetOwner())) return EEWCraftResult::NeedsFire;
    return EEWCraftResult::Success;
}
float UEWInventoryComponent::GetFoodFreshness(const UEWItemDefinition* Item) const
{
    if (!Item || Item->FoodKind != EEWFoodKind::Berry || !FMath::IsFinite(Item->FreshLifetimeSeconds)
        || Item->FreshLifetimeSeconds <= 0.f) return -1.f;
    float Oldest = -1.f;
    for (const auto& Entry : Entries)
        if (Entry.ItemDefinition == Item && Entry.Quantity > 0) Oldest = FMath::Max(Oldest, Entry.FoodAgeSeconds);
    return Oldest < 0.f ? -1.f : FMath::Clamp(1.f - Oldest / Item->FreshLifetimeSeconds, 0.f, 1.f);
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
