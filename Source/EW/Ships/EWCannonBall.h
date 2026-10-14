#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWCannonBall.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UProjectileMovementComponent;
class AEWShip;
class AEWCharacter;

/**
 * Round shot fired from a ship's cannon. The server owns its flight; every screen sees it fly. It falls under
 * gravity, ends in the sea where it drops below the surface, and ends against whatever solid it strikes first,
 * never the ship that fired it.
 */
UCLASS()
class EW_API AEWCannonBall : public AActor
{
    GENERATED_BODY()
public:
    AEWCannonBall();
    /** Authority only: sets off at Velocity from where it was spawned. */
    void Launch(AEWShip* From, AEWCharacter* Gunner, const FVector& Velocity);
    virtual void Tick(float DeltaSeconds) override;
    virtual void BeginPlay() override;
    virtual void PostNetReceiveVelocity(const FVector& NewVelocity) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintPure, Category="Cannon")
    AEWShip* GetFiredFrom() const { return FiredFrom.Get(); }
    UFUNCTION(BlueprintPure, Category="Cannon")
    AEWCharacter* GetGunner() const { return Gunner.Get(); }
    /** Where it ended and what it struck (none for the sea), once it has. */
    UFUNCTION(BlueprintPure, Category="Cannon")
    bool HasLanded() const { return bLanded; }
    UFUNCTION(BlueprintPure, Category="Cannon")
    FVector GetLandedAt() const { return LandedAt; }
    UFUNCTION(BlueprintPure, Category="Cannon")
    AActor* GetStruck() const { return Struck.Get(); }

    /** The most recent shots fired in this world, newest last, for the checks: a shot is gone soon after it lands. */
    static TArray<TWeakObjectPtr<AEWCannonBall>> RecentShots;
    UFUNCTION(BlueprintPure, Category="Cannon", meta=(WorldContext="WorldContext"))
    static AEWCannonBall* GetLastShot(const UObject* WorldContext);

    static constexpr float Radius = 8.f;

private:
    UPROPERTY(VisibleAnywhere, Category="Cannon")
    TObjectPtr<USphereComponent> Collision;
    UPROPERTY(VisibleAnywhere, Category="Cannon")
    TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere, Category="Cannon")
    TObjectPtr<UProjectileMovementComponent> Movement;
    TWeakObjectPtr<AEWShip> FiredFrom;
    TWeakObjectPtr<AEWCharacter> Gunner;
    TWeakObjectPtr<AActor> Struck;
    float WaterZ = -65.f;
    UPROPERTY(ReplicatedUsing=OnRep_Landed)
    bool bLanded = false;
    UPROPERTY(Replicated)
    FVector LandedAt = FVector::ZeroVector;
    UFUNCTION()
    void OnRep_Landed();

    UFUNCTION()
    void OnStopped(const FHitResult& Hit);
    void Land(const FVector& Where, AActor* Hit);
};
