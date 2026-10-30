#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "EWWorldState.generated.h"

/** One placed resource as a save keeps it: its name in the map and what is left of it (wood and thatch for a tree, ore for a rock,
 *  the quantity for a pickup), a tree lying where it fell, and how long a depleted rock has before it comes back. */
USTRUCT(BlueprintType)
struct FEWSavedResource
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Save") FName Name;
    UPROPERTY(BlueprintReadOnly, Category="Save") int32 First = 0;
    UPROPERTY(BlueprintReadOnly, Category="Save") int32 Second = 0;
    UPROPERTY(BlueprintReadOnly, Category="Save") bool bFelled = false;
    UPROPERTY(BlueprintReadOnly, Category="Save") FTransform Transform;
    UPROPERTY(BlueprintReadOnly, Category="Save") float RespawnLeft = -1.f;
};

/** What has changed in the world's resources since the map was made (M7 persistence, October 30). */
USTRUCT(BlueprintType)
struct FEWSavedWorldState
{
    GENERATED_BODY()
    /** Placed trees, rocks and pickups that are gone (cut down, mined out, picked up). */
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FName> Removed;
    /** Placed ones partly used, or knocked over and lying. */
    UPROPERTY(BlueprintReadOnly, Category="Save") TArray<FEWSavedResource> Resources;
};

/**
 * The world's resources as play changes them (M7 persistence, October 30): which of the map's placed trees, rocks and pickups (hand
 * gatherables, items lying about) have gone, and which are partly used. The server keeps the list as play goes; the single-player
 * Save Game and the server's world save carry it, and loading puts the world back the same way: the gone stay gone, the used keep
 * what is left. Things spawned in play (not in the map) are not kept here.
 */
UCLASS()
class EW_API UEWWorldStateSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void OnWorldBeginPlay(UWorld& InWorld) override;
    virtual void Deinitialize() override;

    /** Authority: a placed resource changed (harvested, mined, picked from, knocked over). */
    static void Touch(AActor* Resource);
    static void Capture(UWorld* World, FEWSavedWorldState& Out);
    /** Authority: puts the saved state back on a freshly loaded world; returns how many resources were changed. */
    static int32 Restore(UWorld* World, const FEWSavedWorldState& State);

    UFUNCTION(BlueprintPure, Category="Save") int32 GetRemovedCount() const { return Removed.Num(); }
    UFUNCTION(BlueprintPure, Category="Save") int32 GetTouchedCount() const { return Touched.Num(); }

private:
    static bool IsTracked(const AActor* Actor);
    void ActorDestroyed(AActor* Actor);
    TSet<FName> Removed;
    TSet<TWeakObjectPtr<AActor>> Touched;
    FDelegateHandle DestroyedHandle;
};
