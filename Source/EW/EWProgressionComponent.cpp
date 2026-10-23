// Copyright Elite Game Labs. All Rights Reserved.

#include "EWProgressionComponent.h"
#include "EWSurvivalComponent.h"
#include "EWSkillTree.h"
#include "EWInventoryComponent.h"
#include "EWCraftingRecipe.h"
#include "GameFramework/Actor.h"
#include "Net/UnrealNetwork.h"

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
    if (!GetOwner() || !GetOwner()->HasAuthority() || UnspentPoints <= 0 || !StatPoints.IsValidIndex(int32(Stat))) return false;
    --UnspentPoints; ++StatPoints[int32(Stat)];
    ApplyStats();
    Changed();
    return true;
}

void UEWProgressionComponent::Restore(int32 NewLevel, int32 NewExperience, int32 NewUnspent, const TArray<int32>& NewStatPoints, int32 NewSkillPoints, const TArray<FName>& NewSkills)
{
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
    OnProgressionChanged.Broadcast();
}
