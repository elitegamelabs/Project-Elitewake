// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWLessonComponent.generated.h"

/** The optional lessons (FUTURE_IMPLEMENTATIONS Part 8, 64-65). */
UENUM(BlueprintType)
enum class EEWLesson : uint8 { None, Sailing };

/**
 * Optional, skippable, replayable lessons (owner-approved November 7; built November 8). A Freeport's harbor master starts the
 * sailing lessons, stops them, or starts them again. The server watches the survivor's ship and moves on when each step is
 * done: aboard, anchor up, under way, at the helm and steering, the hold opened, the anchor down again; the last step, on
 * damage and bailing, is read and passes by itself. The step replicates to its player; the arrival prompt shows it, one at a
 * time, at the helm too. Kept on the player's controller; not saved (a lesson is started again from the harbor master).
 */
UCLASS(ClassGroup=(Elitewake), BlueprintType, meta=(BlueprintSpawnableComponent))
class EW_API UEWLessonComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWLessonComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** Authority: begin a lesson from its first step (again, if it was taken before). */
    UFUNCTION(BlueprintCallable, Category="Lessons") void StartLesson(EEWLesson Lesson);
    /** Authority: stop the lesson now. */
    UFUNCTION(BlueprintCallable, Category="Lessons") void StopLesson();
    UFUNCTION(BlueprintPure, Category="Lessons") EEWLesson GetLesson() const { return Lesson; }
    UFUNCTION(BlueprintPure, Category="Lessons") int32 GetStep() const { return Step; }
    UFUNCTION(BlueprintPure, Category="Lessons") bool IsInLesson() const { return Lesson != EEWLesson::None; }
    /** How many lessons this player finished this session (checks). */
    UFUNCTION(BlueprintPure, Category="Lessons") int32 GetFinishedCount() const { return Finished; }
    /** What the current step asks, in keyboard or controller words (button tokens as FEWControllerIcons expands them). */
    FText GetPrompt(bool bController) const;
    /** Authority: the player's ship's hold was just opened for them (AEWShip, at the hatch). */
    void NoteHoldOpened() { bHoldOpened = true; }
    static int32 StepCount(EEWLesson Of);
private:
    bool StepDone(int32 Index) const;
    UPROPERTY(Replicated) EEWLesson Lesson = EEWLesson::None;
    UPROPERTY(Replicated) int32 Step = 0;
    UPROPERTY(Replicated) int32 Finished = 0;
    float StepSeconds = 0.f;
    float UnderWaySeconds = 0.f;
    bool bHoldOpened = false;
};
