#include "World/EWWorldState.h"
#include "EWPickup.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Gathering/EWHarvestTree.h"
#include "Gathering/EWMineable.h"

bool UEWWorldStateSubsystem::IsTracked(const AActor* Actor)
{
    return IsValid(Actor) && Actor->IsNetStartupActor()
        && (Actor->IsA<AEWHarvestTree>() || Actor->IsA<AEWMineable>() || Actor->IsA<AEWPickup>());
}

void UEWWorldStateSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
    Super::OnWorldBeginPlay(InWorld);
    if (InWorld.GetNetMode() == NM_Client) return;
    DestroyedHandle = InWorld.AddOnActorDestroyedHandler(FOnActorDestroyed::FDelegate::CreateUObject(this, &UEWWorldStateSubsystem::ActorDestroyed));
}

void UEWWorldStateSubsystem::Deinitialize()
{
    if (UWorld* World = GetWorld(); World && DestroyedHandle.IsValid()) World->RemoveOnActorDestroyedHandler(DestroyedHandle);
    Super::Deinitialize();
}

void UEWWorldStateSubsystem::ActorDestroyed(AActor* Actor)
{
    // Only a resource of the map going away during play: not the world itself being torn down.
    if (!Actor || !IsTracked(Actor) || !GetWorld() || GetWorld()->bIsTearingDown || !GetWorld()->HasBegunPlay()) return;
    Removed.Add(Actor->GetFName());
    Touched.Remove(Actor);
}

void UEWWorldStateSubsystem::Touch(AActor* Resource)
{
    if (!IsTracked(Resource) || !Resource->HasAuthority()) return;
    if (auto* Self = Resource->GetWorld() ? Resource->GetWorld()->GetSubsystem<UEWWorldStateSubsystem>() : nullptr) Self->Touched.Add(Resource);
}

void UEWWorldStateSubsystem::Capture(UWorld* World, FEWSavedWorldState& Out)
{
    Out = FEWSavedWorldState();
    const auto* Self = World && World->GetNetMode() != NM_Client ? World->GetSubsystem<UEWWorldStateSubsystem>() : nullptr;
    if (!Self) return;
    Out.Removed = Self->Removed.Array();
    for (const TWeakObjectPtr<AActor>& Weak : Self->Touched)
    {
        const AActor* Actor = Weak.Get();
        if (!IsValid(Actor) || Actor->IsActorBeingDestroyed()) continue;
        FEWSavedResource Saved;
        Saved.Name = Actor->GetFName();
        Saved.Transform = Actor->GetActorTransform();
        if (const auto* Tree = Cast<AEWHarvestTree>(Actor))
        {
            Saved.First = Tree->WoodRemaining;
            Saved.Second = Tree->ThatchRemaining;
            Saved.bFelled = Tree->IsFelled();
        }
        else if (const auto* Rock = Cast<AEWMineable>(Actor))
        {
            Saved.First = Rock->Remaining;
            Saved.RespawnLeft = Rock->GetRespawnLeft();
        }
        else if (const auto* Pickup = Cast<AEWPickup>(Actor)) Saved.First = Pickup->Quantity;
        Out.Resources.Add(Saved);
    }
}

int32 UEWWorldStateSubsystem::Restore(UWorld* World, const FEWSavedWorldState& State)
{
    if (!World || World->GetNetMode() == NM_Client) return 0;
    TMap<FName, AActor*> Placed;
    for (TActorIterator<AEWHarvestTree> It(World); It; ++It) if (It->IsNetStartupActor()) Placed.Add(It->GetFName(), *It);
    for (TActorIterator<AEWMineable> It(World); It; ++It) if (It->IsNetStartupActor()) Placed.Add(It->GetFName(), *It);
    for (TActorIterator<AEWPickup> It(World); It; ++It) if (It->IsNetStartupActor()) Placed.Add(It->GetFName(), *It);
    int32 Changed = 0;
    for (const FName& Name : State.Removed)
        if (AActor** Found = Placed.Find(Name)) { (*Found)->Destroy(); ++Changed; }
    for (const FEWSavedResource& Saved : State.Resources)
    {
        AActor** Found = Placed.Find(Saved.Name);
        if (!Found || !IsValid(*Found)) continue;
        if (auto* Tree = Cast<AEWHarvestTree>(*Found)) Tree->RestoreSaved(Saved.First, Saved.Second, Saved.bFelled, Saved.Transform);
        else if (auto* Rock = Cast<AEWMineable>(*Found)) Rock->RestoreSaved(Saved.First, Saved.RespawnLeft);
        else if (auto* Pickup = Cast<AEWPickup>(*Found)) Pickup->RestoreSaved(Saved.First);
        Touch(*Found);
        ++Changed;
    }
    return Changed;
}
