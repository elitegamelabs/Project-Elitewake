// Copyright Elite Game Labs. All Rights Reserved.

#include "EWDiscoveryComponent.h"
#include "EWCharacter.h"
#include "EWProgressionComponent.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Net/UnrealNetwork.h"
#include "Wildlife/EWAnimal.h"
#include "Wildlife/EWAnimalDefinition.h"

UEWDiscoveryComponent::UEWDiscoveryComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 1.f;
    SetIsReplicatedByDefault(true);
}

void UEWDiscoveryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWDiscoveryComponent, Discoveries, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWDiscoveryComponent, RestoredCount, COND_OwnerOnly);
}

bool UEWDiscoveryComponent::HasDiscovered(FName Id) const
{
    return Discoveries.ContainsByPredicate([Id](const FEWDiscovery& D) { return D.Id == Id; });
}

int32 UEWDiscoveryComponent::CountOf(EEWPlaceKind Kind) const
{
    int32 N = 0;
    for (const FEWDiscovery& D : Discoveries) if (D.Kind == Kind) ++N;
    return N;
}

int32 UEWDiscoveryComponent::PlacesOf(EEWPlaceKind Kind)
{
    int32 N = 0;
    for (const EWPlaces::FPlace& P : EWPlaces::All()) if (P.Kind == Kind) ++N;
    return N;
}

bool UEWDiscoveryComponent::Discover(FName Id, EEWPlaceKind Kind, const FText& Name, const FText& Note)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || Id.IsNone() || HasDiscovered(Id)) return false;
    FEWDiscovery& Found = Discoveries.AddDefaulted_GetRef();
    Found.Id = Id; Found.Kind = Kind; Found.Name = Name; Found.Note = Note;
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    if (const AEWCharacter* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr)
        if (UEWProgressionComponent* Progress = Survivor->GetProgressionComponent())
            Progress->GrantExperience(Kind == EEWPlaceKind::Island ? XpIsland : Kind == EEWPlaceKind::Creature ? XpCreature : XpPlace);
    GetOwner()->ForceNetUpdate();
    // A listen server's own player gets no replication: announce here.
    if (PC && PC->IsLocalController()) { SeenCount = Discoveries.Num(); Announce(Discoveries.Num() - 1); }
    return true;
}

void UEWDiscoveryComponent::CheckNow()
{
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    const AEWCharacter* Survivor = PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
    if (!Survivor || !GetOwner()->HasAuthority() || Survivor->IsDead()) return;
    const FVector Here = Survivor->GetActorLocation();
    for (const EWPlaces::FPlace& Place : EWPlaces::All())
        if (EWPlaces::IsAt(Place, Here))
            Discover(FName(Place.Id), Place.Kind, FText::FromString(Place.Name), FText::FromString(Place.Note));
    // Creatures: the first living one of its kind within reach. Every animal is always loaded and few in number (509).
    const double Reach = FMath::Square(double(CreatureRange));
    for (TActorIterator<AEWAnimal> It(GetWorld()); It; ++It)
    {
        const UEWAnimalDefinition* Kind = It->Definition;
        if (!Kind || It->IsDead() || FVector::DistSquared(It->GetActorLocation(), Here) > Reach) continue;
        const FName Id = Kind->GetFName();
        if (!HasDiscovered(Id))
            Discover(Id, EEWPlaceKind::Creature, Kind->DisplayName, NSLOCTEXT("Elitewake", "CreatureNote", "First seen in the wild."));
    }
}

void UEWDiscoveryComponent::Restore(const TArray<FEWDiscovery>& Saved)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    Discoveries.Reset();
    for (const FEWDiscovery& D : Saved)
        if (!D.Id.IsNone() && !HasDiscovered(D.Id)) Discoveries.Add(D);
    RestoredCount = Discoveries.Num();
    SeenCount = Discoveries.Num();
    Pending.Reset();
    GetOwner()->ForceNetUpdate();
}

void UEWDiscoveryComponent::ForgetAll()
{
    Restore(TArray<FEWDiscovery>());
}

void UEWDiscoveryComponent::OnRep_Discoveries()
{
    // Only what is new since the last update, and nothing put back from a save.
    if (Discoveries.Num() < SeenCount) { Pending.Reset(); SeenCount = 0; }
    for (int32 I = FMath::Max(SeenCount, RestoredCount); I < Discoveries.Num(); ++I) Announce(I);
    SeenCount = Discoveries.Num();
}

void UEWDiscoveryComponent::Announce(int32 Index)
{
    Pending.Add(Index);
}

bool UEWDiscoveryComponent::PopAnnouncement(FEWDiscovery& Out)
{
    while (Pending.Num() > 0)
    {
        const int32 Index = Pending[0];
        Pending.RemoveAt(0);
        if (!Discoveries.IsValidIndex(Index)) continue;
        Out = Discoveries[Index];
        ++AnnouncedCount;
        return true;
    }
    return false;
}

void UEWDiscoveryComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (GetOwner() && GetOwner()->HasAuthority()) CheckNow();
}
