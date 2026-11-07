#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWStarterKit.generated.h"

class AEWCharacter;
class APlayerState;
class UEWItemDefinition;

USTRUCT(BlueprintType)
struct FEWStarterKitItem
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Starter Kit")
    TObjectPtr<UEWItemDefinition> Item = nullptr;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Starter Kit", meta=(ClampMin="1"))
    int32 Quantity = 1;
};

/** Test maps only: gives each player's survivor a kit once per session and stocks each ship's hold at
 *  Play start, on the server. Normal starts place no kit, so survivors still begin with nothing. The survivor's
 *  kit is given only while ew.TestStarterKit is 1 (owner, October 31: the kit is a test setup, not the normal start;
 *  run_play_check.py turns it on for the checks that need it). Ships' holds are stocked either way. */
UCLASS()
class EW_API AEWStarterKit : public AActor
{
    GENERATED_BODY()
public:
    AEWStarterKit();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Carried by each survivor. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Starter Kit")
    TArray<FEWStarterKitItem> Items;
    /** Put in the hold of every ship that can use it; heavy fittings belong here rather than on a survivor's back.
     *  A fitting's Quantity is per matching mount, so each ship gets enough to fit out. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Starter Kit")
    TArray<FEWStarterKitItem> ShipCargo;

    /** Authority only. Gives the kit unless this player already had it. Returns true if given now. */
    UFUNCTION(BlueprintCallable, Category="Starter Kit")
    bool GiveKit(AEWCharacter* Survivor);

private:
    TSet<TWeakObjectPtr<APlayerState>> Given;
};
