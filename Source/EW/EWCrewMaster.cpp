#include "EWCrewMaster.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWWalletComponent.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"

namespace
{
// The waterfront's out-of-work sailors (placeholder names and notes, the owner's to change).
const TCHAR* CandidateNames[] = {
    TEXT("Tobin Marsh"), TEXT("Ada Fenwick"), TEXT("Rook Hallam"), TEXT("Mira Quell"), TEXT("Jory Penn"), TEXT("Sable Okoro"),
    TEXT("Hal Brindle"), TEXT("Wren Tasker"), TEXT("Ivo Castell"), TEXT("Nell Garrow"), TEXT("Dace Morrow"), TEXT("Kit Ashby"),
    TEXT("Bram Ulric"), TEXT("Lio Venn"), TEXT("Tamsin Reed"), TEXT("Corin Hale")};
const TCHAR* SailNotes[] = {
    TEXT("knows a reef point from a clew"), TEXT("fast aloft, quick on the lines"), TEXT("twenty years before the mast"),
    TEXT("sailed the Winter run twice"), TEXT("young, keen and strong")};
const TCHAR* GunNotes[] = {
    TEXT("steady hand at the touch-hole"), TEXT("served a broadside on a brigantine"), TEXT("loads fast, swears faster"),
    TEXT("deaf in one ear, sure in the other")};
}

void AEWCrewMaster::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWCrewMaster, Roster);
}

void AEWCrewMaster::BeginPlay()
{
    Super::BeginPlay();
    if (!HasAuthority() || !HasDialogue()) return;
    NextName = FMath::RandRange(0, UE_ARRAY_COUNT(CandidateNames) - 1);
    for (int32 Count = 0; Count < RosterSize; ++Count) AddCandidate();
    GetWorldTimerManager().SetTimer(RosterTimer, this, &AEWCrewMaster::AddCandidate, FMath::Max(1.f, RosterRefillSeconds), true);
}

void AEWCrewMaster::AddCandidate()
{
    if (!HasAuthority() || Roster.Num() >= RosterSize) return;
    FEWCrewCandidate Sailor;
    Sailor.Name = CandidateNames[NextName++ % UE_ARRAY_COUNT(CandidateNames)];
    // About one in three is a gunner, when there are gunner's articles to give.
    Sailor.bGunner = GunnerArticles && FMath::RandRange(0, 2) == 0;
    const int64 Base = Sailor.bGunner ? GunnerHireCost : HireCost;
    Sailor.Fee = int32(Base + FMath::RandRange(-2, 4) * 10);
    Sailor.Note = Sailor.bGunner ? GunNotes[FMath::RandRange(0, UE_ARRAY_COUNT(GunNotes) - 1)] : SailNotes[FMath::RandRange(0, UE_ARRAY_COUNT(SailNotes) - 1)];
    Roster.Add(Sailor);
    ForceNetUpdate();
}

bool AEWCrewMaster::GiveArticles(AEWCharacter* Character, UEWItemDefinition* Item, int64 Fee)
{
    UEWInventoryComponent* Pack = Character ? Character->GetInventoryComponent() : nullptr;
    UEWWalletComponent* Purse = Character ? Character->GetWalletComponent() : nullptr;
    if (!Item || !Pack || !Purse || !Purse->CanAfford(Fee)) return false;
    // The articles go into the pack first, so a full pack costs nothing.
    if (Pack->AddItem(Item, 1) != 1) return false;
    if (!Purse->TrySpend(Fee))
    {
        Pack->RemoveItem(Item, 1);
        return false;
    }
    return true;
}

bool AEWCrewMaster::HireCandidate(AEWCharacter* Character, int32 Index)
{
    if (!HasAuthority() || !Roster.IsValidIndex(Index) || !IsInReach(Character)) return false;
    const FEWCrewCandidate Sailor = Roster[Index];
    if (!GiveArticles(Character, Sailor.bGunner ? GunnerArticles.Get() : Articles.Get(), Sailor.Fee)) return false;
    Roster.RemoveAt(Index);
    ForceNetUpdate();
    return true;
}

FText AEWCrewMaster::GetDialogueGreeting(const AEWCharacter* Character) const
{
    if (!Greeting.IsEmpty() && !Roster.IsEmpty()) return Greeting;
    if (Roster.IsEmpty()) return NSLOCTEXT("Elitewake", "RecruiterEmpty", "Nobody looking for a berth just now. Come back after the next tide.");
    return Super::GetDialogueGreeting(Character);
}

void AEWCrewMaster::GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const
{
    const UEWWalletComponent* Purse = IsValid(Character) ? Character->GetWalletComponent() : nullptr;
    for (int32 Index = 0; Index < Roster.Num(); ++Index)
    {
        const FEWCrewCandidate& Sailor = Roster[Index];
        Out.Add({FName(*FString::Printf(TEXT("Hire%d"), Index)), FText::Format(NSLOCTEXT("Elitewake", "RecruiterOption", "Sign {0}, {1}, for {2}: {3}"),
            FText::FromString(Sailor.Name), Sailor.bGunner ? NSLOCTEXT("Elitewake", "RoleGunner", "gunner") : NSLOCTEXT("Elitewake", "RoleSailhand", "sailhand"),
            FText::FromString(UEWWalletComponent::Format(Sailor.Fee)), FText::FromString(Sailor.Note)), Purse && Purse->CanAfford(Sailor.Fee)});
    }
}

FText AEWCrewMaster::ActOnDialogue(AEWCharacter* Character, FName Key)
{
    const FString Name = Key.ToString();
    if (!Name.StartsWith(TEXT("Hire"))) return FText::GetEmpty();
    const int32 Index = FCString::Atoi(*Name.RightChop(4));
    if (!Roster.IsValidIndex(Index)) return FText::GetEmpty();
    const FEWCrewCandidate Sailor = Roster[Index];
    if (!HireCandidate(Character, Index)) return NSLOCTEXT("Elitewake", "RecruiterNoRoom", "No room in your pack for the articles.");
    return FText::Format(NSLOCTEXT("Elitewake", "RecruiterSigned", "{0} makes their mark. Their articles are in your pack: use them aboard, at {1}."),
        FText::FromString(Sailor.Name), Sailor.bGunner ? NSLOCTEXT("Elitewake", "AtCannon", "a fitted cannon") : NSLOCTEXT("Elitewake", "AtLines", "a sail's lines by the mast"));
}

FText AEWCrewMaster::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    if (HasDialogue()) return AEWTownsfolk::GetInteractionPrompt_Implementation(Character);
    const FText Fee = FText::FromString(UEWWalletComponent::Format(HireCost));
    const UEWWalletComponent* Purse = IsValid(Character) ? Character->GetWalletComponent() : nullptr;
    if (!Purse || !Purse->CanAfford(HireCost))
        return FText::Format(NSLOCTEXT("Elitewake", "CrewMasterPoor", "Crew master: a {0} costs {1}"), FText::FromString(CrewRole), Fee);
    return FText::Format(NSLOCTEXT("Elitewake", "CrewMasterHire", "Hire a {0} ({1})"), FText::FromString(CrewRole), Fee);
}

bool AEWCrewMaster::Interact_Implementation(AEWCharacter* Character)
{
    if (HasDialogue()) return AEWTownsfolk::Interact_Implementation(Character);
    if (!HasAuthority() || !Articles || !CanInteract_Implementation(Character)
        || FVector::Dist(Character->GetActorLocation(), GetActorLocation()) > TradeReach) return false;
    UEWInventoryComponent* Pack = Character->GetInventoryComponent();
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Pack || !Purse || !Purse->CanAfford(HireCost)) return false;
    // The articles go into the pack first, so a full pack costs nothing.
    if (Pack->AddItem(Articles, 1) != 1) return false;
    if (!Purse->TrySpend(HireCost))
    {
        Pack->RemoveItem(Articles, 1);
        return false;
    }
    return true;
}
