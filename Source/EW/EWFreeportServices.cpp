#include "EWFreeportServices.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "EWWalletComponent.h"
#include "Components/CapsuleComponent.h"
#include "EngineUtils.h"
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"

namespace
{
FText Copper(int64 Amount) { return FText::FromString(UEWWalletComponent::Format(Amount)); }
float HullLength(const AEWShip* Ship)
{
    return Ship && Ship->Definition ? Ship->Definition->HullExtent.X * 2.f : 0.f;
}
}

// ---- Shipwright -----------------------------------------------------------------------------------------------------

FText AEWShipwright::ShipName(const UEWShipDefinition* Definition)
{
    if (!Definition) return FText::GetEmpty();
    return Definition->DisplayName.IsEmpty() ? FText::FromName(Definition->ShipId) : Definition->DisplayName;
}

bool AEWShipwright::IsSlipClear() const
{
    if (!GetWorld()) return false;
    for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
        if (!It->IsSinking() && FVector::Dist2D(It->GetActorLocation(), LaunchPoint.GetLocation()) < FMath::Max(1200.f, HullLength(*It) * .6f + 600.f))
            return false;
    return true;
}

AEWShip* AEWShipwright::BuyShip(AEWCharacter* Character, int32 Index)
{
    if (!HasAuthority() || !ShipsForSale.IsValidIndex(Index) || !ShipsForSale[Index].Definition || !ShipClass || !IsInReach(Character)
        || !IsSlipClear()) return nullptr;
    const FEWShipForSale& Sale = ShipsForSale[Index];
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Purse || !Purse->TrySpend(Sale.PriceCopper)) return nullptr;
    AEWShip* Ship = GetWorld()->SpawnActorDeferred<AEWShip>(ShipClass, LaunchPoint, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!Ship)
    {
        Purse->AddCopper(Sale.PriceCopper);
        return nullptr;
    }
    Ship->Definition = Sale.Definition;
    Ship->FinishSpawning(LaunchPoint);
    for (int32 Fit = 0; Fit < Sale.FittedMounts.Num() && Fit < Sale.FittedItems.Num(); ++Fit)
        if (Sale.FittedItems[Fit]) Ship->FitAtShipyard(Sale.FittedMounts[Fit], Sale.FittedItems[Fit]);
    return Ship;
}

AEWShip* AEWShipwright::FindShipToRepair(const AEWCharacter* Character, int64& OutCost) const
{
    OutCost = 0;
    if (!IsValid(Character) || !GetWorld()) return nullptr;
    AEWShip* Best = nullptr;
    float BestDistance = TNumericLimits<float>::Max();
    for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
    {
        AEWShip* Ship = *It;
        const bool bDamaged = Ship->GetHullHealth() < Ship->GetMaxHullHealth() - KINDA_SMALL_NUMBER || Ship->GetHoleCount() > 0 || Ship->GetWaterAboard() > 0.f;
        if (Ship->IsSinking() || !bDamaged || FVector::Dist2D(Ship->GetActorLocation(), GetActorLocation()) > YardReach) continue;
        const float Distance = FVector::Dist(Ship->GetActorLocation(), Character->GetActorLocation());
        if (Distance < BestDistance) { BestDistance = Distance; Best = Ship; }
    }
    if (Best) OutCost = FMath::Max<int64>(1, FMath::CeilToInt64((Best->GetMaxHullHealth() - Best->GetHullHealth()) * RepairCopperPerPoint) + Best->GetHoleCount() * 2);
    return Best;
}

bool AEWShipwright::RepairShip(AEWCharacter* Character)
{
    if (!HasAuthority() || !IsInReach(Character)) return false;
    int64 Cost = 0;
    AEWShip* Ship = FindShipToRepair(Character, Cost);
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Ship || !Purse || !Purse->TrySpend(Cost)) return false;
    Ship->RepairAtShipyard();
    return true;
}

void AEWShipwright::GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const
{
    // His fittings for sale first (as a merchant's goods), then the ships and the repair.
    Super::GetDialogueOptions(Character, Out);
    const UEWWalletComponent* Purse = IsValid(Character) ? Character->GetWalletComponent() : nullptr;
    const bool bSlip = IsSlipClear();
    for (int32 Index = 0; Index < ShipsForSale.Num(); ++Index)
    {
        const FEWShipForSale& Sale = ShipsForSale[Index];
        if (!Sale.Definition) continue;
        Out.Add({FName(*FString::Printf(TEXT("Ship%d"), Index)), bSlip
            ? FText::Format(NSLOCTEXT("Elitewake", "ShipwrightBuy", "Buy a {0} for {1}, launched from the slipway"), ShipName(Sale.Definition), Copper(Sale.PriceCopper))
            : FText::Format(NSLOCTEXT("Elitewake", "ShipwrightSlipBusy", "Buy a {0} for {1} (the slipway is blocked)"), ShipName(Sale.Definition), Copper(Sale.PriceCopper)),
            bSlip && Purse && Purse->CanAfford(Sale.PriceCopper)});
    }
    int64 Cost = 0;
    if (const AEWShip* Ship = FindShipToRepair(Character, Cost))
        Out.Add({FName(TEXT("Repair")), FText::Format(NSLOCTEXT("Elitewake", "ShipwrightRepair", "Repair the {0} nearby ({1} of {2} hull, {3} holes) for {4}"),
            ShipName(Ship->Definition), FText::AsNumber(FMath::RoundToInt(Ship->GetHullHealth())), FText::AsNumber(FMath::RoundToInt(Ship->GetMaxHullHealth())),
            FText::AsNumber(Ship->GetHoleCount()), Copper(Cost)), Purse && Purse->CanAfford(Cost)});
    else
        Out.Add({FName(TEXT("Repair")), NSLOCTEXT("Elitewake", "ShipwrightNothing", "Repair: no damaged ship in the harbor"), false});
}

FText AEWShipwright::ActOnDialogue(AEWCharacter* Character, FName Key)
{
    if (const FText Sold = Super::ActOnDialogue(Character, Key); !Sold.IsEmpty()) return Sold;
    if (Key == FName(TEXT("Repair")))
        return RepairShip(Character) ? NSLOCTEXT("Elitewake", "ShipwrightRepaired", "Caulked, patched and pumped dry. She is sound again.")
                                     : NSLOCTEXT("Elitewake", "ShipwrightNoRepair", "Nothing my yard can do for you just now.");
    const FString Name = Key.ToString();
    if (Name.StartsWith(TEXT("Ship")))
    {
        const int32 Index = FCString::Atoi(*Name.RightChop(4));
        if (const AEWShip* Ship = BuyShip(Character, Index))
            return FText::Format(NSLOCTEXT("Elitewake", "ShipwrightSold", "She is yours. Your {0} is afloat at the foot of the slipway, anchored and fitted out."), ShipName(Ship->Definition));
        return NSLOCTEXT("Elitewake", "ShipwrightNoSale", "The slipway is not clear, or your purse is light.");
    }
    return FText::GetEmpty();
}

// ---- Tavern keeper --------------------------------------------------------------------------------------------------

bool AEWTavernKeeper::CompleteContract(AEWCharacter* Character, int32 Index)
{
    if (!HasAuthority() || !Contracts.IsValidIndex(Index) || !Contracts[Index].Item || !IsInReach(Character)) return false;
    const FEWDeliveryContract& Job = Contracts[Index];
    UEWInventoryComponent* Pack = Character->GetInventoryComponent();
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Pack || !Purse || Pack->GetItemCount(Job.Item) < Job.Quantity) return false;
    if (Pack->RemoveItem(Job.Item, Job.Quantity) != Job.Quantity) return false;
    Purse->AddCopper(Job.RewardCopper);
    return true;
}

bool AEWTavernKeeper::BuyDrink(AEWCharacter* Character)
{
    if (!HasAuthority() || !IsInReach(Character)) return false;
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    UEWSurvivalComponent* Needs = Character->GetSurvivalComponent();
    if (!Purse || !Needs || !Purse->TrySpend(DrinkCost)) return false;
    Needs->SetHydration(FMath::Min(100.f, Needs->GetHydration() + DrinkHydration));
    return true;
}

FText AEWTavernKeeper::DescribeContracts() const
{
    if (Contracts.IsEmpty()) return NSLOCTEXT("Elitewake", "TavernNoJobs", "No work posted.");
    FString Text;
    for (const FEWDeliveryContract& Job : Contracts)
    {
        if (!Job.Item) continue;
        Text += FString::Printf(TEXT("- %d %s for %s. %s\n"), Job.Quantity, *Job.Item->DisplayName.ToString(), *UEWWalletComponent::Format(Job.RewardCopper), *Job.Story.ToString());
    }
    return FText::FromString(Text.TrimEnd());
}

void AEWTavernKeeper::GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const
{
    if (!Rumors.IsEmpty()) Out.Add({FName(TEXT("Rumor")), NSLOCTEXT("Elitewake", "TavernRumor", "Heard anything worth knowing?"), true});
    const UEWInventoryComponent* Pack = IsValid(Character) ? Character->GetInventoryComponent() : nullptr;
    for (int32 Index = 0; Index < Contracts.Num(); ++Index)
    {
        const FEWDeliveryContract& Job = Contracts[Index];
        if (!Job.Item) continue;
        const int32 Have = Pack ? Pack->GetItemCount(Job.Item) : 0;
        Out.Add({FName(*FString::Printf(TEXT("Job%d"), Index)), FText::Format(NSLOCTEXT("Elitewake", "TavernJob", "Job: bring {0} {1} for {2} (you have {3})"),
            FText::AsNumber(Job.Quantity), Job.Item->DisplayName, Copper(Job.RewardCopper), FText::AsNumber(Have)), Have >= Job.Quantity});
    }
    const UEWWalletComponent* Purse = IsValid(Character) ? Character->GetWalletComponent() : nullptr;
    Out.Add({FName(TEXT("Drink")), FText::Format(NSLOCTEXT("Elitewake", "TavernDrink", "Buy a drink ({0})"), Copper(DrinkCost)), Purse && Purse->CanAfford(DrinkCost)});
}

FText AEWTavernKeeper::ActOnDialogue(AEWCharacter* Character, FName Key)
{
    if (Key == FName(TEXT("Rumor")) && !Rumors.IsEmpty()) return Rumors[NextRumor++ % Rumors.Num()];
    if (Key == FName(TEXT("Drink")))
        return BuyDrink(Character) ? NSLOCTEXT("Elitewake", "TavernDrank", "Small beer, cool from the cellar. Your thirst eases.")
                                   : NSLOCTEXT("Elitewake", "TavernNoDrink", "Coin first, friend.");
    const FString Name = Key.ToString();
    if (Name.StartsWith(TEXT("Job")))
    {
        const int32 Index = FCString::Atoi(*Name.RightChop(3));
        if (CompleteContract(Character, Index))
            return FText::Format(NSLOCTEXT("Elitewake", "TavernPaid", "Just what was wanted. {0}, as promised. The job stays posted if you can do it again."), Copper(Contracts[Index].RewardCopper));
        return NSLOCTEXT("Elitewake", "TavernShort", "That is not all of it.");
    }
    return FText::GetEmpty();
}

// ---- Harbor master --------------------------------------------------------------------------------------------------

AEWShip* AEWHarborMaster::FindShipFor(const AEWCharacter* Character) const
{
    if (!IsValid(Character) || !GetWorld()) return nullptr;
    AEWShip* Best = nullptr;
    float BestDistance = TNumericLimits<float>::Max();
    for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
    {
        if (It->IsSinking() || FVector::Dist2D(It->GetActorLocation(), GetActorLocation()) > ApproachRadius) continue;
        const float Distance = FVector::Dist(It->GetActorLocation(), Character->GetActorLocation());
        if (Distance < BestDistance) { BestDistance = Distance; Best = *It; }
    }
    return Best;
}

int32 AEWHarborMaster::FindBerthOf(const AEWShip* Ship) const
{
    if (!Ship) return INDEX_NONE;
    for (int32 Index = 0; Index < Berths.Num(); ++Index)
        if (FVector::Dist2D(Ship->GetActorLocation(), Berths[Index].Where.GetLocation()) < 700.f) return Index;
    return INDEX_NONE;
}

int32 AEWHarborMaster::FindFreeBerth(const AEWShip* Ship) const
{
    if (!Ship || !GetWorld()) return INDEX_NONE;
    const float Length = HullLength(Ship);
    for (int32 Index = 0; Index < Berths.Num(); ++Index)
    {
        const FEWBerth& Berth = Berths[Index];
        if (Length > Berth.MaxLength) continue;
        bool bTaken = false;
        for (TActorIterator<AEWShip> It(GetWorld()); It && !bTaken; ++It)
            bTaken = *It != Ship && !It->IsSinking() && FVector::Dist2D(It->GetActorLocation(), Berth.Where.GetLocation()) < Berth.MaxLength * .55f + HullLength(*It) * .5f;
        if (!bTaken) return Index;
    }
    return INDEX_NONE;
}

int32 AEWHarborMaster::RequestBerth(AEWCharacter* Character)
{
    if (!HasAuthority() || !IsInReach(Character)) return INDEX_NONE;
    AEWShip* Ship = FindShipFor(Character);
    if (!Ship || FindBerthOf(Ship) != INDEX_NONE) return INDEX_NONE;
    const int32 Berth = FindFreeBerth(Ship);
    if (Berth == INDEX_NONE || !Ship->TowTo(Berths[Berth].Where)) return INDEX_NONE;
    return Berth;
}

bool AEWHarborMaster::ClearForDeparture(AEWCharacter* Character)
{
    if (!HasAuthority() || !IsInReach(Character)) return false;
    AEWShip* Ship = FindShipFor(Character);
    if (!Ship || !Ship->TowTo(DepartureLane)) return false;
    // Rowed out: ashore, the survivor is set on her deck amidships.
    if (!Ship->IsAboard(Character))
    {
        const float Up = Ship->Definition ? Ship->Definition->GetDeckHeight() : 200.f;
        Character->TeleportTo(Ship->GetActorTransform().TransformPosition(FVector(0.f, 0.f, Up + Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 10.f)),
            Ship->GetActorRotation(), false, true);
    }
    return true;
}

void AEWHarborMaster::GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const
{
    const AEWShip* Ship = FindShipFor(Character);
    const int32 InBerth = FindBerthOf(Ship);
    if (!Ship)
        Out.Add({FName(TEXT("Berth")), NSLOCTEXT("Elitewake", "HarborNoShip", "Berth: no ship of yours in the approaches"), false});
    else if (InBerth != INDEX_NONE)
        Out.Add({FName(TEXT("Berth")), FText::Format(NSLOCTEXT("Elitewake", "HarborBerthed", "Berth: your {0} lies at {1}"), AEWShipwright::ShipName(Ship->Definition), Berths[InBerth].Name), false});
    else
    {
        const int32 Free = FindFreeBerth(Ship);
        Out.Add({FName(TEXT("Berth")), Free != INDEX_NONE
            ? FText::Format(NSLOCTEXT("Elitewake", "HarborBerthAsk", "Bring my {0} in to a berth"), AEWShipwright::ShipName(Ship->Definition))
            : NSLOCTEXT("Elitewake", "HarborFull", "Berth: every berth that takes her is taken"), Free != INDEX_NONE});
    }
    Out.Add({FName(TEXT("Depart")), Ship
        ? FText::Format(NSLOCTEXT("Elitewake", "HarborDepart", "Clear my {0} for departure (towed to the harbor mouth, you aboard)"), AEWShipwright::ShipName(Ship->Definition))
        : NSLOCTEXT("Elitewake", "HarborDepartNone", "Departure: no ship of yours in the approaches"), Ship != nullptr});
    Out.Add({FName(TEXT("Rules")), NSLOCTEXT("Elitewake", "HarborRules", "What are the harbor's rules?"), true});
}

FText AEWHarborMaster::ActOnDialogue(AEWCharacter* Character, FName Key)
{
    if (Key == FName(TEXT("Berth")))
    {
        const int32 Berth = RequestBerth(Character);
        return Berth != INDEX_NONE ? FText::Format(NSLOCTEXT("Elitewake", "HarborBerthed2", "My pilots have brought her in to {0} and dropped her anchor."), Berths[Berth].Name)
                                   : NSLOCTEXT("Elitewake", "HarborNoBerth", "No berth for her just now.");
    }
    if (Key == FName(TEXT("Depart")))
        return ClearForDeparture(Character) ? NSLOCTEXT("Elitewake", "HarborDeparted", "Cleared. She lies at the harbor mouth, bow to the sea, anchor down until you raise it. Fair winds.")
                                            : NSLOCTEXT("Elitewake", "HarborNoDepart", "I cannot clear her just now.");
    if (Key == FName(TEXT("Rules")))
        return NSLOCTEXT("Elitewake", "HarborRulesText", "This is a free port. Inside its bounds no one raises a hand or a gun against another, no one builds, and no beast is let in. Trade fair, pay your crew, and take your quarrels out past the harbor mouth.");
    return FText::GetEmpty();
}

// ---- Notice board ---------------------------------------------------------------------------------------------------

AEWNoticeBoard::AEWNoticeBoard()
{
    // A wide, low target the size of the board itself, at reading height.
    Capsule->InitCapsuleSize(80.f, 110.f);
    Capsule->SetRelativeLocation(FVector(0, 0, 130.f));
    // No figure, so the board's own target is always solid to aim.
    Capsule->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
}

FText AEWNoticeBoard::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    return FText::Format(NSLOCTEXT("Elitewake", "NoticeBoardRead", "Read the {0}"), NpcName);
}

FText AEWNoticeBoard::GetDialogueGreeting(const AEWCharacter* Character) const
{
    return Directions.IsEmpty() ? NSLOCTEXT("Elitewake", "NoticeBoardBlank", "Old nails and torn paper.") : Directions;
}

void AEWNoticeBoard::GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const
{
    Out.Add({FName(TEXT("Jobs")), NSLOCTEXT("Elitewake", "NoticeBoardJobs", "Read the posted jobs"), true});
    Out.Add({FName(TEXT("Directions")), NSLOCTEXT("Elitewake", "NoticeBoardDirections", "Read the directions"), true});
}

FText AEWNoticeBoard::ActOnDialogue(AEWCharacter* Character, FName Key)
{
    if (Key == FName(TEXT("Directions"))) return GetDialogueGreeting(Character);
    if (Key != FName(TEXT("Jobs")) || !GetWorld()) return FText::GetEmpty();
    const AEWTavernKeeper* Keeper = nullptr;
    for (TActorIterator<AEWTavernKeeper> It(GetWorld()); It; ++It)
        if (!Keeper || FVector::DistSquared(It->GetActorLocation(), GetActorLocation()) < FVector::DistSquared(Keeper->GetActorLocation(), GetActorLocation())) Keeper = *It;
    if (!Keeper) return NSLOCTEXT("Elitewake", "TavernNoJobs", "No work posted.");
    return FText::Format(NSLOCTEXT("Elitewake", "NoticeBoardJobList", "Jobs, paid at the tavern by {0}:\n{1}"), Keeper->NpcName, Keeper->DescribeContracts());
}
