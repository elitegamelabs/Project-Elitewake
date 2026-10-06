#pragma once

#include "GameFramework/CharacterMovementComponent.h"
#include "EWCharacterMovementComponent.generated.h"

/** Stance clearance and prone body sweeps participate in normal predicted movement. */
UCLASS()
class EW_API UEWCharacterMovementComponent : public UCharacterMovementComponent
{
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, Category="Movement|Stance", meta=(ClampMin="1", Units="cm"))
    float CrouchClearanceHalfHeight = 60.f;

    UPROPERTY(EditDefaultsOnly, Category="Movement|Stance", meta=(ClampMin="1", Units="cm"))
    float ProneCapsuleRadius = 28.f;

    UPROPERTY(EditDefaultsOnly, Category="Movement|Stance", meta=(ClampMin="1", Units="cm"))
    float ProneBodyHalfLength = 105.f;

    bool bWantsToProne = false;

    virtual void Crouch(bool bClientSimulation = false) override;
    virtual void UnCrouch(bool bClientSimulation = false) override;
    virtual void UpdateCharacterStateBeforeMovement(float DeltaSeconds) override;
    virtual void UpdateFromCompressedFlags(uint8 Flags) override;
    virtual FNetworkPredictionData_Client* GetPredictionData_Client() const override;

    /** Apply replicated size without running authority clearance checks on a remote proxy. */
    void RefreshProxyStance();

protected:
    virtual bool MoveUpdatedComponentImpl(const FVector& Delta, const FQuat& NewRotation,
        bool bSweep, FHitResult* OutHit = nullptr, ETeleportType Teleport = ETeleportType::None) override;

private:
    bool ResizeStance(bool bProne, bool bStanding, bool bClientSimulation);
    bool BodyBlocked(const FVector& CapsuleLocation, const FQuat& ActorRotation,
        float CapsuleHalfHeight) const;
    FVector BodyCenter(const FVector& CapsuleLocation, float CapsuleHalfHeight) const;
    FQuat BodyRotation(const FQuat& ActorRotation) const;
    float StandingStepHeight = -1.f;
};

class FEWSavedMove : public FSavedMove_Character
{
public:
    using Super = FSavedMove_Character;
    bool bSavedWantsToProne = false;
    bool bSavedSprintInputHeld = false;
    virtual void Clear() override;
    virtual uint8 GetCompressedFlags() const override;
    virtual bool CanCombineWith(const FSavedMovePtr& NewMove, ACharacter* Character, float MaxDelta) const override;
    virtual void SetMoveFor(ACharacter* Character, float InDeltaTime, const FVector& NewAcceleration,
        FNetworkPredictionData_Client_Character& ClientData) override;
    virtual void PrepMoveFor(ACharacter* Character) override;
};
