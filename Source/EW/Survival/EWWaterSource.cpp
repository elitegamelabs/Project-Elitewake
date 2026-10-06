#include "EWWaterSource.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
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

bool AEWWaterSource::CanInteract_Implementation(AEWCharacter* Survivor) const
{
    if (!bAvailable || WaterQuality != EEWWaterQuality::Fresh || bDrinking || IsActorBeingDestroyed()
        || !IsValid(Survivor) || Survivor->IsActorBeingDestroyed() || Survivor->GetWorld() != GetWorld()
        || !Survivor->GetController() || Survivor->GetController()->GetPawn() != Survivor
        || (GetOwner() && GetOwner() != Survivor && GetOwner() != Survivor->GetController())) return false;
    const UEWSurvivalComponent* Stats = Survivor->GetSurvivalComponent();
    return Stats && Stats->GetHealth() > 0 && FMath::IsFinite(Stats->GetHydration()) && Stats->GetHydration() < 100.f;
}

FText AEWWaterSource::GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const
{
    return NSLOCTEXT("Elitewake", "DrinkFreshWater", "Drink fresh water");
}

bool AEWWaterSource::Interact_Implementation(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !Survivor || !Survivor->HasAuthority() || !CanInteract_Implementation(Survivor)
        || FEWInteractionTargeting::FindTarget(Survivor) != this) return false;
    TGuardValue<bool> Guard(bDrinking, true);
    Survivor->GetSurvivalComponent()->SetHydration(100.f);
    Survivor->ForceNetUpdate();
    return true;
}
