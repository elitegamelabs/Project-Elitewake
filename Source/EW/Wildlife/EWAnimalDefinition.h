#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EWAnimalDefinition.generated.h"

class UEWItemDefinition;
class UStaticMesh;
class USoundBase;

/** What an animal is doing, shown on every screen (October 27, natural roaming). */
UENUM(BlueprintType)
enum class EEWAnimalAction : uint8 { Wander, Graze, Rest, Look, Flee, Chase };

/** One kind of land animal: how it looks and moves, how it behaves and what it yields. Numbers are tuning. */
UCLASS(BlueprintType)
class EW_API UEWAnimalDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Animal")
    FText DisplayName;
    /** Its body, built nose toward +X with its feet at the origin's height. Its material walks it (see build_animals.py). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Animal")
    TSoftObjectPtr<UStaticMesh> Mesh;
    /** Length and height of the body, in cm: its reach for blows and how big it is to aim at. */
    // For a mesh made outside the game (a generated model): its facing, scale, and how far its pivot sits above its feet
    // (cm, after scaling). The built-in models face +X with their feet at the origin, so they leave these alone.
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Animal")
    FRotator MeshRotation = FRotator::ZeroRotator;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Animal")
    float MeshScale = 1.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Animal")
    float MeshFootLift = 0.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Animal")
    FVector2D Size = FVector2D(80, 50);
    /** Ground covered by one full stride, in cm, so its legs keep pace with its speed. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Animal")
    float StrideLength = 60.f;

    /** Aggressive animals go for a survivor who comes near on land; the rest run off when struck. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    bool bAggressive = false;
    /** Walking and running speeds, cm/s, and how fast it turns, degrees per second. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float WalkSpeed = 80.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float RunSpeed = 300.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float TurnRate = 120.f;
    /** How far from its home it wanders, in cm; between walks it stands a while. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float RoamRadius = 1200.f;
    /** What it does when it stops (owner, October 16: roam naturally with idle, foraging, rest). Relative odds, tuning: grazing
     *  (head down, a plant eater only: not for an aggressive kind), looking about (turns to a new heading), and lying down (only when
     *  no survivor is near). Durations in seconds, a number in each range. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float GrazeOdds = 5.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float LookOdds = 3.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float RestOdds = 2.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    FVector2D GrazeSeconds = FVector2D(5.f, 12.f);
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    FVector2D LookSeconds = FVector2D(2.f, 5.f);
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    FVector2D LieSeconds = FVector2D(14.f, 30.f);
    /** How deep into the sea it will wade, in cm below the surface (0 keeps it ashore). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float WadeDepth = 0.f;
    /** An aggressive animal notices a survivor this close, in cm. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float NoticeRange = 600.f;
    /** Its bite: health taken, seconds between, and reach beyond its nose, in cm. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float AttackDamage = 10.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float AttackInterval = 1.5f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float AttackReach = 50.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    FText AttackName;

    /** Its calls, one picked at random each time. Every animal calls when struck; an aggressive one also when it goes
     *  for a survivor. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Sound")
    TArray<TSoftObjectPtr<USoundBase>> Calls;
    /** Seconds between its calls while it goes about its day, a number in this range (zero: it calls only when provoked). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Sound")
    FVector2D CallInterval = FVector2D::ZeroVector;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest")
    float MaxHealth = 50.f;
    /** What harvesting the body gives, and how many: a number from YieldMin to YieldMax, drawn when it dies. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest")
    TObjectPtr<UEWItemDefinition> Yield;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="1"))
    int32 YieldMin = 2;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="1"))
    int32 YieldMax = 5;
    /** Seconds before a killed animal returns to its home, harvested or not. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest")
    float RespawnSeconds = 300.f;
};
