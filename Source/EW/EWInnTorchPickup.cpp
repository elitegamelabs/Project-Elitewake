#include "EWInnTorchPickup.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWSurvivalComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerState.h"
#include "Net/UnrealNetwork.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

AEWInnTorchPickup::AEWInnTorchPickup()
{
    PrimaryActorTick.bCanEverTick = true;
}
void AEWInnTorchPickup::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    auto* PC = GetWorld()->GetFirstPlayerController();
    if (PC && PC->IsLocalController())
        Mesh->SetVisibility(!HasCollected(Cast<AEWCharacter>(PC->GetPawn())));
    // Visibility is local presentation; collision remains for other players' server traces.
}

void AEWInnTorchPickup::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWInnTorchPickup, CollectedPlayers);
}
bool AEWInnTorchPickup::HasCollected(const AEWCharacter* Character) const
{
    return Character && Character->GetPlayerState() && CollectedPlayers.Contains(Character->GetPlayerState());
}
bool AEWInnTorchPickup::CanInteract_Implementation(AEWCharacter* Character) const
{
    return Super::CanInteract_Implementation(Character) && Character->GetPlayerState()
        && !HasCollected(Character) && !bGrantInProgress;
}
int32 AEWInnTorchPickup::TryPickup(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character) || !Character->HasAuthority()
        || Character->GetSurvivalComponent()->GetHealth() <= 0.f || FindTarget(Character) != this) return 0;
    TGuardValue<bool> Guard(bGrantInProgress, true);
    if (Character->GetInventoryComponent()->AddItem(ItemDefinition, 1) != 1) return 0;
    CollectedPlayers.AddUnique(Character->GetPlayerState());
    ForceNetUpdate();
    // Leave the world item intact for other players. No global quantity depletion.
    return 1;
}
