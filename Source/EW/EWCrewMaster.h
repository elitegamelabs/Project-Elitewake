#pragma once
#include "CoreMinimal.h"
#include "EWMerchant.h"
#include "EWCrewMaster.generated.h"

class UEWItemDefinition;

/** A sailor waiting to be signed on at a Freeport recruiter: their name, whether they serve the guns or the sails, their fee and a word about them. */
USTRUCT(BlueprintType)
struct FEWCrewCandidate
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Crew") FString Name;
    UPROPERTY(BlueprintReadOnly, Category="Crew") bool bGunner = false;
    UPROPERTY(BlueprintReadOnly, Category="Crew") int32 Fee = 0;
    UPROPERTY(BlueprintReadOnly, Category="Crew") FString Note;
};

/**
 * A Port's crew master (owner, October 18: "purchased Port NPCs"; crew dependency). One press of Interact hires a sailhand:
 * it takes the fee from the survivor's purse and gives Sailhand's Articles, which sign the hand on at a sail's lines aboard.
 * A recruiter with a name (the Freeport's) keeps a roster of named sailors and gunners instead, browsed and signed in a dialogue window;
 * each signed sailor hands over the articles for their trade, and the roster fills again one sailor at a time. The name does not go
 * aboard with them yet (crew are anonymous hands aboard). Fees are placeholders for tuning.
 * The fee is a placeholder for tuning; wages, crew limits per hull and cannon crews are not built. Placeholder figure.
 */
UCLASS()
class EW_API AEWCrewMaster : public AEWMerchant
{
    GENERATED_BODY()
public:
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual bool Interact_Implementation(AEWCharacter* Character) override;

    /** The item handed over for the fee (set by Scripts/Setup/add_port_merchants.py). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew")
    TObjectPtr<UEWItemDefinition> Articles;
    /** Tuning: the fee for one sailhand, in Copper. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew")
    int64 HireCost = 100;
    /** Who is hired, as the prompt names them: "sailhand" or "gunner". */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew")
    FString CrewRole = TEXT("sailhand");

    /** A named recruiter's second trade: the gunner's articles and the base fee (tuning). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew") TObjectPtr<UEWItemDefinition> GunnerArticles;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew") int64 GunnerHireCost = 150;
    /** Tuning: how many sailors wait at once, and seconds between one more arriving. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew", meta=(ClampMin="1")) int32 RosterSize = 6;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Crew", meta=(ClampMin="1")) float RosterRefillSeconds = 240.f;

    UFUNCTION(BlueprintPure, Category="Crew") TArray<FEWCrewCandidate> GetRoster() const { return Roster; }
    /** Authority: sign the sailor at Index for their fee; their articles go into the pack. */
    UFUNCTION(BlueprintCallable, Category="Crew") bool HireCandidate(AEWCharacter* Character, int32 Index);
    /** Authority: one more sailor joins the roster, if there is room. */
    UFUNCTION(BlueprintCallable, Category="Crew") void AddCandidate();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;
    virtual FText GetDialogueGreeting(const AEWCharacter* Character) const override;
    virtual void GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const override;
    virtual FText ActOnDialogue(AEWCharacter* Character, FName Key) override;

private:
    bool GiveArticles(AEWCharacter* Character, UEWItemDefinition* Item, int64 Fee);
    UPROPERTY(Replicated) TArray<FEWCrewCandidate> Roster;
    FTimerHandle RosterTimer;
    int32 NextName = 0;
};
