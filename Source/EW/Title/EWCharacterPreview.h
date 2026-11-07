#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Characters/EWAppearance.h"
#include "EWCharacterPreview.generated.h"

class UAnimSequence;
class UPoseableMeshComponent;
class USkeletalMeshComponent;
class UEWBodyRoster;

/**
 * The survivor being made, standing in the character creator: wears a look, breathes in its idle, and turns. A hidden
 * body plays the idle; the shown body copies its pose each frame and reshapes its bones by the body sliders.
 */
UCLASS(NotPlaceable)
class EW_API AEWCharacterPreview : public AActor
{
    GENERATED_BODY()
public:
    AEWCharacterPreview();
    virtual void Tick(float DeltaSeconds) override;
    /** Plays the idle (hidden). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Preview")
    TObjectPtr<USkeletalMeshComponent> Body;
    /** What is seen: the idle's pose, reshaped. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Preview")
    TObjectPtr<UPoseableMeshComponent> Shown;
    UFUNCTION(BlueprintCallable, Category="Preview")
    void ShowAppearance(const FEWAppearance& Appearance, UEWBodyRoster* Roster);
    UFUNCTION(BlueprintCallable, Category="Preview")
    void Turn(float Degrees);
    /** The shown body's bone scale (its own axes, after the sliders), for checks. */
    UFUNCTION(BlueprintPure, Category="Preview")
    FVector GetBoneShape(FName Bone) const;
private:
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> Idle;
    TArray<FVector> Shape;
};
