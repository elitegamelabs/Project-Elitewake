#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "Wildlife/EWWildlifeRest.h"
#include "EWFish.generated.h"

class AEWCharacter;
class UEWFishDefinition;
class USphereComponent;
class UStaticMeshComponent;

/**
 * A fish or sea creature living in the water about a home point. The server moves it: it roams; aggressive kinds
 * go for a swimmer who comes near and bite or sting; the rest dart away when struck. Survivors strike it with
 * melee, with whatever they hold. Killed, it floats belly-up at the surface. Interact picks the body up to carry;
 * Interact again sets it down. Set down on land, Interact harvests it for its yield. It returns home later.
 * Clients glide to each replicated position; a carried body follows its carrier on every screen.
 */
UCLASS()
class EW_API AEWFish : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWFish();
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void PostNetReceiveLocationAndRotation() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Fish")
    TObjectPtr<USphereComponent> Body;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Fish")
    TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Fish")
    TObjectPtr<UEWFishDefinition> Definition;
    /** Height of the water surface it lives under, in world cm. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Fish")
    float SurfaceZ = -65.f;

    UFUNCTION(BlueprintPure, Category="Fish")
    float GetHealth() const { return Health; }
    UFUNCTION(BlueprintPure, Category="Fish")
    bool IsDead() const { return bDead; }
    UFUNCTION(BlueprintPure, Category="Fish")
    bool IsHarvested() const { return bHarvested; }
    /** The survivor it is going for, if any (server). */
    UFUNCTION(BlueprintPure, Category="Fish")
    AEWCharacter* GetQuarry() const { return Quarry.Get(); }
    UFUNCTION(BlueprintPure, Category="Fish")
    FVector GetHome() const { return Home; }
    /** Who carries the body, if anyone; and whether it lies on land, where it can be harvested. */
    UFUNCTION(BlueprintPure, Category="Fish")
    AEWCharacter* GetCarrier() const { return Carrier; }
    UFUNCTION(BlueprintPure, Category="Fish")
    bool IsOnLand() const { return bOnLand; }
    /** Server: how much the body still gives. */
    UFUNCTION(BlueprintPure, Category="Fish")
    int32 GetYieldLeft() const { return YieldLeft; }
    /** Authority: the carrier lets go of the body in front of them, onto land or into the water. */
    void SetDown();

    /** Authority only: a survivor's blow. Returns true if it landed. */
    bool TakeStrike(AEWCharacter* Striker, float Damage);
    /** The live creature a survivor's swing would hit: in front of them, within reach of their arm. */
    static AEWFish* FindStruck(const AEWCharacter* Striker, float Reach);

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return EEWInteractionMode::Press; }
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** How near a survivor must be to harvest the body, in cm (tuning). */
    static constexpr float HarvestReach = 350.f;

private:
    UPROPERTY(Replicated)
    float Health = 1.f;
    UPROPERTY(ReplicatedUsing=OnRep_State)
    bool bDead = false;
    UPROPERTY(ReplicatedUsing=OnRep_State)
    bool bHarvested = false;
    UPROPERTY(ReplicatedUsing=OnRep_State)
    TObjectPtr<AEWCharacter> Carrier;
    UPROPERTY(Replicated)
    bool bOnLand = false;
    /** Where a carried body rides: a small one over the shoulder, a big one dragged behind. */
    FTransform CarryPose() const;
    UFUNCTION()
    void OnRep_State();
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastFlinch();

    void ApplyDefinition();
    void Think(float DeltaSeconds);
    void SwimToward(const FVector& Target, float Speed, float DeltaSeconds);
    FVector PickRoamPoint() const;
    float FloorBelow(const FVector& At) const;
    void Die();
    void Respawn();
    bool IsInWater(const AEWCharacter* Survivor) const;

    FVector Home = FVector::ZeroVector;
    FVector RoamPoint = FVector::ZeroVector;
    float RoamSeconds = 0.f;
    TWeakObjectPtr<AEWCharacter> Quarry;
    TWeakObjectPtr<AEWCharacter> FleeFrom;
    float FleeSeconds = 0.f;
    float AttackCooldown = 0.f;
    float DeadSeconds = 0.f;
    float FlinchSeconds = 0.f;
    FEWWildlifeRest Rest;
    /** Server: how much of the yield is still on the body. */
    int32 YieldLeft = 0;
    /** Clients: the latest replicated pose, glided to. */
    FTransform NetPose;
    bool bHasNetPose = false;
};
