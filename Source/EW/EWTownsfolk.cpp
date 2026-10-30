#include "EWTownsfolk.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/GameStateBase.h"
#include "Materials/MaterialInterface.h"

AEWTownsfolk::AEWTownsfolk()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    bReplicates = true;
    SetNetUpdateFrequency(2.f);
    auto* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    // Solid to people and to aim (the interaction trace) only, like every Port figure: no ship ever catches on one.
    Capsule = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Capsule"));
    Capsule->SetupAttachment(Root);
    Capsule->InitCapsuleSize(36.f, 92.f);
    Capsule->SetRelativeLocation(FVector(0, 0, 92.f));
    Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Capsule->SetCollisionObjectType(ECC_WorldDynamic);
    Capsule->SetCollisionResponseToAllChannels(ECR_Ignore);
    Capsule->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    Capsule->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Figure = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Figure"));
    Figure->SetupAttachment(Root);
    // The mannequin faces +Y; turned so the person faces the actor's forward.
    Figure->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
    Figure->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Figure->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
}

void AEWTownsfolk::BeginPlay()
{
    Super::BeginPlay();
    if (FigureMesh)
    {
        Figure->SetSkeletalMesh(FigureMesh);
        if (FigureMaterial) for (int32 Slot = 0; Slot < Figure->GetNumMaterials(); ++Slot) Figure->SetMaterial(Slot, FigureMaterial);
        Capsule->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        PlayFigure(false);
    }
    // The stroll's timetable: at each point a pause, then the walk to the next.
    LegStart.Reset();
    LoopSeconds = 0.f;
    if (StrollPoints.Num() >= 2)
    {
        for (int32 Index = 0; Index < StrollPoints.Num(); ++Index)
        {
            LegStart.Add(LoopSeconds);
            LoopSeconds += StrollPause + FVector::Dist(StrollPoints[Index], StrollPoints[(Index + 1) % StrollPoints.Num()]) / StrollSpeed;
        }
        SetActorTickEnabled(true);
    }
}

bool AEWTownsfolk::StrollPose(double Time, FVector& OutWhere, float& OutYaw) const
{
    if (LegStart.IsEmpty() || LoopSeconds <= 0.f) return false;
    const float T = float(FMath::Fmod(Time, double(LoopSeconds)));
    int32 Leg = LegStart.Num() - 1;
    while (Leg > 0 && LegStart[Leg] > T) --Leg;
    const FVector From = StrollPoints[Leg], To = StrollPoints[(Leg + 1) % StrollPoints.Num()];
    const float Walked = T - LegStart[Leg] - StrollPause;
    OutYaw = (To - From).GetSafeNormal2D().Rotation().Yaw;
    if (Walked <= 0.f)
    {
        OutWhere = From;
        // Pausing, they still face where they came from until they set off.
        const FVector Back = StrollPoints[(Leg + StrollPoints.Num() - 1) % StrollPoints.Num()];
        OutYaw = (From - Back).GetSafeNormal2D().Rotation().Yaw;
        return false;
    }
    const float Length = FMath::Max(1.f, FVector::Dist(From, To));
    OutWhere = FMath::Lerp(From, To, FMath::Clamp(Walked * StrollSpeed / Length, 0.f, 1.f));
    return true;
}

void AEWTownsfolk::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const AGameStateBase* State = GetWorld() ? GetWorld()->GetGameState() : nullptr;
    const double Now = State ? State->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
    FVector Where; float Yaw = 0.f;
    const bool bNowWalking = StrollPose(Now, Where, Yaw);
    SetActorLocationAndRotation(Where, FRotator(0.f, FMath::FixedTurn(GetActorRotation().Yaw, Yaw, 240.f * DeltaSeconds), 0.f));
    if (bNowWalking != bWalking || !bFigureStarted) PlayFigure(bNowWalking);
}

void AEWTownsfolk::PlayFigure(bool bWalk)
{
    bWalking = bWalk;
    if (!FigureMesh) return;
    UAnimSequence* Anim = bWalk && WalkAnim ? WalkAnim.Get() : IdleAnim.Get();
    if (!Anim) return;
    bFigureStarted = true;
    Figure->PlayAnimation(Anim, true);
    // Each idle starts somewhere else in its loop, so a crowd does not breathe in step.
    if (!bWalk) Figure->SetPosition(FMath::FRandRange(0.f, Anim->GetPlayLength()), false);
}

bool AEWTownsfolk::IsInReach(const AEWCharacter* Character) const
{
    return IsValid(Character) && !Character->IsDead() && FVector::Dist(Character->GetActorLocation(), GetActorLocation()) <= TalkReach;
}

bool AEWTownsfolk::CanInteract_Implementation(AEWCharacter* Character) const
{
    return HasDialogue() && IsValid(Character) && !Character->IsDead();
}

FText AEWTownsfolk::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    if (RoleTitle.IsEmpty()) return FText::Format(NSLOCTEXT("Elitewake", "TownsfolkTalk", "Talk to {0}"), NpcName);
    return FText::Format(NSLOCTEXT("Elitewake", "TownsfolkTalkRole", "Talk to {0}, {1}"), NpcName, RoleTitle);
}

bool AEWTownsfolk::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !HasDialogue() || !IsInReach(Character)) return false;
    auto* Controller = Cast<AEWPlayerController>(Character->GetController());
    if (!Controller) return false;
    Controller->ClientOpenDialogue(this);
    return true;
}

FText AEWTownsfolk::GetDialogueGreeting(const AEWCharacter* Character) const
{
    if (!Greeting.IsEmpty()) return Greeting;
    return FText::Format(NSLOCTEXT("Elitewake", "TownsfolkGreeting", "{0} nods to you."), NpcName);
}

TArray<FEWDialogueOption> AEWTownsfolk::GetDialogueOptionsFor(const AEWCharacter* Character) const
{
    TArray<FEWDialogueOption> Options;
    GetDialogueOptions(Character, Options);
    if (!SmallTalk.IsEmpty())
        Options.Add({FName(TEXT("Chat")), NSLOCTEXT("Elitewake", "TownsfolkChat", "Ask for a word"), true});
    return Options;
}

FText AEWTownsfolk::ChooseDialogue(AEWCharacter* Character, FName Key)
{
    if (!HasAuthority()) return FText::GetEmpty();
    if (!IsInReach(Character)) return NSLOCTEXT("Elitewake", "TownsfolkFar", "You are too far away.");
    const FEWDialogueOption* Option = GetDialogueOptionsFor(Character).FindByPredicate([Key](const FEWDialogueOption& O) { return O.Key == Key; });
    if (!Option) return FText::GetEmpty();
    if (!Option->bEnabled) return NSLOCTEXT("Elitewake", "TownsfolkNotNow", "That is not open to you now.");
    if (Key == FName(TEXT("Chat")))
    {
        const FText Line = SmallTalk[NextSmallTalk % SmallTalk.Num()];
        ++NextSmallTalk;
        return Line;
    }
    return ActOnDialogue(Character, Key);
}
