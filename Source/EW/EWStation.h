#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWStation.generated.h"

class UStaticMeshComponent;
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
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Mesh;
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
