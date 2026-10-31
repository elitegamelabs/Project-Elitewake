#include "EWShipSurgeon.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
#include "EWWalletComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWShipSurgeon::AEWShipSurgeon()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicatingMovement(false);                  // she is attached to her ship; the attachment replicates
    SetNetUpdateFrequency(10.f);
    auto* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
    Body->SetupAttachment(Root);
    if (Cylinder.Succeeded()) Body->SetStaticMesh(Cylinder.Object);
    Body->SetRelativeLocation(FVector(0, 0, 55));
    Body->SetRelativeScale3D(FVector(.45f, .45f, 1.1f));
    // Solid to people and to aim only, so the hull she rides in never catches on her.
    Body->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Body->SetCollisionObjectType(ECC_WorldDynamic);
    Body->SetCollisionResponseToAllChannels(ECR_Ignore);
    Body->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Head = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Head"));
    Head->SetupAttachment(Body);
    if (Sphere.Succeeded()) Head->SetStaticMesh(Sphere.Object);
    Head->SetRelativeLocation(FVector(0, 0, 62));
    Head->SetRelativeScale3D(FVector(.7f, .7f, .35f));
    Head->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AEWShipSurgeon::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWShipSurgeon, bTreating);
    DOREPLIFETIME(AEWShipSurgeon, TreatmentsGiven);
}

bool AEWShipSurgeon::IsTreatingCharacter(const AEWCharacter* Character) const
{
    return Patients.ContainsByPredicate([Character](const FPatient& P) { return P.Who.Get() == Character; });
}

bool AEWShipSurgeon::CanInteract_Implementation(AEWCharacter* Character) const
{
    return IsValid(Character) && !Character->IsDead();
}

FText AEWShipSurgeon::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    if (!IsValid(Character)) return FText::GetEmpty();
    const UEWSurvivalComponent* Needs = Character->GetSurvivalComponent();
    const UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (IsTreatingCharacter(Character)) return NSLOCTEXT("Elitewake", "SurgeonBusy", "The surgeon is treating you");
    if (Needs && Needs->GetHealth() >= Needs->GetMaxHealth() - .01f) return NSLOCTEXT("Elitewake", "SurgeonWell", "Surgeon: you are in good health");
    if (Purse && !Purse->CanAfford(TreatmentCost))
        return FText::Format(NSLOCTEXT("Elitewake", "SurgeonPoor", "Surgeon: a treatment costs {0} Copper"), FText::AsNumber(TreatmentCost));
    return FText::Format(NSLOCTEXT("Elitewake", "SurgeonOffer", "Treat wounds ({0} Copper)"), FText::AsNumber(TreatmentCost));
}

bool AEWShipSurgeon::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character) || IsTreatingCharacter(Character)) return false;
    UEWSurvivalComponent* Needs = Character->GetSurvivalComponent();
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Needs || !Purse || Needs->GetHealth() >= Needs->GetMaxHealth() - .01f) return false;
    if (FVector::Dist(Character->GetActorLocation(), GetActorLocation()) > TreatmentReach) return false;
    if (!Purse->TrySpend(TreatmentCost)) return false;
    FPatient Patient;
    Patient.Who = Character;
    Patient.Left = Needs->GetMaxHealth() * TreatmentHealFraction;
    Patient.RatePerSecond = Patient.Left / TreatmentSeconds;
    Patients.Add(Patient);
    ++TreatmentsGiven;
    bTreating = true;
    ForceNetUpdate();
    return true;
}

void AEWShipSurgeon::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (HasAuthority())
    {
        for (int32 i = Patients.Num() - 1; i >= 0; --i)
        {
            AEWCharacter* Who = Patients[i].Who.Get();
            UEWSurvivalComponent* Needs = Who ? Who->GetSurvivalComponent() : nullptr;
            if (!Needs || Who->IsDead() || FVector::Dist(Who->GetActorLocation(), GetActorLocation()) > TreatmentReach * 2.f)
            {
                Patients.RemoveAtSwap(i);
                continue;
            }
            const float Step = FMath::Min(Patients[i].Left, Patients[i].RatePerSecond * DeltaSeconds);
            Needs->RestoreHealth(Step);                 // the survival component caps this at the maximum
            Patients[i].Left -= Step;
            if (Patients[i].Left <= KINDA_SMALL_NUMBER) Patients.RemoveAtSwap(i);
        }
        const bool bBusy = !Patients.IsEmpty();
        if (bBusy != bTreating) { bTreating = bBusy; ForceNetUpdate(); }
    }
    // Presentation on every machine: she leans in while treating and rocks gently as she works.
    LeanAlpha = FMath::FInterpTo(LeanAlpha, bTreating ? 1.f : 0.f, DeltaSeconds, 4.f);
    const float Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
    Body->SetRelativeRotation(FRotator(LeanAlpha * 18.f + FMath::Sin(Time * 5.f) * LeanAlpha * 4.f, 0.f, 0.f));
}
