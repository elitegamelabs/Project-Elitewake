#include "Title/EWCharacterPreview.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/ConstructorHelpers.h"

AEWCharacterPreview::AEWCharacterPreview()
{
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Stand"));
    Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
    Body->SetupAttachment(RootComponent);
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // The mannequin meshes face +Y; turn them to face along the actor's forward.
    Body->SetRelativeRotation(FRotator(0, -90, 0));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> IdleFinder(TEXT("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle"));
    Idle = IdleFinder.Object;
}

void AEWCharacterPreview::ShowAppearance(const FEWAppearance& Appearance, UEWBodyRoster* Roster)
{
    const USkeletalMesh* Before = Body->GetSkeletalMeshAsset();
    if (!Appearance.Clamped(Roster).ApplyTo(Body, Roster)) return;
    // A new body starts its idle afresh.
    if (Idle && (Before != Body->GetSkeletalMeshAsset() || !Body->IsPlaying())) Body->PlayAnimation(Idle, true);
}

void AEWCharacterPreview::Turn(float Degrees)
{
    AddActorWorldRotation(FRotator(0, Degrees, 0));
}
