#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWTownsfolk.generated.h"

class AEWCharacter;
class UAnimSequence;
class UCapsuleComponent;
class UMaterialInterface;
class USkeletalMesh;
class USkeletalMeshComponent;

/** One choice in a dialogue window: a key the server acts on, the line the survivor reads, and whether it can be chosen now. */
USTRUCT(BlueprintType)
struct FEWDialogueOption
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Dialogue") FName Key;
    UPROPERTY(BlueprintReadOnly, Category="Dialogue") FText Label;
    UPROPERTY(BlueprintReadOnly, Category="Dialogue") bool bEnabled = true;
};

/**
 * A named person of a town (owner, October 30: the Freeport's NPCs have a name, a role, a place, a prompt and a dialogue window).
 * Pressing Interact on one with a name opens a dialogue window on the survivor's screen: their greeting and a list of choices.
 * The choices are worked out from replicated state on each side; choosing one asks the server, which checks it again, acts and
 * answers with a line. Subclasses add their trade (merchant, crew recruiter, shipwright, tavern keeper, harbor master).
 * The figure is the engine's mannequin playing a looping idle or walk until the owner's character art; a person with stroll
 * points walks them in a loop, pausing at each, worked out from the server's clock so every screen agrees without replication.
 */
UCLASS()
class EW_API AEWTownsfolk : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWTownsfolk();

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual EEWInteractionMode GetInteractionMode_Implementation() const override { return EEWInteractionMode::Press; }
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** Someone to talk to: a person with a name opens a dialogue window. */
    UFUNCTION(BlueprintPure, Category="Townsfolk") bool HasDialogue() const { return !NpcName.IsEmpty(); }
    /** What they say when the window opens. */
    UFUNCTION(BlueprintPure, Category="Townsfolk") virtual FText GetDialogueGreeting(const AEWCharacter* Character) const;
    /** The choices this survivor has now (the window lists them in order; Leave is the window's own). */
    UFUNCTION(BlueprintPure, Category="Townsfolk") TArray<FEWDialogueOption> GetDialogueOptionsFor(const AEWCharacter* Character) const;
    /** Authority: the survivor chose Key. Checks reach and that the choice is open to them, acts, and returns the answer. */
    UFUNCTION(BlueprintCallable, Category="Townsfolk") FText ChooseDialogue(AEWCharacter* Character, FName Key);
    /** Within reach to talk (and to trade). */
    bool IsInReach(const AEWCharacter* Character) const;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk") FText NpcName;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk") FText RoleTitle;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk", meta=(MultiLine="true")) FText Greeting;
    /** What they say when asked for a word (one after another). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk") TArray<FText> SmallTalk;

    /** The figure: a skeletal mesh (none keeps a subclass's own placeholder shapes), its material, and looping idle and walk animations. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk|Figure") TObjectPtr<USkeletalMesh> FigureMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk|Figure") TObjectPtr<UMaterialInterface> FigureMaterial;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk|Figure") TObjectPtr<UAnimSequence> IdleAnim;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk|Figure") TObjectPtr<UAnimSequence> WalkAnim;
    /** Where they walk, in the world, looped (empty: they stay where they were placed). Tuning: speed (cm/s) and the pause at each point (s). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk|Stroll") TArray<FVector> StrollPoints;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk|Stroll", meta=(ClampMin="10")) float StrollSpeed = 115.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Townsfolk|Stroll", meta=(ClampMin="0")) float StrollPause = 5.f;

    UFUNCTION(BlueprintPure, Category="Townsfolk") bool IsWalking() const { return bWalking; }
    static constexpr float TalkReach = 450.f;

protected:
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    /** The choices a subclass offers (after these the base adds a word of small talk). */
    virtual void GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const {}
    /** Authority: act on a subclass's choice; return the line said back (empty if the key is not theirs). */
    virtual FText ActOnDialogue(AEWCharacter* Character, FName Key) { return FText::GetEmpty(); }
    /** Where along the stroll they are at a time, and which way they face; true while walking. */
    bool StrollPose(double Time, FVector& OutWhere, float& OutYaw) const;

    UPROPERTY(VisibleAnywhere, Category="Townsfolk") TObjectPtr<UCapsuleComponent> Capsule;
    UPROPERTY(VisibleAnywhere, Category="Townsfolk") TObjectPtr<USkeletalMeshComponent> Figure;

private:
    void PlayFigure(bool bWalk);
    bool bWalking = false;
    bool bFigureStarted = false;
    int32 NextSmallTalk = 0;
    TArray<float> LegStart;     // seconds from the loop's start at which each leg (pause then walk) begins
    float LoopSeconds = 0.f;
};
