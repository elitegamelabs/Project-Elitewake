#include "EWDeathBag.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWPlayerController.h"
#include "EWSurvivalComponent.h"
#include "World/EWWorldState.h"
#include "UObject/ConstructorHelpers.h"

AEWDeathBag::AEWDeathBag()
{
    bReplicates = true;
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = .5f;
    InitialLifeSpan = LifeSeconds;
    Sack = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Sack"));
    RootComponent = Sack;
    // A squashed sphere about 60 cm across, its centre at the origin, until PostInitializeComponents finds the modelled sack.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Ball(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (Ball.Succeeded()) Sack->SetStaticMesh(Ball.Object);
    Sack->SetWorldScale3D(FVector(.6f, .5f, .4f));
    Sack->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Sack->SetCollisionResponseToAllChannels(ECR_Ignore);
    Sack->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Contents = CreateDefaultSubobject<UEWInventoryComponent>(TEXT("Contents"));
}

void AEWDeathBag::PostInitializeComponents()
{
    Super::PostInitializeComponents();
    // The canvas sack (Scripts/Setup/build_plains_threat.py) when it has been built, its base at the actor's origin.
    if (UStaticMesh* Modelled = LoadObject<UStaticMesh>(nullptr, SackMesh, nullptr, LOAD_Quiet | LOAD_NoWarn))
    {
        Sack->SetStaticMesh(Modelled);
        Sack->SetWorldScale3D(FVector::OneVector);
        bModelled = true;
    }
}

void AEWDeathBag::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority()) return;
    if (Contents && Contents->GetUsedSlotCount() > 0) bEverFilled = true;
    else if (bEverFilled) Destroy();     // taken clean
}

bool AEWDeathBag::CanAccess(const AEWCharacter* Character) const
{
    return IsValid(Character) && Character->GetSurvivalComponent() && !Character->GetSurvivalComponent()->IsDead()
        && FVector::Dist(Character->GetActorLocation(), GetActorLocation()) <= Reach;
}

bool AEWDeathBag::CanInteract_Implementation(AEWCharacter* Character) const { return CanAccess(Character); }

FText AEWDeathBag::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    return NSLOCTEXT("Elitewake", "OpenDeathBag", "Recover your belongings");
}

bool AEWDeathBag::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanAccess(Character)) return false;
    auto* PC = Cast<AEWPlayerController>(Character->GetController());
    if (!PC) return false;
    PC->ClientOpenContainer(this);
    return true;
}

FEWSavedContainer AEWDeathBag::CaptureForSave() const
{
    FEWSavedContainer Saved;
    Saved.Transform = GetActorTransform();
    if (Contents) Saved.Contents = Contents->Entries;
    Saved.LifeLeft = GetLifeSpan();
    return Saved;
}

void AEWDeathBag::RestoreSaved(const FEWSavedContainer& Saved)
{
    if (!HasAuthority() || !Contents) return;
    Contents->SetMaxSlots(FMath::Max(1, Saved.Contents.Num()));
    Contents->Entries = Saved.Contents;
    Contents->HandleInventoryChanged();
    // The time it had left when the game was saved, not a fresh half hour.
    SetLifeSpan(FMath::Max(1.f, Saved.LifeLeft));
}

AEWDeathBag* AEWDeathBag::DropInventoryOf(AEWCharacter* Dead, const FVector& Where)
{
    UEWInventoryComponent* Carried = Dead && Dead->HasAuthority() ? Dead->GetInventoryComponent() : nullptr;
    UWorld* World = Dead ? Dead->GetWorld() : nullptr;
    if (!Carried || !World || Carried->GetUsedSlotCount() == 0) return nullptr;
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    // On the ground under the body (Phase 1 slice 4: it floated at the body's middle), or where it is if there is none below.
    FVector Spot = Where;
    FHitResult Ground;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWDeathBagGround), false, Dead);
    if (World->LineTraceSingleByChannel(Ground, Where, Where - FVector(0.f, 0.f, 400.f), ECC_Visibility, Query)) Spot = Ground.ImpactPoint;
    AEWDeathBag* Bag = World->SpawnActor<AEWDeathBag>(AEWDeathBag::StaticClass(), Spot, FRotator(0.f, FMath::FRandRange(0.f, 360.f), 0.f), Params);
    if (!Bag) return nullptr;
    if (!Bag->bModelled && Spot != Where) Bag->AddActorWorldOffset(FVector(0.f, 0.f, 20.f));   // the sphere stands on its middle
    Bag->Contents->SetMaxSlots(FMath::Max(1, Carried->GetUsedSlotCount()));
    // Whole stacks, first to last, each moving its full quantity; whatever the bag cannot take stays with the body.
    for (int32 Index = Carried->GetUsedSlotCount() - 1; Index >= 0; --Index)
    {
        const TArray<FEWInventoryEntry> Entries = Carried->GetInventoryEntries();
        if (Entries.IsValidIndex(Index)) Carried->TransferEntryTo(Bag->Contents, Index, Entries[Index].Quantity);
    }
    return Bag;
}
