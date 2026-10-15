#include "Wildlife/EWAnimal.h"
#include "Wildlife/EWAnimalDefinition.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "EWSound.h"
#include "Sound/SoundBase.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "WaterBodyActor.h"

AEWAnimal::AEWAnimal()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicatingMovement(true);
    SetNetUpdateFrequency(10.f);
    Body = CreateDefaultSubobject<USphereComponent>(TEXT("Body"));
    RootComponent = Body;
    // Only aim finds it (to strike or harvest it); nothing walks into it.
    Body->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Body->SetCollisionObjectType(ECC_WorldDynamic);
    Body->SetCollisionResponseToAllChannels(ECR_Ignore);
    Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Body->InitSphereRadius(25.f);
    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Body);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AEWAnimal::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWAnimal, Definition);
    DOREPLIFETIME(AEWAnimal, Health);
    DOREPLIFETIME(AEWAnimal, bDead);
    DOREPLIFETIME(AEWAnimal, bHarvested);
}

void AEWAnimal::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyDefinition();
}

void AEWAnimal::ApplyDefinition()
{
    if (!Definition) return;
    Visual->SetStaticMesh(Definition->Mesh.LoadSynchronous());
    // The actor stands on its feet; the aiming sphere sits on the body, big enough to hit anywhere along it.
    const float Radius = FMath::Max3(float(Definition->Size.Y * .5f), float(Definition->Size.X * .3f), 15.f);
    Body->SetSphereRadius(Radius);
    Visual->SetRelativeLocation(FVector(0, 0, -Radius));
}

void AEWAnimal::BeginPlay()
{
    Super::BeginPlay();
    ApplyDefinition();
    Home = RoamPoint = GetActorLocation();
    LastShown = GetActorLocation();
    if (HasAuthority() && Definition) Health = Definition->MaxHealth;
    RestSeconds = FMath::FRandRange(0.f, 4.f);
    if (Definition) CallSeconds = FMath::FRandRange(0.f, Definition->CallInterval.Y);
    OnRep_State();
}

void AEWAnimal::OnRep_State()
{
    Visual->SetVisibility(!bHarvested);
    Body->SetCollisionEnabled(bHarvested ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryOnly);
    Visual->SetCustomPrimitiveDataFloat(2, bDead ? 1.f : 0.f);
    // Dead, it lies on its side.
    Visual->SetRelativeRotation(FRotator(0, 0, bDead ? 80.f : 0.f));
}

void AEWAnimal::PostNetReceiveLocationAndRotation()
{
    const FTransform Shown = GetActorTransform();
    Super::PostNetReceiveLocationAndRotation();
    NetPose = GetActorTransform();
    if (!bHasNetPose || FVector::Dist(Shown.GetLocation(), NetPose.GetLocation()) > 600.f)
    {
        bHasNetPose = true;
        return;
    }
    SetActorTransform(Shown);
}

void AEWAnimal::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (HasAuthority()) Think(DeltaSeconds);
    else if (bHasNetPose)
    {
        FTransform Shown;
        Shown.Blend(GetActorTransform(), NetPose, 1.f - FMath::Exp(-8.f * DeltaSeconds));
        SetActorTransform(Shown);
    }
    Animate(DeltaSeconds);
}

void AEWAnimal::Animate(float DeltaSeconds)
{
    if (!Definition || DeltaSeconds <= 0.f) return;
    const FVector Here = GetActorLocation();
    const float Moved = FVector::Dist2D(Here, LastShown) / DeltaSeconds;
    LastShown = Here;
    ShownSpeed = bDead ? 0.f : FMath::FInterpTo(ShownSpeed, FMath::Min(Moved, Definition->RunSpeed * 1.5f), DeltaSeconds, 6.f);
    // The stride advances with the ground covered, so feet do not slide.
    StridePhase = FMath::Fmod(StridePhase + ShownSpeed / FMath::Max(Definition->StrideLength, 1.f) * 2.f * PI * DeltaSeconds, 2.f * PI);
    Visual->SetCustomPrimitiveDataFloat(0, StridePhase);
    Visual->SetCustomPrimitiveDataFloat(1, FMath::Clamp(ShownSpeed / FMath::Max(Definition->WalkSpeed * .6f, 1.f), 0.f, 1.f));
    // A struck animal shudders.
    FlinchSeconds = FMath::Max(0.f, FlinchSeconds - DeltaSeconds);
    if (!bDead) Visual->SetRelativeRotation(FRotator(0, FlinchSeconds > 0.f ? FMath::Sin(FlinchSeconds * 60.f) * 10.f : 0.f, 0));
}

bool AEWAnimal::IsAshore(const AEWCharacter* Survivor) const
{
    return IsValid(Survivor) && Survivor->GetCharacterMovement() && !Survivor->GetCharacterMovement()->IsSwimming()
        && Survivor->GetSurvivalComponent() && Survivor->GetSurvivalComponent()->GetHealth() > 0.f;
}

bool AEWAnimal::GroundAt(const FVector& At, float& OutZ) const
{
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWAnimalGround), false, this);
    for (TActorIterator<AWaterBody> It(GetWorld()); It; ++It) Query.AddIgnoredActor(*It);
    FHitResult Hit;
    const FVector From(At.X, At.Y, At.Z + 250.f);
    if (!GetWorld()->LineTraceSingleByObjectType(Hit, From, From - FVector(0, 0, 1500.f), FCollisionObjectQueryParams(ECC_WorldStatic), Query))
        return false;
    OutZ = Hit.ImpactPoint.Z;
    return OutZ > SurfaceZ - Definition->WadeDepth;
}

FVector AEWAnimal::PickRoamPoint() const
{
    for (int32 Try = 0; Try < 10; ++Try)
    {
        const FVector2D Offset = FMath::RandPointInCircle(Definition->RoamRadius);
        FVector Point(Home.X + Offset.X, Home.Y + Offset.Y, Home.Z);
        float Z;
        if (GroundAt(Point, Z)) { Point.Z = Z; return Point; }
    }
    return Home;
}

bool AEWAnimal::WalkToward(const FVector& Target, float Speed, float DeltaSeconds)
{
    const float Radius = Body->GetUnscaledSphereRadius();
    const FVector Feet = GetActorLocation() - FVector(0, 0, Radius);
    const FRotator Want = (Target - Feet).Rotation();
    FRotator Facing = GetActorRotation();
    Facing.Yaw = FMath::FixedTurn(Facing.Yaw, Want.Yaw, Definition->TurnRate * DeltaSeconds);
    Facing.Pitch = Facing.Roll = 0.f;
    // Slow while turning hard, so it turns on the spot rather than circling.
    const float Ahead = FVector::DotProduct(Facing.Vector(), (Target - Feet).GetSafeNormal2D());
    const FVector Step = Facing.Vector() * Speed * FMath::Clamp(Ahead, .15f, 1.f) * DeltaSeconds;
    float Z;
    if (!GroundAt(Feet + Step, Z) || FMath::Abs(Z - Feet.Z) > FMath::Max(60.f, Step.Size() * 3.f))
    {
        SetActorRotation(Facing);
        return false;
    }
    SetActorLocationAndRotation(FVector(Feet.X + Step.X, Feet.Y + Step.Y, Z + Radius), Facing);
    return true;
}

void AEWAnimal::Think(float DeltaSeconds)
{
    if (!Definition) return;
    if (bDead)
    {
        DeadSeconds += DeltaSeconds;
        if (DeadSeconds >= Definition->RespawnSeconds) Respawn();
        return;
    }
    AttackCooldown -= DeltaSeconds;
    FleeSeconds -= DeltaSeconds;
    if (Definition->CallInterval.Y > 0.f && (CallSeconds -= DeltaSeconds) <= 0.f)
    {
        CallSeconds = FMath::FRandRange(Definition->CallInterval.X, Definition->CallInterval.Y);
        Call();
    }
    if (Definition->bAggressive)
    {
        AEWCharacter* Target = Quarry.Get();
        if (Target && (!IsAshore(Target) || FVector::Dist(Target->GetActorLocation(), GetActorLocation()) > Definition->NoticeRange * 1.6f))
            Target = nullptr;
        if (!Target)
        {
            float Best = Definition->NoticeRange;
            for (TActorIterator<AEWCharacter> It(GetWorld()); It; ++It)
            {
                const float Distance = FVector::Dist(It->GetActorLocation(), GetActorLocation());
                if (Distance < Best && IsAshore(*It)) { Best = Distance; Target = *It; }
            }
        }
        // Going for someone, it warns them first.
        if (Target && !Quarry.IsValid()) Call();
        Quarry = Target;
        if (Target)
        {
            const FVector Nose = GetActorLocation() + GetActorForwardVector() * Definition->Size.X * .5f;
            if (FVector::Dist2D(Nose, Target->GetActorLocation()) > Definition->AttackReach * .6f)
                WalkToward(Target->GetActorLocation(), Definition->RunSpeed, DeltaSeconds);
            if (AttackCooldown <= 0.f && FVector::Dist(Nose, Target->GetActorLocation()) < Definition->AttackReach + 70.f)
            {
                AttackCooldown = Definition->AttackInterval;
                Target->GetSurvivalComponent()->ApplyDamage(Definition->AttackDamage);
                Target->ReactToHit();
            }
            return;
        }
    }
    if (FleeSeconds > 0.f && FleeFrom.IsValid())
    {
        const FVector Away = (GetActorLocation() - FleeFrom->GetActorLocation()).GetSafeNormal2D();
        if (!WalkToward(GetActorLocation() + Away * 800.f, Definition->RunSpeed, DeltaSeconds))
            WalkToward(GetActorLocation() + FVector(-Away.Y, Away.X, 0.f) * 800.f, Definition->RunSpeed, DeltaSeconds);
        return;
    }
    // Wander: walk to a spot, stand a while, walk on.
    if (RestSeconds > 0.f) { RestSeconds -= DeltaSeconds; return; }
    RoamSeconds -= DeltaSeconds;
    const bool bArrived = FVector::Dist2D(RoamPoint, GetActorLocation()) < FMath::Max(60.f, Definition->Size.X * .4f);
    if (bArrived || RoamSeconds <= 0.f || !WalkToward(RoamPoint, Definition->WalkSpeed, DeltaSeconds))
    {
        RoamPoint = PickRoamPoint();
        RoamSeconds = 20.f;
        if (bArrived) RestSeconds = FMath::FRandRange(2.f, 8.f);
    }
}

AEWAnimal* AEWAnimal::FindStruck(const AEWCharacter* Striker, float Reach)
{
    if (!IsValid(Striker) || !Striker->GetWorld()) return nullptr;
    FVector Eye; FRotator View;
    Striker->GetActorEyesViewPoint(Eye, View);
    const FVector From = Striker->GetActorLocation() + FVector(0, 0, Striker->BaseEyeHeight * .5f);
    const FVector To = From + View.Vector() * Reach;
    AEWAnimal* Best = nullptr;
    float BestAlong = TNumericLimits<float>::Max();
    for (TActorIterator<AEWAnimal> It(Striker->GetWorld()); It; ++It)
    {
        AEWAnimal* Animal = *It;
        if (Animal->bDead || !Animal->Definition) continue;
        const FVector Spine = Animal->GetActorForwardVector() * Animal->Definition->Size.X * .5f;
        FVector OnSwing, OnSpine;
        FMath::SegmentDistToSegmentSafe(From, To, Animal->GetActorLocation() - Spine, Animal->GetActorLocation() + Spine, OnSwing, OnSpine);
        const float Along = FVector::Dist(From, OnSwing);
        // Low animals are struck at a downward swing's end too: the body's height counts toward reach.
        if (FVector::Dist(OnSwing, OnSpine) < Animal->Definition->Size.Y * .5f + 45.f && Along < BestAlong)
        {
            Best = Animal;
            BestAlong = Along;
        }
    }
    return Best;
}

bool AEWAnimal::TakeStrike(AEWCharacter* Striker, float Damage)
{
    if (!HasAuthority() || bDead || !Definition || Damage <= 0.f) return false;
    Health = FMath::Max(0.f, Health - Damage);
    MulticastFlinch();
    Call();
    if (Health <= 0.f) Die();
    else if (Definition->bAggressive) Quarry = Striker;
    else
    {
        FleeFrom = Striker;
        FleeSeconds = 6.f;
        RestSeconds = 0.f;
    }
    return true;
}

void AEWAnimal::MulticastFlinch_Implementation()
{
    FlinchSeconds = .35f;
}

void AEWAnimal::Call()
{
    const double Now = GetWorld()->GetTimeSeconds();
    if (!HasAuthority() || !Definition || Definition->Calls.IsEmpty() || Now - LastCallTime < 3.0) return;
    LastCallTime = Now;
    MulticastCall();
}

void AEWAnimal::MulticastCall_Implementation()
{
    if (!Definition || Definition->Calls.IsEmpty()) return;
    USoundBase* Sound = Definition->Calls[FMath::RandRange(0, Definition->Calls.Num() - 1)].LoadSynchronous();
    UEWSoundLibrary::PlayAssetAt(this, Sound, GetActorLocation() + FVector(0, 0, Definition->Size.Y * .5f), 1.f, FMath::FRandRange(.95f, 1.05f));
}

void AEWAnimal::Die()
{
    bDead = true;
    Health = 0.f;
    YieldLeft = FMath::RandRange(Definition->YieldMin, FMath::Max(Definition->YieldMin, Definition->YieldMax));
    Quarry = nullptr;
    DeadSeconds = 0.f;
    OnRep_State();
    ForceNetUpdate();
}

void AEWAnimal::Respawn()
{
    bDead = bHarvested = false;
    Health = Definition->MaxHealth;
    YieldLeft = 0;
    FleeSeconds = 0.f;
    RoamPoint = Home;
    SetActorLocationAndRotation(Home, FRotator(0, FMath::FRandRange(-180.f, 180.f), 0));
    OnRep_State();
    ForceNetUpdate();
}

bool AEWAnimal::CanInteract_Implementation(AEWCharacter* Character) const
{
    return IsValid(Character) && bDead && !bHarvested && Definition && Definition->Yield
        && FVector::Dist(Character->GetActorLocation(), GetActorLocation()) < HarvestReach + Definition->Size.X * .5f;
}

FText AEWAnimal::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    return Definition ? FText::Format(NSLOCTEXT("Elitewake", "HarvestAnimal", "Harvest the {0}"), Definition->DisplayName) : FText::GetEmpty();
}

bool AEWAnimal::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character) || !Character->GetInventoryComponent()) return false;
    // Nothing is lost: whatever does not fit stays on the body for later.
    const int32 Taken = Character->GetInventoryComponent()->AddItem(Definition->Yield, YieldLeft);
    if (Taken <= 0) return false;
    YieldLeft -= Taken;
    if (YieldLeft > 0) return true;
    bHarvested = true;
    OnRep_State();
    ForceNetUpdate();
    return true;
}
