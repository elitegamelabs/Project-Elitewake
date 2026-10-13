#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Characters/EWAppearance.h"
#include "EWCharacterPreview.generated.h"

class UAnimSequence;
class USkeletalMeshComponent;

/** The survivor being made, standing in the character creator: wears a look, breathes in its idle, and turns. */
UCLASS(NotPlaceable)
class EW_API AEWCharacterPreview : public AActor
{
    GENERATED_BODY()
public:
    AEWCharacterPreview();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Preview")
    TObjectPtr<USkeletalMeshComponent> Body;
    UFUNCTION(BlueprintCallable, Category="Preview")
    void ShowAppearance(const FEWAppearance& Appearance, UEWBodyRoster* Roster);
    UFUNCTION(BlueprintCallable, Category="Preview")
    void Turn(float Degrees);
private:
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> Idle;
};
