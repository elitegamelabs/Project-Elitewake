#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "EWInteractable.generated.h"

class AEWCharacter;

UENUM(BlueprintType)
enum class EEWInteractionMode : uint8 { Press, Hold };

UINTERFACE(BlueprintType)
class EW_API UEWInteractable : public UInterface
{
    GENERATED_BODY()
};

/** Queries never mutate gameplay. Interact must validate authority in every implementation. */
class EW_API IEWInteractable
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    bool CanInteract(AEWCharacter* Character) const;
    virtual bool CanInteract_Implementation(AEWCharacter* Character) const;
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    FText GetInteractionPrompt(AEWCharacter* Character) const;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const;
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    EEWInteractionMode GetInteractionMode() const;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const;
    /** Press or hold for what this survivor aims at; by default the actor's own mode. A ship's ladder takes a
     *  press while its fittings take a hold. */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    EEWInteractionMode GetInteractionModeFor(AEWCharacter* Character) const;
    virtual EEWInteractionMode GetInteractionModeFor_Implementation(AEWCharacter* Character) const;
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    float GetHoldDuration() const;
    virtual float GetHoldDuration_Implementation() const;
    /** How long this survivor holds Interact for what they aim at; by default the actor's own duration. A ship's
     *  capstan takes longer than its fittings. */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    float GetHoldDurationFor(AEWCharacter* Character) const;
    virtual float GetHoldDurationFor_Implementation(AEWCharacter* Character) const;
    /** Authority only: a survivor's hold on this actor began, or ended (finished or not). */
    UFUNCTION(BlueprintNativeEvent, BlueprintAuthorityOnly, Category="Interaction")
    void HoldChanged(AEWCharacter* Character, bool bHolding);
    virtual void HoldChanged_Implementation(AEWCharacter* Character, bool bHolding);
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, BlueprintAuthorityOnly, Category="Interaction")
    bool Interact(AEWCharacter* Character);
    virtual bool Interact_Implementation(AEWCharacter* Character);
};

/** Shared eye trace used for local presentation and authoritative targeting. */
struct EW_API FEWInteractionTargeting
{
    static constexpr float Range = 250.f;
    static AActor* FindTarget(const AEWCharacter* Character);
};
