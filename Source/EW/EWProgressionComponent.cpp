// Copyright Elite Game Labs. All Rights Reserved.

#include "EWProgressionComponent.h"
#include "EWSurvivalComponent.h"
#include "EWSkillTree.h"
#include "EWInventoryComponent.h"
#include "EWCraftingRecipe.h"
#include "EWWalletComponent.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"

static_assert(UEWProgressionComponent::AttributeResetCopper == 5 * UEWWalletComponent::CopperPerSilver * UEWWalletComponent::SilverPerGold);

UEWProgressionComponent::UEWProgressionComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
    StatPoints.Init(0, StatCount);
}

void UEWProgressionComponent::BeginPlay()
{
    Super::BeginPlay();
    if (StatPoints.Num() != StatCount) StatPoints.SetNumZeroed(StatCount);
    if (GetOwner() && GetOwner()->HasAuthority()) { ApplyStats(); GrantSkillRecipes(); }
}

void UEWProgressionComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UEWProgressionComponent, Level);
    DOREPLIFETIME(UEWProgressionComponent, Experience);
    DOREPLIFETIME(UEWProgressionComponent, UnspentPoints);
    DOREPLIFETIME(UEWProgressionComponent, StatPoints);
    DOREPLIFETIME(UEWProgressionComponent, SkillPoints);
    DOREPLIFETIME(UEWProgressionComponent, UnlockedSkills);
    DOREPLIFETIME(UEWProgressionComponent, AttributeRevision);
}

FText UEWProgressionComponent::StatName(EEWStat Stat)
{
    switch (Stat)
    {
    case EEWStat::Vitality: return NSLOCTEXT("Elitewake", "StatVitality", "Vitality");
    case EEWStat::Endurance: return NSLOCTEXT("Elitewake", "StatEndurance", "Endurance");
    case EEWStat::Strength: return NSLOCTEXT("Elitewake", "StatStrength", "Strength");
    default: return NSLOCTEXT("Elitewake", "StatFortitude", "Fortitude");
    }
}

FText UEWProgressionComponent::StatEffect(EEWStat Stat) const
{
    switch (Stat)
    {
    case EEWStat::Vitality: return FText::Format(NSLOCTEXT("Elitewake", "StatVitalityEffect", "+{0} maximum health per point"), FMath::RoundToInt(HealthPerVitality));
    case EEWStat::Endurance: return FText::Format(NSLOCTEXT("Elitewake", "StatEnduranceEffect", "+{0} maximum stamina per point"), FMath::RoundToInt(StaminaPerEndurance));
    case EEWStat::Strength: return FText::Format(NSLOCTEXT("Elitewake", "StatStrengthEffect", "+{0} kg carrying capacity per point"), FMath::RoundToInt(CarryPerStrength));
    default: return FText::Format(NSLOCTEXT("Elitewake", "StatFortitudeEffect", "{0}% less cold and heat damage per point"), FMath::RoundToInt(ResistPerFortitude * 100.f));
    }
}

int32 UEWProgressionComponent::ExperienceForLevel(int32 FromLevel) const
{
    return FirstLevelExperience + ExperienceStep * FMath::Max(0, FromLevel - 1);
}

int32 UEWProgressionComponent::GrantExperience(int32 Amount)
{
    if (bAttributeTransaction) return 0;
    if (!GetOwner() || !GetOwner()->HasAuthority() || Amount <= 0 || IsAtMaxLevel()) return 0;
    Experience += Amount;
    int32 Gained = 0;
    while (!IsAtMaxLevel() && Experience >= ExperienceForLevel(Level))
    {
        Experience -= ExperienceForLevel(Level);
        ++Level; ++UnspentPoints; ++SkillPoints; ++Gained;
    }
    if (IsAtMaxLevel()) Experience = 0;
    Changed();
    return Gained;
}

int32 UEWProgressionComponent::Award(EEWExperienceSource Source, int32 Times)
{
    const int32 Each = Source == EEWExperienceSource::Gather ? XpGather : Source == EEWExperienceSource::Craft ? XpCraft
        : Source == EEWExperienceSource::Hunt ? XpHunt : XpFish;
    return GrantExperience(Each * FMath::Max(1, Times));
}

bool UEWProgressionComponent::SpendPoint(EEWStat Stat)
{
    if (bAttributeTransaction) return false;
    if (!GetOwner() || !GetOwner()->HasAuthority() || UnspentPoints <= 0 || !StatPoints.IsValidIndex(int32(Stat))) return false;
    --UnspentPoints; ++StatPoints[int32(Stat)];
    ApplyStats();
    Changed();
    return true;
}

EEWAttributeResult UEWProgressionComponent::CommitAttributePoints(const TArray<int32>& Additions, int64 ExpectedRevision, TFunctionRef<bool()> Persist)
{
    return AttributeTransaction(Additions, false, ExpectedRevision, Persist);
}

EEWAttributeResult UEWProgressionComponent::ResetAttributePoints(int64 ExpectedRevision, TFunctionRef<bool()> Persist)
{
    return AttributeTransaction({}, true, ExpectedRevision, Persist);
}

EEWAttributeResult UEWProgressionComponent::AttributeTransaction(const TArray<int32>& Additions, bool bReset, int64 ExpectedRevision, TFunctionRef<bool()> Persist)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return EEWAttributeResult::NotAuthority;
    if (bAttributeTransaction) return EEWAttributeResult::Busy;
    if (ExpectedRevision != AttributeRevision) return EEWAttributeResult::Stale;
    int64 Total = 0;
    if (bReset)
    {
        for (const int32 Points : StatPoints) Total += Points;
        if (Total <= 0) return EEWAttributeResult::NothingToReset;
        if (Total > MAX_int32 - int64(UnspentPoints)) return EEWAttributeResult::InvalidAllocation;
    }
    else
    {
        if (Additions.Num() != StatCount) return EEWAttributeResult::InvalidAllocation;
        for (int32 Index = 0; Index < StatCount; ++Index)
        {
            if (Additions[Index] < 0 || int64(Additions[Index]) + StatPoints[Index] > MAX_int32) return EEWAttributeResult::InvalidAllocation;
            Total += Additions[Index];
        }
        if (Total <= 0) return EEWAttributeResult::InvalidAllocation;
        if (Total > UnspentPoints) return EEWAttributeResult::NotEnoughPoints;
    }
    auto* Wallet = GetOwner()->FindComponentByClass<UEWWalletComponent>();
    if (bReset && (!Wallet || !Wallet->CanAfford(AttributeResetCopper))) return EEWAttributeResult::NotEnoughGold;
    TGuardValue<bool> Guard(bAttributeTransaction, true);
    const auto Before = StatPoints;
    const int32 BeforeUnspent = UnspentPoints;
    const int64 BeforeCopper = Wallet ? Wallet->GetCopper() : 0;
    auto* Survival = GetOwner()->FindComponentByClass<UEWSurvivalComponent>();
    const float BeforeHealth = Survival ? Survival->GetHealth() : 0.f;
    const float BeforeStamina = Survival ? Survival->GetStamina() : 0.f;
    if (bReset)
    {
        if (!Wallet->TrySpend(AttributeResetCopper)) return EEWAttributeResult::NotEnoughGold;
        StatPoints.Init(0, StatCount);
        UnspentPoints += int32(Total);
    }
    else
    {
        for (int32 Index = 0; Index < StatCount; ++Index) StatPoints[Index] += Additions[Index];
        UnspentPoints -= int32(Total);
    }
    ApplyStats();
    if (!Persist())
    {
        StatPoints = Before;
        UnspentPoints = BeforeUnspent;
        if (Wallet) Wallet->SetCopper(BeforeCopper);
        ApplyStats();
        if (Survival)
        {
            Survival->Health = BeforeHealth;
            Survival->Stamina = BeforeStamina;
            Survival->NotifyStatsChanged();
        }
        return EEWAttributeResult::SaveFailed;
    }
    Changed();
    return EEWAttributeResult::Success;
}

void UEWProgressionComponent::Restore(int32 NewLevel, int32 NewExperience, int32 NewUnspent, const TArray<int32>& NewStatPoints, int32 NewSkillPoints, const TArray<FName>& NewSkills)
{
    if (bAttributeTransaction) return;
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    Level = FMath::Clamp(NewLevel, 1, MaxLevel);
    Experience = FMath::Max(0, NewExperience);
    UnspentPoints = FMath::Max(0, NewUnspent);
    StatPoints.SetNumZeroed(StatCount);
    for (int32 i = 0; i < StatCount && i < NewStatPoints.Num(); ++i) StatPoints[i] = FMath::Max(0, NewStatPoints[i]);
    SkillPoints = FMath::Max(0, NewSkillPoints);
    UnlockedSkills.Reset();
    for (const FName& Id : NewSkills) if (FEWSkillTree::Find(Id)) UnlockedSkills.AddUnique(Id);     // a star that no longer exists is left out
    ApplyStats();
    GrantSkillRecipes();
    Changed();
}

bool UEWProgressionComponent::IsSkillUnlocked(FName Id) const
{
    const FEWSkillNode* Node = FEWSkillTree::Find(Id);
    return Node && (UnlockedSkills.Contains(Id) || (Node->Cost <= 0 && Node->Requires.IsEmpty()));
}

bool UEWProgressionComponent::CanUnlockSkill(FName Id) const
{
    const FEWSkillNode* Node = FEWSkillTree::Find(Id);
    if (!Node || IsSkillUnlocked(Id) || SkillPoints < Node->Cost) return false;
    for (const FName& Parent : Node->Requires) if (!IsSkillUnlocked(Parent)) return false;
    return true;
}

bool UEWProgressionComponent::UnlockSkill(FName Id)
{
    if (bAttributeTransaction) return false;
    if (!GetOwner() || !GetOwner()->HasAuthority() || !CanUnlockSkill(Id)) return false;
    const FEWSkillNode* Node = FEWSkillTree::Find(Id);
    SkillPoints -= Node->Cost;
    UnlockedSkills.Add(Id);
    ApplyStats();
    GrantSkillRecipes();
    Changed();
    return true;
}

void UEWProgressionComponent::GrantSkillRecipes()
{
    auto* Pack = GetOwner() ? GetOwner()->FindComponentByClass<UEWInventoryComponent>() : nullptr;
    if (!Pack || !GetOwner()->HasAuthority()) return;
    for (const FEWSkillNode& Node : FEWSkillTree::Nodes())
        if (IsSkillUnlocked(Node.Id))
            for (const TSoftObjectPtr<UEWCraftingRecipe>& Recipe : Node.Recipes)
                if (UEWCraftingRecipe* Loaded = Recipe.LoadSynchronous()) Pack->UnlockRecipe(Loaded);
}

void UEWProgressionComponent::ApplyStats()
{
    float Health = GetStatPoints(EEWStat::Vitality) * HealthPerVitality, Stamina = GetStatPoints(EEWStat::Endurance) * StaminaPerEndurance;
    float Carry = GetStatPoints(EEWStat::Strength) * CarryPerStrength;
    for (const FEWSkillNode& Node : FEWSkillTree::Nodes())
        if (IsSkillUnlocked(Node.Id)) { Health += Node.MaxHealthBonus; Stamina += Node.MaxStaminaBonus; Carry += Node.CarryBonus; }
    if (UEWSurvivalComponent* Survival = GetOwner() ? GetOwner()->FindComponentByClass<UEWSurvivalComponent>() : nullptr)
        Survival->SetStatBonuses(Health, Stamina, Carry, FMath::Min(.6f, GetStatPoints(EEWStat::Fortitude) * ResistPerFortitude));
}

void UEWProgressionComponent::OnRep_Progression()
{
    Changed();
}

void UEWProgressionComponent::Changed()
{
    if (GetOwner() && GetOwner()->HasAuthority())
    {
        ++AttributeRevision;
        GetOwner()->ForceNetUpdate();
    }
    OnProgressionChanged.Broadcast();
}
