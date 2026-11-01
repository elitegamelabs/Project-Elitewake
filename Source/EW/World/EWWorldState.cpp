#include "World/EWWorldState.h"
#include "EWPickup.h"
#include "EWDeathBag.h"
#include "Ships/EWWreckCrate.h"
#include "World/EWCampfire.h"
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
    for (TActorIterator<AEWDeathBag> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed() && It->GetContents() && It->GetContents()->GetUsedSlotCount() > 0) Out.Containers.Add(It->CaptureForSave());
    for (TActorIterator<AEWWreckCrate> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed() && It->GetContents() && It->GetContents()->GetUsedSlotCount() > 0) Out.Containers.Add(It->CaptureForSave());
    for (TActorIterator<AEWCampfire> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed()) Out.Campfires.Add(It->CaptureForSave());
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
    // Bags and crates from before this load are not the save's: they go, and the save's own come back.
    for (TActorIterator<AEWDeathBag> It(World); It; ++It) It->Destroy();
    for (TActorIterator<AEWWreckCrate> It(World); It; ++It) It->Destroy();
    for (const FEWSavedContainer& Saved : State.Containers)
    {
        if (Saved.LifeLeft <= 0.f || Saved.Contents.IsEmpty()) continue;
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        if (Saved.bWreckCrate)
        {
            if (auto* Crate = World->SpawnActor<AEWWreckCrate>(AEWWreckCrate::StaticClass(), Saved.Transform, Params)) { Crate->RestoreSaved(Saved); ++Changed; }
        }
        else if (auto* Bag = World->SpawnActor<AEWDeathBag>(AEWDeathBag::StaticClass(), Saved.Transform, Params)) { Bag->RestoreSaved(Saved); ++Changed; }
    }
    // Campfires likewise: the ones laid since the load go, the save's come back burning as they were.
    for (TActorIterator<AEWCampfire> It(World); It; ++It) It->Destroy();
    for (const FEWSavedCampfire& Saved : State.Campfires)
    {
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        if (auto* Fire = World->SpawnActor<AEWCampfire>(AEWCampfire::StaticClass(), Saved.Transform, Params)) { Fire->RestoreSaved(Saved); ++Changed; }
    }
    return Changed;
}
