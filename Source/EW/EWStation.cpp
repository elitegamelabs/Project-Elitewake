#include "EWStation.h"
#include "EWCharacter.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWStation::AEWStation()
{
    bReplicates = true; SetReplicateMovement(true);
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FixtureMesh")); SetRootComponent(Mesh);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Mesh->SetCollisionResponseToAllChannels(ECR_Ignore); Mesh->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Mesh->SetStaticMesh(Cube.Object);
    Mesh->SetRelativeScale3D(FVector(.3));
}
void AEWStation::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWStation, StationType); DOREPLIFETIME(AEWStation, Mode);
    DOREPLIFETIME(AEWStation, HoldDuration); DOREPLIFETIME(AEWStation, bAvailable);
    DOREPLIFETIME(AEWStation, bSingleUse); DOREPLIFETIME(AEWStation, Acknowledgements);
}
bool AEWStation::CanInteract_Implementation(AEWCharacter* Survivor) const
{
    return bAvailable && !bAcknowledging && !IsActorBeingDestroyed() && IsValid(Survivor)
        && Survivor->GetWorld() == GetWorld() && Survivor->GetController()
        && Survivor->GetController()->GetPawn() == Survivor
        && (!GetOwner() || GetOwner() == Survivor || GetOwner() == Survivor->GetController());
}
FText AEWStation::GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const
{
    return StationType == EEWStationType::Campfire ? NSLOCTEXT("Elitewake","TestCampfire","Inspect Campfire (test)")
        : NSLOCTEXT("Elitewake","TestSmithy","Inspect Smithy (test)");
}
bool AEWStation::Interact_Implementation(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !Survivor || !Survivor->HasAuthority() || !CanInteract_Implementation(Survivor)
        || FEWInteractionTargeting::FindTarget(Survivor) != this) return false;
    TGuardValue<bool> Guard(bAcknowledging,true);
    Acknowledgements = Acknowledgements == MAX_int32 ? 0 : Acknowledgements+1;
    if (bSingleUse) bAvailable = false;
    ForceNetUpdate(); return true;
}
