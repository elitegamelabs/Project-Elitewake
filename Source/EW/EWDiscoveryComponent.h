// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "World/EWPlaces.h"
#include "EWDiscoveryComponent.generated.h"

/** One thing a survivor has discovered: a named place or the first sight of a kind of creature. */
USTRUCT(BlueprintType)
struct FEWDiscovery
{
    GENERATED_BODY()
    /** A place's id (EWPlaces) or a creature definition's asset name. */
    UPROPERTY(BlueprintReadOnly, Category="Discovery") FName Id;
    UPROPERTY(BlueprintReadOnly, Category="Discovery") EEWPlaceKind Kind = EEWPlaceKind::Island;
    UPROPERTY(BlueprintReadOnly, Category="Discovery") FText Name;
    UPROPERTY(BlueprintReadOnly, Category="Discovery") FText Note;
};

/**
 * The Captain's discovery journal (FUTURE_IMPLEMENTATIONS Part 8, 63; owner-approved November 7): the server notes each named
 * place a survivor reaches (an island, a Freeport, a reef, a cave) and each kind of creature they come close to, once. Each new
 * discovery is announced on the HUD, earns a little experience and is written in the Journal's Discoveries pages. Kept on the
 * player's controller beside their exploration, saved with the survivor (UEWSurvivorSave::Discoveries), shown to its owner only.
 */
UCLASS(ClassGroup=(Elitewake), BlueprintType, meta=(BlueprintSpawnableComponent))
class EW_API UEWDiscoveryComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWDiscoveryComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** How close a living creature must come to be noted, cm. */
    UPROPERTY(EditDefaultsOnly, Category="Discovery", meta=(ClampMin="100")) float CreatureRange = 3000.f;
    /** Experience for a new discovery, by kind (tuning). */
    UPROPERTY(EditDefaultsOnly, Category="Discovery") int32 XpIsland = 40;
    UPROPERTY(EditDefaultsOnly, Category="Discovery") int32 XpPlace = 25;
    UPROPERTY(EditDefaultsOnly, Category="Discovery") int32 XpCreature = 10;

    UFUNCTION(BlueprintPure, Category="Discovery") const TArray<FEWDiscovery>& GetDiscoveries() const { return Discoveries; }
    UFUNCTION(BlueprintPure, Category="Discovery") bool HasDiscovered(FName Id) const;
    UFUNCTION(BlueprintPure, Category="Discovery") int32 CountOf(EEWPlaceKind Kind) const;
    /** How many places of the kind the world holds (creatures: 0, the count is open). */
    UFUNCTION(BlueprintPure, Category="Discovery") static int32 PlacesOf(EEWPlaceKind Kind);

    /** Authority only: notes a discovery if it is new. Returns true when it was. */
    bool Discover(FName Id, EEWPlaceKind Kind, const FText& Name, const FText& Note);
    /** Authority only: checks where the player's survivor stands now (the tick does this every second). */
    UFUNCTION(BlueprintCallable, Category="Discovery") void CheckNow();
    /** Authority only: puts back what a save held, without announcing any of it. */
    void Restore(const TArray<FEWDiscovery>& Saved);
    /** Authority only: forgets everything (a new survivor). */
    void ForgetAll();

    /** On the owner's screen: takes the oldest discovery still to announce, one at a time (the HUD shows each in turn). */
    bool PopAnnouncement(FEWDiscovery& Out);
    /** Discoveries announced on this screen so far (tests). */
    UFUNCTION(BlueprintPure, Category="Discovery") int32 GetAnnouncedCount() const { return AnnouncedCount; }
private:
    UFUNCTION() void OnRep_Discoveries();
    void Announce(int32 Index);
    UPROPERTY(ReplicatedUsing=OnRep_Discoveries) TArray<FEWDiscovery> Discoveries;
    /** Entries before this were restored from a save, not found just now: never announced. */
    UPROPERTY(Replicated) int32 RestoredCount = 0;
    int32 SeenCount = 0;
    TArray<int32> Pending;
    int32 AnnouncedCount = 0;
};
