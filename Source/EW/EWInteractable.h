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
