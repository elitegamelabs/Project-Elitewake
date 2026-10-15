#include "EWWaterSource.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
#include "EWEquipmentComponent.h"
#include "EWItemDefinition.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"

AEWWaterSource::AEWWaterSource()
{
    bReplicates = true;
    SetReplicateMovement(true);
    InteractionSurface = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionSurface"));
    SetRootComponent(InteractionSurface);
    InteractionSurface->SetBoxExtent(FVector(50, 50, 10));
    InteractionSurface->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    InteractionSurface->SetCollisionResponseToAllChannels(ECR_Ignore);
    InteractionSurface->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    InteractionSurface->SetGenerateOverlapEvents(false);
}

void AEWWaterSource::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWWaterSource, WaterQuality);
    DOREPLIFETIME(AEWWaterSource, bAvailable);
}

bool AEWWaterSource::HoldsEmptyWaterskin(const AEWCharacter* Survivor)
{
    const UEWEquipmentComponent* Equipment = Survivor ? Survivor->GetEquipmentComponent() : nullptr;
    const UEWItemDefinition* Held = Equipment ? Equipment->GetEquippedItem(EEWEquipmentSlot::MainHand) : nullptr;
    return Held && !Held->FilledVersion.IsNull();
}

bool AEWWaterSource::CanInteract_Implementation(AEWCharacter* Survivor) const
{
    if (!bAvailable || WaterQuality != EEWWaterQuality::Fresh || bDrinking || IsActorBeingDestroyed()
        || !IsValid(Survivor) || Survivor->IsActorBeingDestroyed() || Survivor->GetWorld() != GetWorld()
        || !Survivor->GetController() || Survivor->GetController()->GetPawn() != Survivor
        || (GetOwner() && GetOwner() != Survivor && GetOwner() != Survivor->GetController())) return false;
    const UEWSurvivalComponent* Stats = Survivor->GetSurvivalComponent();
    if (!Stats || Stats->GetHealth() <= 0) return false;
    // An empty waterskin in hand is filled here, however thirsty its carrier is.
    if (HoldsEmptyWaterskin(Survivor)) return true;
    return FMath::IsFinite(Stats->GetHydration()) && Stats->GetHydration() < 100.f;
}

FText AEWWaterSource::GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const
{
    return HoldsEmptyWaterskin(Survivor) ? NSLOCTEXT("Elitewake", "FillWaterskin", "Fill the waterskin")
        : NSLOCTEXT("Elitewake", "DrinkFreshWater", "Drink fresh water");
}

bool AEWWaterSource::Interact_Implementation(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !Survivor || !Survivor->HasAuthority() || !CanInteract_Implementation(Survivor)
        || FEWInteractionTargeting::FindTarget(Survivor) != this) return false;
    TGuardValue<bool> Guard(bDrinking, true);
    if (HoldsEmptyWaterskin(Survivor)) return Survivor->FillHeldWaterskin();
    Survivor->GetSurvivalComponent()->SetHydration(100.f);
    Survivor->ForceNetUpdate();
    return true;
}
