#include "EWStation.h"
#include "EWCharacter.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWStation::AEWStation()
{
    bReplicates = true; SetReplicateMovement(true);
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FixtureMesh")); SetRootComponent(Mesh);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Mesh->SetCollisionResponseToAllChannels(ECR_Ignore); Mesh->SetCollisionResponseToChannel(ECC_Visibility,ECR_Block);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Mesh->SetStaticMesh(Cube.Object);
    Mesh->SetRelativeScale3D(FVector(.3));
    Blocker = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Blocker"));
    Blocker->SetupAttachment(Mesh);
    Blocker->SetUsingAbsoluteScale(true);
    Blocker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Blocker->SetCapsuleSize(1.f, 1.f);
}

void AEWStation::PlayHitShake(const FVector& Direction, float Degrees)
{
    if (ShakeSeconds <= 0.f) RestRotation = GetActorQuat();
    // It rocks about the level line across the blow, from its base.
    const FVector Flat = Direction.GetSafeNormal2D();
    ShakeAxis = Flat.IsNearlyZero() ? FVector::RightVector : FVector::CrossProduct(FVector::UpVector, Flat);
    ShakeDegrees = Degrees;
    ShakeSeconds = .6f;
    SetActorTickEnabled(true);
}

void AEWStation::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (ShakeSeconds <= 0.f) { SetActorTickEnabled(false); return; }
    ShakeSeconds = FMath::Max(0.f, ShakeSeconds - DeltaSeconds);
    const float T = .6f - ShakeSeconds;
    const float Angle = ShakeSeconds > 0.f ? ShakeDegrees * FMath::Exp(-T * 7.f) * FMath::Sin(T * 38.f) : 0.f;
    SetActorRotation(FQuat(ShakeAxis, FMath::DegreesToRadians(Angle)) * RestRotation);
}

void AEWStation::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (!Blocker) return;
    const bool bSolid = BlockerRadius > 0.f && BlockerHalfHeight > 0.f;
    Blocker->SetCapsuleSize(FMath::Max(BlockerRadius, 1.f), FMath::Max3(BlockerHalfHeight, BlockerRadius, 1.f));
    // Upright from the actor's origin whatever the mesh's own rotation and scale.
    Blocker->SetUsingAbsoluteRotation(true);
    Blocker->SetWorldRotation(FRotator::ZeroRotator);
    Blocker->SetWorldLocation(Transform.GetLocation() + FVector(0, 0, BlockerHalfHeight));
    Blocker->SetCollisionEnabled(bSolid ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    Blocker->SetCollisionResponseToAllChannels(ECR_Block);
    // Aiming and interaction trace the mesh, so the core never hides it.
    Blocker->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
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
