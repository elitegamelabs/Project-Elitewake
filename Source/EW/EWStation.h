#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWStation.generated.h"

class UStaticMeshComponent;
class UCapsuleComponent;
UENUM(BlueprintType)
enum class EEWStationType : uint8 { Campfire, Smithy };

/** Explicit opt-in interaction fixture. Acknowledges only; no crafting, yields or storage. */
UCLASS(Blueprintable)
class EW_API AEWStation : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWStation();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    virtual void OnConstruction(const FTransform& Transform) override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Mesh;
    /** Optional solid core that people and cameras cannot pass, such as a tree's trunk, standing upright from the
     *  actor's origin. Aiming still uses the mesh. Off while its radius is 0. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UCapsuleComponent> Blocker;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Fixture", meta=(ClampMin="0")) float BlockerRadius = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Fixture", meta=(ClampMin="0")) float BlockerHalfHeight = 0.f;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category="Fixture") EEWStationType StationType = EEWStationType::Campfire;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category="Fixture") EEWInteractionMode Mode = EEWInteractionMode::Press;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category="Fixture", meta=(ClampMin="0.01")) float HoldDuration = 1.f;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category="Fixture") bool bAvailable = true;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category="Fixture") bool bSingleUse = false;
    UFUNCTION(BlueprintPure, Category="Fixture") int32 GetAcknowledgementCount() const { return Acknowledgements; }
    virtual bool CanInteract_Implementation(AEWCharacter* Survivor) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return Mode; }
    virtual float GetHoldDuration_Implementation() const override { return HoldDuration; }
    virtual bool Interact_Implementation(AEWCharacter* Survivor) override;
private:
    UPROPERTY(Replicated) int32 Acknowledgements = 0;
    bool bAcknowledging = false;
};
