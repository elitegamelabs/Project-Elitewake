// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWProgressionComponent.generated.h"

class FLifetimeProperty;

/** The survivor's stats (owner, October 22: one stat point per level). Names and effects are working tuning until the owner sets them. */
UENUM(BlueprintType)
enum class EEWStat : uint8 { Vitality, Endurance, Strength, Fortitude };

/** What earns experience. */
UENUM(BlueprintType)
enum class EEWExperienceSource : uint8 { Gather, Craft, Hunt, Fish };

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FEWOnProgressionChanged);

/**
 * Experience, level and stat points. Every level earns one stat point to spend on a stat; each point in a stat strengthens the survivor (see the Per... values).
 * The server owns everything here; clients ask through the controller to spend a point and see the replicated result. All numbers are editable tuning.
 */
UCLASS(ClassGroup=(Elitewake), BlueprintType, Blueprintable, meta=(BlueprintSpawnableComponent))
class EW_API UEWProgressionComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWProgressionComponent();
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    static constexpr int32 StatCount = 4;
    static FText StatName(EEWStat Stat);
    /** One line saying what a point in the stat does. */
    FText StatEffect(EEWStat Stat) const;

    UPROPERTY(BlueprintAssignable, Category="Progression") FEWOnProgressionChanged OnProgressionChanged;

    UFUNCTION(BlueprintPure, Category="Progression") int32 GetLevel() const { return Level; }
    /** Experience earned towards the next level. */
    UFUNCTION(BlueprintPure, Category="Progression") int32 GetExperience() const { return Experience; }
    UFUNCTION(BlueprintPure, Category="Progression") int32 GetExperienceForNextLevel() const { return ExperienceForLevel(Level); }
    UFUNCTION(BlueprintPure, Category="Progression") int32 GetUnspentPoints() const { return UnspentPoints; }
    UFUNCTION(BlueprintPure, Category="Progression") int32 GetStatPoints(EEWStat Stat) const { return StatPoints.IsValidIndex(int32(Stat)) ? StatPoints[int32(Stat)] : 0; }
    UFUNCTION(BlueprintPure, Category="Progression") bool IsAtMaxLevel() const { return Level >= MaxLevel; }
    /** Experience needed to climb from the given level to the next. */
    UFUNCTION(BlueprintPure, Category="Progression") int32 ExperienceForLevel(int32 FromLevel) const;

    /** Authority only. Adds experience, earning a level (and a stat point) each time the bar fills. Returns the levels gained. */
    UFUNCTION(BlueprintCallable, Category="Progression") int32 GrantExperience(int32 Amount);
    /** Authority only. Experience for one act of the given kind, from the XP values below. */
    UFUNCTION(BlueprintCallable, Category="Progression") int32 Award(EEWExperienceSource Source, int32 Times = 1);
    /** Authority only. Spends one stat point; false when none is left. */
    UFUNCTION(BlueprintCallable, Category="Progression") bool SpendPoint(EEWStat Stat);
    /** Authority only: sets level and spent points straight (a saved survivor coming back, and tests). */
    void Restore(int32 NewLevel, int32 NewExperience, int32 NewUnspent, const TArray<int32>& NewStatPoints);

    /** The most stat points the level allows in all; the rest is the unspent count. */
    UPROPERTY(EditDefaultsOnly, Category="Progression", meta=(ClampMin="1")) int32 MaxLevel = 50;
    /** Experience from level 1 to 2; each further level needs ExperienceStep more. */
    UPROPERTY(EditDefaultsOnly, Category="Progression", meta=(ClampMin="1")) int32 FirstLevelExperience = 100;
    UPROPERTY(EditDefaultsOnly, Category="Progression", meta=(ClampMin="0")) int32 ExperienceStep = 50;
    UPROPERTY(EditDefaultsOnly, Category="Progression|Experience") int32 XpGather = 3;
    UPROPERTY(EditDefaultsOnly, Category="Progression|Experience") int32 XpCraft = 12;
    UPROPERTY(EditDefaultsOnly, Category="Progression|Experience") int32 XpHunt = 25;
    UPROPERTY(EditDefaultsOnly, Category="Progression|Experience") int32 XpFish = 10;
    /** What one point in each stat adds. */
    UPROPERTY(EditDefaultsOnly, Category="Progression|Stats") float HealthPerVitality = 10.f;
    UPROPERTY(EditDefaultsOnly, Category="Progression|Stats") float StaminaPerEndurance = 10.f;
    UPROPERTY(EditDefaultsOnly, Category="Progression|Stats") float CarryPerStrength = 5.f;
    /** Fraction of cold and heat damage turned aside per point of Fortitude (capped at 0.6 in all). */
    UPROPERTY(EditDefaultsOnly, Category="Progression|Stats") float ResistPerFortitude = .04f;

private:
    UFUNCTION() void OnRep_Progression();
    void ApplyStats();
    void Changed();
    UPROPERTY(ReplicatedUsing=OnRep_Progression) int32 Level = 1;
    UPROPERTY(ReplicatedUsing=OnRep_Progression) int32 Experience = 0;
    UPROPERTY(ReplicatedUsing=OnRep_Progression) int32 UnspentPoints = 0;
    UPROPERTY(ReplicatedUsing=OnRep_Progression) TArray<int32> StatPoints;
};
