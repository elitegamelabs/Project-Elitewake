#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EWFishDefinition.generated.h"

class UEWItemDefinition;
class UStaticMesh;

UENUM(BlueprintType)
enum class EEWWaterKind : uint8 { Salt, Fresh };

/** One kind of fish or sea creature: how it looks, where it lives, how it behaves and what it yields. Numbers are
 *  tuning unless the design reference says otherwise. */
UCLASS(BlueprintType)
class EW_API UEWFishDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Fish")
    FText DisplayName;
    /** Its body, built nose toward +X, as long as the creature. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Fish")
    TSoftObjectPtr<UStaticMesh> Mesh;
    /** Length and height of the body, in cm: the creature's reach for blows and its size for the camera. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Fish")
    FVector2D Size = FVector2D(50, 20);
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Fish")
    EEWWaterKind Water = EEWWaterKind::Salt;

    /** Aggressive creatures go for a swimmer who comes near; the rest swim off when struck. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    bool bAggressive = false;
    /** Cruising and hurrying speeds, cm/s, and how fast it turns, degrees per second. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float SwimSpeed = 120.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float DashSpeed = 300.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float TurnRate = 90.f;
    /** How far from its home it roams, and the depth below the surface it keeps to, in cm. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float RoamRadius = 1500.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float MinDepth = 80.f;
    /** It never goes deeper than this below the surface, so swimmers can reach it, in cm. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float MaxDepth = 400.f;
    /** An aggressive creature notices a swimmer this close, in cm. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float NoticeRange = 1200.f;
    /** Its bite or sting: health taken, seconds between, and reach beyond its nose, in cm. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float AttackDamage = 10.f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float AttackInterval = 1.5f;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    float AttackReach = 80.f;
    /** What its attack is called in the survivor's notice, for example "bite" or "sting". */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Behaviour")
    FText AttackName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest")
    float MaxHealth = 20.f;
    /** What harvesting the body on land gives, and how many: a number from YieldMin to YieldMax, drawn when it
     *  dies (owner, October 14: 2 to 5 for ordinary fish, 6 to 10 for sharks, the manatee and bigger creatures). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest")
    TObjectPtr<UEWItemDefinition> Yield;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="1"))
    int32 YieldMin = 2;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest", meta=(ClampMin="1"))
    int32 YieldMax = 5;
    /** Seconds before a killed creature returns to its home, harvested or not. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Harvest")
    float RespawnSeconds = 300.f;
};
