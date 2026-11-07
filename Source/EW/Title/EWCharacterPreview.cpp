#include "Title/EWCharacterPreview.h"
#include "Animation/AnimSequence.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/ConstructorHelpers.h"

AEWCharacterPreview::AEWCharacterPreview()
{
    PrimaryActorTick.bCanEverTick = true;
    // After the idle has posed the hidden body this frame.
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Stand"));
    Body = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Body"));
    Body->SetupAttachment(RootComponent);
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // The mannequin meshes face +Y; turn them to face along the actor's forward.
    Body->SetRelativeRotation(FRotator(0, -90, 0));
    Body->SetVisibility(false);
    Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Shown = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("Shown"));
    Shown->SetupAttachment(RootComponent);
    Shown->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Shown->SetRelativeRotation(FRotator(0, -90, 0));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> IdleFinder(TEXT("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle"));
    Idle = IdleFinder.Object;
}

void AEWCharacterPreview::ShowAppearance(const FEWAppearance& Appearance, UEWBodyRoster* Roster)
{
    const FEWAppearance Look = Appearance.Clamped(Roster);
    const USkeletalMesh* Before = Body->GetSkeletalMeshAsset();
    if (!Look.ApplyTo(Body, Roster) || !Look.ApplyTo(Shown, Roster)) return;
    Look.BoneScales(Shown, Shape);
    // A new body starts its idle afresh.
    if (Idle && (Before != Body->GetSkeletalMeshAsset() || !Body->IsPlaying())) Body->PlayAnimation(Idle, true);
}

void AEWCharacterPreview::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!Shown->GetSkinnedAsset() || Shown->GetSkinnedAsset() != Body->GetSkeletalMeshAsset()) return;
    Shown->CopyPoseFromSkeletalComponent(Body);
    const FReferenceSkeleton& Skeleton = Shown->GetSkinnedAsset()->GetRefSkeleton();
    TArray<FTransform>& Pose = Shown->BoneSpaceTransforms;
    if (Shape.Num() != Pose.Num()) return;
    // Each bone takes its own shape; a bone below a reshaped one takes back its parent's so only what was asked for changes.
    for (int32 Index = 0; Index < Pose.Num(); ++Index)
    {
        const int32 Parent = Skeleton.GetParentIndex(Index);
        const FVector Ratio = Shape[Index] / (Parent == INDEX_NONE ? FVector::OneVector : Shape[Parent]);
        if (!Ratio.Equals(FVector::OneVector, 1.e-4f)) Pose[Index].SetScale3D(Pose[Index].GetScale3D() * Ratio);
    }
    Shown->MarkRefreshTransformDirty();
}

FVector AEWCharacterPreview::GetBoneShape(FName Bone) const
{
    const int32 Index = Shown->GetBoneIndex(Bone);
    return Shape.IsValidIndex(Index) ? Shape[Index] : FVector::OneVector;
}

void AEWCharacterPreview::Turn(float Degrees)
{
    AddActorWorldRotation(FRotator(0, Degrees, 0));
}
