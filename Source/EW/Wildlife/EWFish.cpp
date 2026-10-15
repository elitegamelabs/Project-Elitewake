#include "Wildlife/EWFish.h"
#include "Wildlife/EWFishDefinition.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "WaterBodyActor.h"

AEWFish::AEWFish()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicatingMovement(true);
    SetNetUpdateFrequency(10.f);
    Body = CreateDefaultSubobject<USphereComponent>(TEXT("Body"));
    RootComponent = Body;
    // Only aim finds it (to harvest the body); nothing walks or swims into it.
    Body->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Body->SetCollisionObjectType(ECC_WorldDynamic);
    Body->SetCollisionResponseToAllChannels(ECR_Ignore);
    Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Body->InitSphereRadius(20.f);
    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Body);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetCastShadow(false);
}

void AEWFish::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWFish, Definition);
    DOREPLIFETIME(AEWFish, Health);
    DOREPLIFETIME(AEWFish, bDead);
    DOREPLIFETIME(AEWFish, bHarvested);
    DOREPLIFETIME(AEWFish, Carrier);
    DOREPLIFETIME(AEWFish, bOnLand);
}

void AEWFish::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyDefinition();
}

void AEWFish::ApplyDefinition()
{
    if (!Definition) return;
    Visual->SetStaticMesh(Definition->Mesh.LoadSynchronous());
    // Big enough to aim at anywhere on the body, a long creature's included.
    Body->SetSphereRadius(FMath::Max3(float(Definition->Size.Y * .5), float(Definition->Size.X * .3), 15.f));
}

void AEWFish::BeginPlay()
{
    Super::BeginPlay();
    ApplyDefinition();
    Home = RoamPoint = GetActorLocation();
    if (HasAuthority() && Definition)
    {
        Health = Definition->MaxHealth;
    }
    OnRep_State();
}

void AEWFish::OnRep_State()
{
    Visual->SetVisibility(!bHarvested);
    // A carried body is not in anyone's way, its carrier's included.
    Body->SetCollisionEnabled(bHarvested || Carrier ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryOnly);
}

void AEWFish::PostNetReceiveLocationAndRotation()
{
    const FTransform Shown = GetActorTransform();
    Super::PostNetReceiveLocationAndRotation();
    NetPose = GetActorTransform();
    // The first update, or a respawn far away, is taken at once; otherwise glide to it.
    if (!bHasNetPose || FVector::Dist(Shown.GetLocation(), NetPose.GetLocation()) > 600.f)
    {
        bHasNetPose = true;
        return;
    }
    SetActorTransform(Shown);
}

void AEWFish::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (IsValid(Carrier))
    {
        // Every screen keeps a carried body with its carrier, smoothly.
        SetActorTransform(CarryPose());
        if (HasAuthority()) Think(DeltaSeconds);
    }
    else if (HasAuthority()) Think(DeltaSeconds);
    else if (bHasNetPose)
    {
        FTransform Shown;
        Shown.Blend(GetActorTransform(), NetPose, 1.f - FMath::Exp(-8.f * DeltaSeconds));
        SetActorTransform(Shown);
    }
    // A struck creature shudders.
    FlinchSeconds = FMath::Max(0.f, FlinchSeconds - DeltaSeconds);
    Visual->SetRelativeRotation(FRotator(0, FlinchSeconds > 0.f ? FMath::Sin(FlinchSeconds * 60.f) * 12.f : 0.f, 0));
}

bool AEWFish::IsInWater(const AEWCharacter* Survivor) const
{
    return IsValid(Survivor) && Survivor->GetCharacterMovement() && Survivor->GetCharacterMovement()->IsSwimming()
        && Survivor->GetSurvivalComponent() && Survivor->GetSurvivalComponent()->GetHealth() > 0.f;
}

float AEWFish::FloorBelow(const FVector& At) const
{
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWFishFloor), false, this);
    for (TActorIterator<AWaterBody> It(GetWorld()); It; ++It) Query.AddIgnoredActor(*It);
    FHitResult Hit;
    const FVector From(At.X, At.Y, SurfaceZ + 50.f);
    return GetWorld()->LineTraceSingleByChannel(Hit, From, From - FVector(0, 0, 6000.f), ECC_WorldStatic, Query)
        ? Hit.ImpactPoint.Z : SurfaceZ - 6000.f;
}

FVector AEWFish::PickRoamPoint() const
{
    const float Half = Definition->Size.Y * .5f;
    for (int32 Try = 0; Try < 10; ++Try)
    {
        const FVector2D Offset = FMath::RandPointInCircle(Definition->RoamRadius);
        FVector Point(Home.X + Offset.X, Home.Y + Offset.Y, 0.f);
        const float Floor = FMath::Max(FloorBelow(Point) + Half + 30.f, SurfaceZ - Definition->MaxDepth);
        const float Ceiling = SurfaceZ - FMath::Max(Definition->MinDepth, Half + 20.f);
        if (Floor >= Ceiling) continue;   // too shallow, or land
        Point.Z = FMath::FRandRange(Floor, Ceiling);
        return Point;
    }
    return Home;
}

void AEWFish::SwimToward(const FVector& Target, float Speed, float DeltaSeconds)
{
    const FVector Here = GetActorLocation();
    const FRotator Want = (Target - Here).Rotation();
    FRotator Facing = GetActorRotation();
    Facing.Yaw = FMath::FixedTurn(Facing.Yaw, Want.Yaw, Definition->TurnRate * DeltaSeconds);
    Facing.Pitch = FMath::FixedTurn(Facing.Pitch, FMath::Clamp(Want.Pitch, -25.f, 25.f), Definition->TurnRate * .5f * DeltaSeconds);
    Facing.Roll = 0.f;
    // Slow while turning hard, so a fast swimmer closes on its target instead of circling it.
    const float Ahead = FVector::DotProduct(Facing.Vector(), (Target - Here).GetSafeNormal());
    FVector Next = Here + Facing.Vector() * Speed * FMath::Clamp(Ahead, .25f, 1.f) * DeltaSeconds;
    // Stay in the water: under the surface and over the bottom. Shallows it cannot fit in turn it back.
    const float Half = Definition->Size.Y * .5f;
    const float Ceiling = SurfaceZ - Half - 10.f;
    const float Floor = FloorBelow(Next) + Half + 10.f;
    if (Floor > Ceiling)
    {
        RoamPoint = PickRoamPoint();
        RoamSeconds = 12.f;
        SetActorRotation(Facing);
        return;
    }
    Next.Z = FMath::Clamp(Next.Z, Floor, Ceiling);
    SetActorLocationAndRotation(Next, Facing);
}

void AEWFish::Think(float DeltaSeconds)
{
    if (!Definition) return;
    if (bDead)
    {
        if (Carrier)
        {
            // Let go if the carrier can no longer carry it.
            const auto* Survival = IsValid(Carrier) ? Carrier->GetSurvivalComponent() : nullptr;
            if (!Survival || Survival->GetHealth() <= 0.f || Carrier->GetCarriedFish() != this || Carrier->GetHelmShip() || Carrier->IsOnLadder())
                SetDown();
            return;   // the body keeps while it is carried
        }
        DeadSeconds += DeltaSeconds;
        if (DeadSeconds >= Definition->RespawnSeconds) { Respawn(); return; }
        if (bOnLand) return;   // lying where it was set down
        // Belly-up, drifting to the surface, until it returns home.
        FVector Here = GetActorLocation();
        Here.Z = FMath::FInterpConstantTo(Here.Z, SurfaceZ - Definition->Size.Y * .25f, DeltaSeconds, 60.f);
        FRotator Facing = GetActorRotation();
        Facing.Pitch = 0.f;
        Facing.Roll = FMath::FInterpConstantTo(Facing.Roll, 180.f, DeltaSeconds, 120.f);
        SetActorLocationAndRotation(Here, Facing);
        return;
    }
    AttackCooldown -= DeltaSeconds;
    FleeSeconds -= DeltaSeconds;
    if (Definition->bAggressive)
    {
        AEWCharacter* Target = Quarry.Get();
        if (Target && (!IsInWater(Target) || FVector::Dist(Target->GetActorLocation(), GetActorLocation()) > Definition->NoticeRange * 1.5f))
            Target = nullptr;
        if (!Target)
        {
            float Best = Definition->NoticeRange;
            for (TActorIterator<AEWCharacter> It(GetWorld()); It; ++It)
            {
                const float Distance = FVector::Dist(It->GetActorLocation(), GetActorLocation());
                if (Distance < Best && IsInWater(*It)) { Best = Distance; Target = *It; }
            }
        }
        Quarry = Target;
        if (Target)
        {
            SwimToward(Target->GetActorLocation(), Definition->DashSpeed, DeltaSeconds);
            const FVector Nose = GetActorLocation() + GetActorForwardVector() * Definition->Size.X * .5f;
            if (AttackCooldown <= 0.f && FVector::Dist(Nose, Target->GetActorLocation()) < Definition->AttackReach + 45.f)
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
        SwimToward(GetActorLocation() + Away * 600.f, Definition->DashSpeed, DeltaSeconds);
        return;
    }
    RoamSeconds -= DeltaSeconds;
    if (RoamSeconds <= 0.f || FVector::Dist(RoamPoint, GetActorLocation()) < FMath::Max(100.f, Definition->Size.X * .5f))
    {
        RoamPoint = PickRoamPoint();
        RoamSeconds = 12.f;
    }
    SwimToward(RoamPoint, Definition->SwimSpeed, DeltaSeconds);
}

AEWFish* AEWFish::FindStruck(const AEWCharacter* Striker, float Reach)
{
    if (!IsValid(Striker) || !Striker->GetWorld()) return nullptr;
    FVector Eye; FRotator View;
    Striker->GetActorEyesViewPoint(Eye, View);
    const FVector From = Striker->GetActorLocation() + FVector(0, 0, Striker->BaseEyeHeight * .5f);
    const FVector To = From + View.Vector() * Reach;
    AEWFish* Best = nullptr;
    float BestAlong = TNumericLimits<float>::Max();
    for (TActorIterator<AEWFish> It(Striker->GetWorld()); It; ++It)
    {
        AEWFish* Fish = *It;
        if (Fish->bDead || !Fish->Definition) continue;
        // The swing's line against the creature's spine, nose to tail.
        const FVector Spine = Fish->GetActorForwardVector() * Fish->Definition->Size.X * .5f;
        FVector OnSwing, OnSpine;
        FMath::SegmentDistToSegmentSafe(From, To, Fish->GetActorLocation() - Spine, Fish->GetActorLocation() + Spine, OnSwing, OnSpine);
        const float Along = FVector::Dist(From, OnSwing);
        if (FVector::Dist(OnSwing, OnSpine) < Fish->Definition->Size.Y * .5f + 30.f && Along < BestAlong)
        {
            Best = Fish;
            BestAlong = Along;
        }
    }
    return Best;
}

bool AEWFish::TakeStrike(AEWCharacter* Striker, float Damage)
{
    if (!HasAuthority() || bDead || !Definition || Damage <= 0.f) return false;
    Health = FMath::Max(0.f, Health - Damage);
    MulticastFlinch();
    if (Health <= 0.f) Die();
    else if (Definition->bAggressive) Quarry = Striker;
    else
    {
        FleeFrom = Striker;
        FleeSeconds = 5.f;
    }
    return true;
}

void AEWFish::MulticastFlinch_Implementation()
{
    FlinchSeconds = .35f;
}

void AEWFish::Die()
{
    bDead = true;
    Health = 0.f;
    YieldLeft = FMath::RandRange(Definition->YieldMin, FMath::Max(Definition->YieldMin, Definition->YieldMax));
    Quarry = nullptr;
    DeadSeconds = 0.f;
    OnRep_State();
    ForceNetUpdate();
}

void AEWFish::Respawn()
{
    if (Carrier) Carrier->SetCarriedFish(nullptr);
    Carrier = nullptr;
    bDead = bHarvested = bOnLand = false;
    Health = Definition->MaxHealth;
    YieldLeft = 0;
    FleeSeconds = 0.f;
    RoamPoint = Home;
    SetActorLocationAndRotation(Home, FRotator(0, FMath::FRandRange(-180.f, 180.f), 0));
    OnRep_State();
    ForceNetUpdate();
}

bool AEWFish::CanInteract_Implementation(AEWCharacter* Character) const
{
    if (!IsValid(Character) || !bDead || bHarvested || !Definition || !Definition->Yield) return false;
    if (Carrier) return Carrier == Character;   // set it down
    const bool bNear = FVector::Dist(Character->GetActorLocation(), GetActorLocation()) < HarvestReach + Definition->Size.X * .5f;
    // On land it is harvested; in the water it is picked up, by someone with nothing else in their arms.
    return bNear && (bOnLand || (!Character->GetCarriedFish() && !Character->GetHelmShip() && !Character->IsOnLadder()));
}

FText AEWFish::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    if (!Definition) return FText::GetEmpty();
    if (Carrier) return FText::Format(NSLOCTEXT("Elitewake", "SetDownFish", "Set down the {0}"), Definition->DisplayName);
    return bOnLand ? FText::Format(NSLOCTEXT("Elitewake", "HarvestFish", "Harvest the {0}"), Definition->DisplayName)
                   : FText::Format(NSLOCTEXT("Elitewake", "PickUpFish", "Pick up the {0}  (harvest it on land)"), Definition->DisplayName);
}

bool AEWFish::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character) || !Character->GetInventoryComponent()) return false;
    if (Carrier == Character) { SetDown(); return true; }
    if (!bOnLand)
    {
        Carrier = Character;
        Character->SetCarriedFish(this);
        OnRep_State();
        ForceNetUpdate();
        return true;
    }
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

FTransform AEWFish::CarryPose() const
{
    if (!IsValid(Carrier) || !Definition) return GetActorTransform();
    const FTransform Holder(FRotator(0.f, Carrier->GetActorRotation().Yaw, 0.f), Carrier->GetActorLocation());
    // A small catch rides across the shoulders; a big one is dragged behind, on its side.
    if (Definition->Size.X < 150.f)
        return FTransform(FRotator(0.f, 90.f, 0.f), FVector(-12.f, 0.f, 58.f)) * Holder;
    return FTransform(FRotator(0.f, 0.f, 90.f), FVector(-(Definition->Size.X * .5f + 45.f), 0.f, -55.f)) * Holder;
}

void AEWFish::SetDown()
{
    if (!HasAuthority() || !Carrier) return;
    AEWCharacter* Was = Carrier;
    const FVector Front = IsValid(Was) ? Was->GetActorLocation() + FRotator(0.f, Was->GetActorRotation().Yaw, 0.f).Vector() * 110.f
                                       : GetActorLocation();
    if (IsValid(Was)) Was->SetCarriedFish(nullptr);
    Carrier = nullptr;
    // Onto the ground if there is ground above the sea there; otherwise back into the water to float.
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWFishSetDown), false, this);
    if (IsValid(Was)) Query.AddIgnoredActor(Was);
    for (TActorIterator<AWaterBody> It(GetWorld()); It; ++It) Query.AddIgnoredActor(*It);
    const bool bGround = GetWorld()->LineTraceSingleByChannel(Hit, Front + FVector(0, 0, 150.f), Front - FVector(0, 0, 3000.f), ECC_WorldStatic, Query);
    bOnLand = bGround && Hit.ImpactPoint.Z > SurfaceZ + 5.f;
    if (bOnLand)
        SetActorLocationAndRotation(Hit.ImpactPoint + FVector(0, 0, Definition->Size.Y * .3f), FRotator(0.f, GetActorRotation().Yaw, 90.f));
    else
        SetActorLocation(FVector(Front.X, Front.Y, SurfaceZ - Definition->Size.Y * .25f));
    OnRep_State();
    ForceNetUpdate();
}
