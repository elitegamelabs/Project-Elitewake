#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "Wildlife/EWWildlifeRest.h"
#include "Wildlife/EWAnimalDefinition.h"
#include "EWAnimal.generated.h"

class AEWCharacter;
class UEWAnimalDefinition;
class USphereComponent;
class UStaticMeshComponent;

/**
 * A land animal living about a home point on an island. The server moves it over the ground: it wanders and
 * stands; aggressive kinds go for a survivor who comes near on land and bite; the rest run off when struck.
 * Survivors strike it with melee, with whatever they hold. Killed, it drops on its side where it fell; Interact
 * harvests it for its yield. It returns home later. Clients glide to each replicated position, and every screen
 * walks its legs at the pace it is moving (the material reads the gait from custom primitive data: 0 the stride's
 * phase in radians, 1 how much it is striding, 2 whether it is dead).
 */
UCLASS()
class EW_API AEWAnimal : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWAnimal();
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void PostNetReceiveLocationAndRotation() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Animal")
    TObjectPtr<USphereComponent> Body;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Animal")
    TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Animal")
    TObjectPtr<UEWAnimalDefinition> Definition;
    /** Height of the sea around its island, in world cm: it keeps to the ground above it. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Animal")
    float SurfaceZ = -65.f;

    UFUNCTION(BlueprintPure, Category="Animal") float GetHealth() const { return Health; }
    UFUNCTION(BlueprintPure, Category="Animal") bool IsDead() const { return bDead; }
    UFUNCTION(BlueprintPure, Category="Animal") bool IsHarvested() const { return bHarvested; }
    UFUNCTION(BlueprintPure, Category="Animal") AEWCharacter* GetQuarry() const { return Quarry.Get(); }
    UFUNCTION(BlueprintPure, Category="Animal") FVector GetHome() const { return Home; }
    /** This screen's walking speed, cm/s, as its legs show it. */
    UFUNCTION(BlueprintPure, Category="Animal") float GetShownSpeed() const { return ShownSpeed; }
    UFUNCTION(BlueprintPure, Category="Animal") float GetStridePhase() const { return StridePhase; }
    /** What it is doing now (wandering, grazing, lying down, looking about, fleeing, chasing). */
    UFUNCTION(BlueprintPure, Category="Animal") EEWAnimalAction GetAction() const { return Action; }
    /** How far its body is lowered (lying down, 0..1) and its head bowed (grazing, 0..1), as shown. */
    UFUNCTION(BlueprintPure, Category="Animal") float GetLieShown() const { return LieShown; }
    UFUNCTION(BlueprintPure, Category="Animal") float GetGrazeShown() const { return GrazeShown; }

    UFUNCTION(BlueprintPure, Category="Animal") AEWCharacter* GetRider() const { return Rider; }
    /** Where a rider's centre sits, relative to this actor, for a capsule of the given half height. */
    FVector GetRideSeatLocal(float RiderHalfHeight) const;
    /** Authority: the rider's steering, a world-space direction on the ground (length 0 to 1; 0 stands still). */
    void SetRideSteer(AEWCharacter* Who, FVector2D Direction);
    /** Authority: the rider gets off, onto the ground beside it. */
    void Dismount();
    bool CanRide(const AEWCharacter* Character) const;

    /** Authority only: a survivor's blow. Returns true if it landed. */
    UFUNCTION(BlueprintCallable, Category="Wildlife")
    bool TakeStrike(AEWCharacter* Striker, float Damage);
    /** The live animal a survivor's swing would hit: in front of them, within reach of their arm. */
    static AEWAnimal* FindStruck(const AEWCharacter* Striker, float Reach);

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return EEWInteractionMode::Press; }
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** How near a survivor must be to harvest the body, in cm (tuning). */
    static constexpr float HarvestReach = 250.f;

private:
    UPROPERTY(Replicated)
    TObjectPtr<AEWCharacter> Rider;
    FVector2D RideDirection = FVector2D::ZeroVector;
    float RideSteerAge = 0.f;
    void ThinkRidden(float DeltaSeconds);
    UPROPERTY(Replicated)
    float Health = 1.f;
    UPROPERTY(Replicated)
    EEWAnimalAction Action = EEWAnimalAction::Wander;
    float LieShown = 0.f;
    float GrazeShown = 0.f;
    float LookYaw = 0.f;
    /** Authority: after a walk it stands and does something: graze, look about, or lie down. */
    void ChooseIdle();
    void PushTrees(float DeltaSeconds);
    float TreePushCooldown = 5.f;
    FVector Repulsion() const;
    UPROPERTY(ReplicatedUsing=OnRep_State)
    bool bDead = false;
    UPROPERTY(ReplicatedUsing=OnRep_State)
    bool bHarvested = false;
    UFUNCTION()
    void OnRep_State();
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastFlinch();
    /** Authority: it calls out, heard on every screen near; never twice within a few seconds. */
    void Call();
    /** Every machine: one of its attack (Kind 1) or death (Kind 2) sounds at the animal. */
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastCue(uint8 Kind);
    /** For the checks: attack and death sounds played on this machine. */
    UFUNCTION(BlueprintPure, Category="Wildlife") int32 GetCuesHeard() const { return CuesHeard; }
    int32 CuesHeard = 0;
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastCall();
    float CallSeconds = 0.f;
    FEWWildlifeRest Rest;
    double LastCallTime = -100.0;

    void ApplyDefinition();
    void Think(float DeltaSeconds);
    /** Steps toward Target over the ground. False if the way is blocked (sea, cliff), so it should pick elsewhere. */
    bool WalkToward(const FVector& Target, float Speed, float DeltaSeconds);
    bool GroundAt(const FVector& At, float& OutZ) const;
    FVector PickRoamPoint() const;
    bool IsAshore(const AEWCharacter* Survivor) const;
    void Die();
    void Respawn();
    void Animate(float DeltaSeconds);

    FVector Home = FVector::ZeroVector;
    FVector RoamPoint = FVector::ZeroVector;
    float RoamSeconds = 0.f;
    float RestSeconds = 0.f;
    TWeakObjectPtr<AEWCharacter> Quarry;
    TWeakObjectPtr<AEWCharacter> FleeFrom;
    float FleeSeconds = 0.f;
    /** A neutral animal (bDefendsItself) answering a blow: how long it keeps at its attacker. */
    float DefendSeconds = 0.f;
    /** Authority: close on Target and strike it when in reach (the attack aggressive and defending animals share). */
    void PressAttack(AEWCharacter* Target, float DeltaSeconds);
    float AttackCooldown = 0.f;
    float DeadSeconds = 0.f;
    float FlinchSeconds = 0.f;
    int32 YieldLeft = 0;
    /** Every screen: where it was last frame, its smoothed speed and its stride, for the legs. */
    FVector LastShown = FVector::ZeroVector;
    float ShownSpeed = 0.f;
    float StridePhase = 0.f;
    FTransform NetPose;
    bool bHasNetPose = false;
};
