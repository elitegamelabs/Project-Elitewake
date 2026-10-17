#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Subsystems/WorldSubsystem.h"
#include "EWWindSubsystem.generated.h"

/** Carries the server's wind to every machine. Spawned by the wind subsystem on the server. */
UCLASS(NotPlaceable, Transient)
class EW_API AEWWindState : public AActor
{
    GENERATED_BODY()
public:
    AEWWindState();
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    UPROPERTY(Replicated)
    float WindYaw = 45.f;
};

/**
 * The world's wind. Ships read it on the server; every screen reads it for the compass and the sails.
 * It is constant until the weather system drives it.
 */
UCLASS()
class EW_API UEWWindSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void OnWorldBeginPlay(UWorld& InWorld) override;
    /** The wind of the world this object is in. */
    UFUNCTION(BlueprintPure, Category="Wind", meta=(WorldContext="WorldContext"))
    static UEWWindSubsystem* GetForWorld(const UObject* WorldContext);

    /** Direction the wind blows toward, as a world yaw in degrees. */
    UFUNCTION(BlueprintPure, Category="Wind")
    float GetWindYaw() const { return State ? State->WindYaw : WindYaw; }
    UFUNCTION(BlueprintPure, Category="Wind")
    FVector GetWindDirection() const { return FRotator(0, GetWindYaw(), 0).Vector(); }
    /** Server only. */
    UFUNCTION(BlueprintCallable, Category="Wind")
    void SetWindYaw(float NewYaw);

    /**
     * How much of a ship's sailing speed the wind allows for a given heading with its sails well trimmed: 1
     * running straight downwind, falling smoothly to MinUpwindFactor heading straight into the wind (tuning).
     */
    float GetHeadingFactor(const FVector& ShipForward) const;
    /** Owner, October 16: crossings were too slow, so the worst point of sail keeps 45% of top speed (was 30%). */
    static constexpr float MinUpwindFactor = .45f;

    /** Called by the replicated wind state as it arrives on a client. */
    void SetState(AEWWindState* InState) { State = InState; }

private:
    float WindYaw = 45.f;
    UPROPERTY(Transient)
    TObjectPtr<AEWWindState> State;
};
