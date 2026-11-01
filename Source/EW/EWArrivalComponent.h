#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWArrivalComponent.generated.h"

class UEWCraftingRecipe;

/** The first things a new survivor is shown, one at a time, in this order (CLAUDE.md Phase 1, minutes 0-5). */
UENUM(BlueprintType)
enum class EEWArrivalStep : uint8 { Look, Move, Jump, Crouch, Interact, Done };

/** What Saltreach is for (CLAUDE.md Phase 1 slice 5, minutes 20-25), shown one at a time once the survivor is in the town. They
 *  may be done in any order; the first not yet done is the one shown. */
UENUM(BlueprintType)
enum class EEWTownStep : uint8 { Sell, Store, Shipyard, Company, Done };

/** What the survivor's own machine sees of them each frame: enough to tell whether a step's action has been done. */
struct FEWArrivalSnapshot
{
    FVector Location = FVector::ZeroVector;
    float Yaw = 0.f;
    float Pitch = 0.f;
    /** Leaving the ground upward under their own jump. */
    bool bJumping = false;
    /** Crouched or prone. */
    bool bLow = false;
};

/** Watches one step from the moment it is shown until its action is done. */
struct EW_API FEWArrivalTracker
{
    static constexpr float LookDegrees = 45.f;      // turning the view this far (yaw and pitch together) is looking around
    static constexpr float WalkDistance = 300.f;    // cm on foot is walking

    void Begin(EEWArrivalStep InStep, const FEWArrivalSnapshot& Now);
    /** True once the step's action has been done since Begin. The interact step is the server's to judge. */
    bool Update(const FEWArrivalSnapshot& Now);
    EEWArrivalStep Step = EEWArrivalStep::Done;
private:
    FEWArrivalSnapshot Start;
    FEWArrivalSnapshot Last;
    float Looked = 0.f;
};

/**
 * The arrival prompts (owner, October 31: CLAUDE.md Phase 1, slice 1): look, walk, jump, crouch, then use something (the
 * spring ahead), each taught by one prompt at a time and finished by doing it. Lives on the survivor so it is saved with them;
 * the step replicates to its owner only. Its own machine sees the first four done and tells the server; the server judges
 * the last itself, from a real interaction. Only maps whose PlayerStart is tagged "Arrival" run it; elsewhere, and for any
 * survivor restored from a save made before it existed, it starts finished.
 * Arriving there, a survivor also knows how to make their first tools by hand (FirstRecipes, slice 2): the stone hatchet
 * from sticks, stones and fiber, then the pickaxe from the wood it fells. Other maps keep their intro-gated recipes.
 * Reaching Saltreach afterwards (slice 5: inside a safe zone), the town steps follow the same way: sell or hand in something, put
 * something in the strongbox, talk to the shipwright, open the Company page. The server judges the first three from the real
 * action; the owning machine reports the last (a menu page, nothing to win by it).
 */
UCLASS(ClassGroup=(Elitewake), meta=(BlueprintSpawnableComponent))
class EW_API UEWArrivalComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWArrivalComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    static constexpr int32 StepCount = int32(EEWArrivalStep::Done);
    static inline const FName ArrivalStartTag = TEXT("Arrival");
    /** Seconds after arriving before the first prompt, so the first view is read without one (tuning). */
    static constexpr float FirstPromptDelay = 3.f;
    /** Seconds between one step's end and the next prompt (tuning). */
    static constexpr float StepGap = 1.f;

    /** The recipes a survivor arriving on an arrival map knows from the start, given each time they arrive (tuning). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Arrival") TArray<TSoftObjectPtr<UEWCraftingRecipe>> FirstRecipes;
    UFUNCTION(BlueprintPure, Category="Arrival") bool IsArrivalMap() const { return bArrivalMap; }

    UFUNCTION(BlueprintPure, Category="Arrival") int32 GetStepIndex() const { return Step; }
    UFUNCTION(BlueprintPure, Category="Arrival") EEWArrivalStep GetStep() const { return Step >= StepCount ? EEWArrivalStep::Done : EEWArrivalStep(Step); }
    UFUNCTION(BlueprintPure, Category="Arrival") bool IsComplete() const { return Step >= StepCount; }
    /** The owning machine: true while the current step's prompt should be on screen (not during the pauses). */
    UFUNCTION(BlueprintPure, Category="Arrival") bool IsPromptDue() const;
    /** The words for a step, for the keyboard and mouse or for a controller. */
    UFUNCTION(BlueprintPure, Category="Arrival") static FText PromptFor(EEWArrivalStep Step, bool bController);

    /** Authority: sets the step outright (a save being restored); clamped, so StepCount or more is finished. */
    UFUNCTION(BlueprintCallable, Category="Arrival") void SetStepIndex(int32 NewStep);
    /** Authority: the survivor used something. Finishes the interact step if it is the one shown. */
    void NoteInteracted();
    /** The owning machine: this step's action is done. The server accepts only the step it is on, never the interact step. */
    UFUNCTION(Server, Reliable) void ServerCompleteStep(int32 Completed);

    static constexpr int32 TownStepCount = int32(EEWTownStep::Done);
    static constexpr int32 AllTownSteps = (1 << TownStepCount) - 1;
    /** Which town steps are done, a bit each (bit n: EEWTownStep n). */
    UFUNCTION(BlueprintPure, Category="Arrival|Town") int32 GetTownStepsDone() const { return TownDone; }
    UFUNCTION(BlueprintPure, Category="Arrival|Town") bool IsTownStepDone(EEWTownStep Which) const { return Which >= EEWTownStep::Done || (TownDone & (1 << int32(Which))); }
    /** The first town step not yet done, or Done. */
    UFUNCTION(BlueprintPure, Category="Arrival|Town") EEWTownStep GetTownStep() const;
    UFUNCTION(BlueprintPure, Category="Arrival|Town") bool IsTownComplete() const { return (TownDone & AllTownSteps) == AllTownSteps; }
    /** The survivor stands inside a settlement's safe zone (Saltreach). */
    UFUNCTION(BlueprintPure, Category="Arrival|Town") bool IsInTown() const;
    /** The owning machine: true while a town step's prompt should be on screen (the arrival prompts finished, in town, not in a pause). */
    UFUNCTION(BlueprintPure, Category="Arrival|Town") bool IsTownPromptDue() const;
    UFUNCTION(BlueprintPure, Category="Arrival|Town") static FText TownPromptFor(EEWTownStep Step, bool bController);
    /** Where the shown town step is done (the nearest such place), for the compass; false when none is shown. */
    UFUNCTION(BlueprintPure, Category="Arrival|Town") bool GetTownTarget(FVector& OutLocation) const;
    /** Authority: the town steps outright (a save being restored). */
    UFUNCTION(BlueprintCallable, Category="Arrival|Town") void SetTownStepsDone(int32 Mask);
    /** Authority: the survivor did a town step's action for real (sold, stored, spoke to the shipwright). */
    void NoteTownStep(EEWTownStep Done);
    /** The owning machine: the Company page was opened. The server accepts only that step this way. */
    UFUNCTION(Server, Reliable) void ServerCompleteTownStep(int32 Completed);

private:
    UPROPERTY(ReplicatedUsing=OnRep_Step) int32 Step = 0;
    UFUNCTION() void OnRep_Step();
    UPROPERTY(ReplicatedUsing=OnRep_TownDone) int32 TownDone = 0;
    UFUNCTION() void OnRep_TownDone();
    void TickTown(double Time);
    /** The owning machine: in town at the last look, when the town prompt may next show, and when the Company page was last reported. */
    bool bWasInTown = false;
    double TownShowAt = 0.;
    double TownSentAt = -100.;
    void Advance();
    bool ReadSnapshot(FEWArrivalSnapshot& Out) const;

    FEWArrivalTracker Tracker;
    bool bArrivalMap = false;
    /** The owning machine's clock (seconds) when the current prompt may show, and when a completion was last sent. */
    double ShowAt = 0.;
    double SentAt = -100.;
    int32 SentFor = -1;
};
