#include "EWShip.h"
#include "EWShipDefinition.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "EWPlayerController.h"
#include "EWInteractionComponent.h"
#include "EWWindSubsystem.h"
#include "EW.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"
#include "WaterBodyActor.h"
#include "Ships/EWCannonBall.h"
#include "Ships/EWWreckCrate.h"
#include "Ships/EWShipSoundComponent.h"
#include "Ships/EWWakeTrailComponent.h"
#include "Ships/EWBowWaveComponent.h"

namespace
{
    UStaticMesh* StandInCube() { return LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")); }

    /** Stand-in proportions (cube scale, 1 = 1 m) for fittings without authored meshes. */
    FVector StandInScale(const UEWItemDefinition* Item)
    {
        switch (Item->FittingMountType)
        {
        case EEWShipMountType::Helm: return FVector(.3, .3, .8);
        case EEWShipMountType::Cannon: return FVector(1.2, .35, .35);
        case EEWShipMountType::Utility: return FVector(1, 1, .2);
        case EEWShipMountType::Flag: return FVector(1.5, .02, 1);
        case EEWShipMountType::Sail:
            return Item->FittingSailSize == EEWSailSize::Large ? FVector(.05, 4, 6)
                : Item->FittingSailSize == EEWSailSize::Medium ? FVector(.05, 3, 4.5) : FVector(.05, 2, 3);
        default: return FVector(.3);
        }
    }

    FText MountTypeName(const FEWShipMount& Mount)
    {
        switch (Mount.Type)
        {
        case EEWShipMountType::Helm: return NSLOCTEXT("Elitewake", "MountHelm", "helm");
        case EEWShipMountType::Cannon: return NSLOCTEXT("Elitewake", "MountCannon", "cannon");
        case EEWShipMountType::Utility: return NSLOCTEXT("Elitewake", "MountUtility", "utility attachment");
        case EEWShipMountType::Flag: return NSLOCTEXT("Elitewake", "MountFlag", "flag");
        case EEWShipMountType::Sail:
            return Mount.SailSize == EEWSailSize::Large ? NSLOCTEXT("Elitewake", "MountSailLarge", "large sail")
                : Mount.SailSize == EEWSailSize::Medium ? NSLOCTEXT("Elitewake", "MountSailMedium", "medium sail")
                : NSLOCTEXT("Elitewake", "MountSailSmall", "small sail");
        default: return FText::GetEmpty();
        }
    }
}

AEWShip::AEWShip()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicateMovement(true);
    SetNetUpdateFrequency(30.f);
    HullCollision = CreateDefaultSubobject<UBoxComponent>(TEXT("HullCollision"));
    Sounds = CreateDefaultSubobject<UEWShipSoundComponent>(TEXT("Sounds"));
    WakeTrail = CreateDefaultSubobject<UEWWakeTrailComponent>(TEXT("WakeTrail"));
    BowWave = CreateDefaultSubobject<UEWBowWaveComponent>(TEXT("BowWave"));
    SetRootComponent(HullCollision);
    HullCollision->SetMobility(EComponentMobility::Movable);
    HullCollision->SetCollisionProfileName(TEXT("BlockAll"));
    HullCollision->SetBoxExtent(FVector(400, 150, 90));
    Cargo = CreateDefaultSubobject<UEWInventoryComponent>(TEXT("Cargo"));
    HullVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HullVisual"));
    HullVisual->SetupAttachment(HullCollision);
    HullVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RiggingVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RiggingVisual"));
    RiggingVisual->SetupAttachment(HullCollision);
    RiggingVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WakeVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WakeVisual"));
    WakeVisual->SetupAttachment(HullCollision);
    WakeVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WakeVisual->SetCastShadow(false);
    WakeVisual->SetVisibility(false);
}

void AEWShip::PlaceWake()
{
    if (!Definition || !WakeVisual) return;
    if (!WakeVisual->GetStaticMesh())
        WakeVisual->SetStaticMesh(Cast<UStaticMesh>(FSoftObjectPath(TEXT("/Game/Elitewake/World/Ships/SM_ShipWake_v1.SM_ShipWake_v1")).TryLoad()));
    if (!WakeVisual->GetStaticMesh()) return;
    // The wake mesh is made for the sloop (14 m by 5 m) with its point at the stern; other hulls scale its width. It is
    // the churn just behind the stern, 8 m of it; the foam trail behind her is UEWWakeTrailComponent's.
    const FVector Extent = Definition->HullExtent;
    WakeVisual->SetRelativeScale3D(FVector(800.f / 2800.f, Extent.Y / 250.f, 1.f));
    WakeVisual->SetRelativeLocation(FVector(-Extent.X * .92f, 0.f, SurfaceZ + 3.f - GetActorLocation().Z));
    WakeMaterial = WakeVisual->CreateDynamicMaterialInstance(0);
}

void AEWShip::ShowWake(float DeltaSeconds)
{
    if (!Definition || !WakeMaterial) return;
    const float Wanted = Definition->TopSpeed > 0.f ? FMath::Clamp(FMath::Abs(Speed) / Definition->TopSpeed, 0.f, 1.f) : 0.f;
    WakeStrength = FMath::FInterpTo(WakeStrength, Wanted, DeltaSeconds, 1.5f);
    WakeVisual->SetVisibility(WakeStrength > .02f);
    WakeMaterial->SetScalarParameterValue(TEXT("Foam"), WakeStrength);
}

void AEWShip::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWShip, Definition);
    DOREPLIFETIME(AEWShip, Fittings);
    DOREPLIFETIME(AEWShip, Helmsman);
    DOREPLIFETIME(AEWShip, SailState);
    DOREPLIFETIME(AEWShip, Speed);
    DOREPLIFETIME(AEWShip, Rudder);
    DOREPLIFETIME(AEWShip, RudderAngle);
    DOREPLIFETIME(AEWShip, SailAngle);
    DOREPLIFETIME(AEWShip, bAnchored);
    DOREPLIFETIME(AEWShip, AnchorBed);
    DOREPLIFETIME(AEWShip, ChainReach);
    DOREPLIFETIME(AEWShip, ChainCatches);
    DOREPLIFETIME(AEWShip, bChainTaut);
    DOREPLIFETIME(AEWShip, CapstanWorker);
    DOREPLIFETIME(AEWShip, Cannons);
    DOREPLIFETIME(AEWShip, HullHealth);
    DOREPLIFETIME(AEWShip, Holes);
    DOREPLIFETIME(AEWShip, OpenGunports);
    DOREPLIFETIME(AEWShip, Load);
    DOREPLIFETIME(AEWShip, bOverloaded);
    DOREPLIFETIME(AEWShip, bSwamped);
    DOREPLIFETIME(AEWShip, WaterAboard);
    DOREPLIFETIME(AEWShip, bSinking);
    DOREPLIFETIME(AEWShip, OverloadSecondsLeft);
}

void AEWShip::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyDefinition();
    RefreshFittingVisuals();
}

void AEWShip::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority() && Definition) HullHealth = Definition->HullHealth;
    if (Definition)
    {
        const FString Problem = Definition->Validate();
        if (!Problem.IsEmpty()) UE_LOG(LogEW, Error, TEXT("Ship definition %s is invalid: %s"), *GetNameSafe(Definition), *Problem);
    }
    ApplyDefinition();
    RefreshFittingVisuals();
    PlaceWake();
    // A ship that starts at anchor has her anchor down already, chain out below her bow.
    if (HasAuthority() && bAnchored && ChainReach <= 0.f) LayAnchor();
    // Water bodies answer swimming and wave queries; their collision boxes must never stop a hull.
    for (TActorIterator<AWaterBody> It(GetWorld()); It; ++It) HullCollision->IgnoreActorWhenMoving(*It, true);
}

void AEWShip::PostInitializeComponents()
{
    Super::PostInitializeComponents();
    // Fittings that are part of the hull, fitted as the ship enters play (never in the editor, so maps stay bare).
    if (HasAuthority() && Definition && GetWorld() && GetWorld()->IsGameWorld())
    {
        for (const FEWInstalledFitting& BuiltIn : Definition->BuiltInFittings)
            if (BuiltIn.Item && !GetFitting(BuiltIn.MountId)) Fittings.Add(BuiltIn);
        RefreshFittingVisuals();
    }
}

void AEWShip::OnRep_Definition() { ApplyDefinition(); RefreshFittingVisuals(); }
void AEWShip::OnRep_Fittings() { RefreshFittingVisuals(); }
void AEWShip::OnRep_SailState() { RefreshFittingVisuals(); }

void AEWShip::ApplyDefinition()
{
    for (auto& Pair : MountTargets) if (Pair.Value) Pair.Value->DestroyComponent();
    MountTargets.Reset();
    for (UPointLightComponent* Light : LanternVisuals) if (Light) Light->DestroyComponent();
    LanternVisuals.Reset();
    for (auto& Pair : MastVisuals) if (Pair.Value) Pair.Value->DestroyComponent();
    MastVisuals.Reset();
    // Her lanterns' warm light, below decks, on every machine that draws (no shadows: there are many, and small).
    if (Definition && GetNetMode() != NM_DedicatedServer)
        for (const FVector& At : Definition->LanternLights)
        {
            auto* Light = NewObject<UPointLightComponent>(this, MakeUniqueObjectName(this, UPointLightComponent::StaticClass(), TEXT("Lantern")), RF_Transient);
            Light->SetupAttachment(HullCollision);
            Light->SetRelativeLocation(At);
            Light->SetIntensityUnits(ELightUnits::Candelas);
            Light->SetIntensity(LanternIntensity);
            Light->SetAttenuationRadius(LanternReach);
            Light->SetLightColor(FLinearColor(1.f, .62f, .3f));
            Light->SetCastShadows(false);
            Light->SetSourceRadius(6.f);
            Light->RegisterComponent();
            LanternVisuals.Add(Light);
        }
    for (UBoxComponent* Target : BoardingTargets) if (Target) Target->DestroyComponent();
    BoardingTargets.Reset();
    for (UStaticMeshComponent* Ladder : LadderVisuals) if (Ladder) Ladder->DestroyComponent();
    LadderVisuals.Reset();
    if (AnchorTarget) AnchorTarget->DestroyComponent();
    if (AnchorVisual) AnchorVisual->DestroyComponent();
    if (CapstanVisual) CapstanVisual->DestroyComponent();
    AnchorTarget = nullptr; AnchorVisual = nullptr; CapstanVisual = nullptr;
    for (const TPair<FName, TObjectPtr<UStaticMeshComponent>>& Plain : EmptyMountVisuals) if (Plain.Value) Plain.Value->DestroyComponent();
    EmptyMountVisuals.Empty();
    if (CargoHatchTarget) CargoHatchTarget->DestroyComponent();
    if (CargoHatchVisual) CargoHatchVisual->DestroyComponent();
    CargoHatchTarget = nullptr; CargoHatchVisual = nullptr;
    if (BucketTarget) BucketTarget->DestroyComponent();
    if (BucketVisual) BucketVisual->DestroyComponent();
    BucketTarget = nullptr; BucketVisual = nullptr;
    if (!Definition) return;
    if (HasAuthority() && Cargo) Cargo->SetMaxSlots(Definition->CargoSlots);
    if (HasAuthority() && HullHealth < 0.f) HullHealth = Definition->HullHealth;
    if (HasAuthority() && HullHealth < 0.f) HullHealth = Definition->HullHealth;
    // A modelled hull carries its own hatch, capstan and ladders, and crew walk on the mesh itself.
    UStaticMesh* HullMesh = Definition->HullMesh.LoadSynchronous();
    bModelledHull = HullMesh != nullptr;

    CargoHatchTarget = NewObject<UBoxComponent>(this, MakeUniqueObjectName(this, UBoxComponent::StaticClass(), TEXT("CargoHatch")), RF_Transient);
    CargoHatchTarget->SetupAttachment(HullCollision);
    CargoHatchTarget->SetRelativeLocation(Definition->CargoHatchPoint);
    CargoHatchTarget->SetBoxExtent(FVector(40, 40, 30));
    CargoHatchTarget->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    CargoHatchTarget->SetCollisionResponseToAllChannels(ECR_Ignore);
    CargoHatchTarget->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    CargoHatchTarget->SetGenerateOverlapEvents(false);
    CargoHatchTarget->RegisterComponent();
    CargoHatchVisual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(), TEXT("CargoHatchVisual")), RF_Transient);
    CargoHatchVisual->SetupAttachment(HullCollision);
    CargoHatchVisual->SetStaticMesh(StandInCube());
    // Stand-in hatch: a low square on the deck.
    CargoHatchVisual->SetRelativeTransform(FTransform(FRotator::ZeroRotator,
        FVector(Definition->CargoHatchPoint.X, Definition->CargoHatchPoint.Y, Definition->GetDeckHeight() + 5.f), FVector(.8, .8, .1)));
    CargoHatchVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CargoHatchVisual->SetVisibility(!bModelledHull);
    CargoHatchVisual->RegisterComponent();

    // A bailing bucket stands on deck beside the hatch, on every ship.
    BucketTarget = NewObject<UBoxComponent>(this, MakeUniqueObjectName(this, UBoxComponent::StaticClass(), TEXT("BailBucket")), RF_Transient);
    BucketTarget->SetupAttachment(HullCollision);
    BucketTarget->SetRelativeLocation(BucketPoint() + FVector(0, 0, 20));
    BucketTarget->SetBoxExtent(FVector(25, 25, 25));
    BucketTarget->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    BucketTarget->SetCollisionResponseToAllChannels(ECR_Ignore);
    BucketTarget->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    BucketTarget->SetGenerateOverlapEvents(false);
    BucketTarget->RegisterComponent();
    BucketVisual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(), TEXT("BailBucketVisual")), RF_Transient);
    BucketVisual->SetupAttachment(HullCollision);
    // A modelled bucket (origin at its base) when there is one, else a stand-in: a small cylinder.
    if (UStaticMesh* Bucket = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Elitewake/World/Ships/SM_BailBucket_v1.SM_BailBucket_v1"), nullptr, LOAD_Quiet | LOAD_NoWarn))
    {
        BucketVisual->SetStaticMesh(Bucket);
        BucketVisual->SetRelativeLocation(BucketPoint());
    }
    else
    {
        BucketVisual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder")));
        BucketVisual->SetRelativeTransform(FTransform(FRotator::ZeroRotator, BucketPoint() + FVector(0, 0, 15), FVector(.3, .3, .3)));
    }
    BucketVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BucketVisual->RegisterComponent();

    AnchorTarget = NewObject<UBoxComponent>(this, MakeUniqueObjectName(this, UBoxComponent::StaticClass(), TEXT("AnchorCapstan")), RF_Transient);
    AnchorTarget->SetupAttachment(HullCollision);
    AnchorTarget->SetRelativeLocation(Definition->AnchorPoint);
    AnchorTarget->SetBoxExtent(FVector(30, 30, 40));
    AnchorTarget->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    AnchorTarget->SetCollisionResponseToAllChannels(ECR_Ignore);
    AnchorTarget->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    AnchorTarget->SetGenerateOverlapEvents(false);
    AnchorTarget->RegisterComponent();
    AnchorVisual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(), TEXT("AnchorVisual")), RF_Transient);
    AnchorVisual->SetupAttachment(HullCollision);
    AnchorVisual->SetStaticMesh(StandInCube());
    // Stand-in capstan: a short post on the deck.
    AnchorVisual->SetRelativeTransform(FTransform(FRotator::ZeroRotator,
        FVector(Definition->AnchorPoint.X, Definition->AnchorPoint.Y, Definition->GetDeckHeight() + 35.f), FVector(.4, .4, .7)));
    AnchorVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    AnchorVisual->SetVisibility(!bModelledHull);
    AnchorVisual->RegisterComponent();
    if (UStaticMesh* Capstan = Definition->CapstanMesh.LoadSynchronous())
    {
        CapstanVisual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(), TEXT("CapstanVisual")), RF_Transient);
        CapstanVisual->SetupAttachment(HullCollision);
        CapstanVisual->SetStaticMesh(Capstan);
        CapstanVisual->SetRelativeLocationAndRotation(Definition->CapstanLocation, FRotator(0, CapstanYaw, 0));
        CapstanVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        CapstanVisual->RegisterComponent();
    }

    for (int32 i = 0; i < Definition->BoardingPoints.Num(); ++i)
    {
        const FVector Point = Definition->BoardingPoints[i];
        // The ladder runs from below the waterline up the hull side, so it can be reached by a swimmer or from a dock.
        auto* Target = NewObject<UBoxComponent>(this, MakeUniqueObjectName(this, UBoxComponent::StaticClass(),
            *FString::Printf(TEXT("Ladder_%d"), i)), RF_Transient);
        Target->SetupAttachment(HullCollision);
        // Aim anywhere on it, from just below the water up to the rail: on a tall hull the rungs a swimmer sees are
        // well above the boarding point. A leaning ladder's box leans with it.
        const float Bottom = Point.Z - 90.f;
        float Top = FMath::Max(Point.Z + 90.f, Definition->GetDeckHeight() + 60.f);
        if (Definition->LadderTops.IsValidIndex(i) && !Definition->LadderTops[i].IsNearlyZero()) Top = FMath::Max(Top, Definition->LadderTops[i].Z);
        const FVector Foot = GetLadderLineLocal(i, Bottom), Head = GetLadderLineLocal(i, Top);
        const FVector Outward = GetLadderOutward(i);
        const FVector Along = (Head - Foot).GetSafeNormal();
        Target->SetRelativeLocation((Foot + Head) / 2.f);
        // Box X across the ladder's face (out from the hull), Y along its rungs, Z up the ladder.
        Target->SetRelativeRotation(FRotationMatrix::MakeFromZX(Along, Outward).Rotator());
        Target->SetBoxExtent(FVector(25, 40, FVector::Dist(Foot, Head) / 2.f));
        Target->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Target->SetCollisionResponseToAllChannels(ECR_Ignore);
        Target->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
        Target->SetGenerateOverlapEvents(false);
        Target->RegisterComponent();
        BoardingTargets.Add(Target);
        auto* Ladder = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
            *FString::Printf(TEXT("LadderVisual_%d"), i)), RF_Transient);
        Ladder->SetupAttachment(HullCollision);
        Ladder->SetStaticMesh(StandInCube());
        Ladder->SetRelativeTransform(FTransform(FRotationMatrix::MakeFromXZ(FVector::CrossProduct(FVector::UpVector, GetLadderOutward(i)), FVector::UpVector).Rotator(),
            Point, FVector(.6, .08, 1.8)));
        Ladder->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Ladder->SetVisibility(!bModelledHull);
        Ladder->RegisterComponent();
        LadderVisuals.Add(Ladder);
    }

    HullCollision->SetBoxExtent(Definition->HullExtent);
    RiggingVisual->SetStaticMesh(Definition->RiggingMesh.LoadSynchronous());
    RiggingVisual->SetRelativeTransform(Definition->HullMeshTransform);
    if (bModelledHull)
    {
        HullVisual->SetStaticMesh(HullMesh);
        HullVisual->SetRelativeTransform(Definition->HullMeshTransform);
        // Crew stand on the mesh (deck, hold, stairs) and its bulwarks keep them aboard; the camera stays inside it
        // below deck. Interaction traces pass through to the hull's interaction points.
        HullVisual->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        HullVisual->SetCollisionObjectType(ECC_WorldDynamic);
        HullVisual->SetCollisionResponseToAllChannels(ECR_Block);
        HullVisual->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
        HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
        HullCollision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
        HullCollision->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
        // Round shot (a physics body) strikes the planking itself, not the box around the hull.
        HullCollision->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Ignore);
    }
    else
    {
        HullVisual->SetStaticMesh(StandInCube());
        HullVisual->SetRelativeTransform(FTransform(FRotator::ZeroRotator, FVector::ZeroVector, Definition->HullExtent / 50.f));
        HullVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        HullCollision->SetCollisionProfileName(TEXT("BlockAll"));
    }

    for (const FEWShipMount& Mount : Definition->Mounts)
    {
        if (Mount.MountId.IsNone() || MountTargets.Contains(Mount.MountId)) continue;
        auto* Target = NewObject<UBoxComponent>(this, MakeUniqueObjectName(this, UBoxComponent::StaticClass(),
            *FString::Printf(TEXT("Mount_%s"), *Mount.MountId.ToString())), RF_Transient);
        Target->SetupAttachment(HullCollision);
        Target->SetRelativeTransform(Mount.Transform);
        Target->SetBoxExtent(FVector(30, 30, 40));
        Target->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        Target->SetCollisionResponseToAllChannels(ECR_Ignore);
        Target->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
        Target->SetGenerateOverlapEvents(false);
        Target->RegisterComponent();
        MountTargets.Add(Mount.MountId, Target);
    }
}

void AEWShip::RefreshFittingVisuals()
{
    for (auto It = FittingVisuals.CreateIterator(); It; ++It)
        if (!GetFitting(It.Key()))
        {
            if (It.Value()) It.Value()->DestroyComponent();
            It.RemoveCurrent();
        }
    for (auto It = MastVisuals.CreateIterator(); It; ++It)
        if (!GetFitting(It.Key()))
        {
            if (It.Value()) It.Value()->DestroyComponent();
            It.RemoveCurrent();
        }
    if (!Definition) return;
    for (const FEWInstalledFitting& Fitting : Fittings)
    {
        const FEWShipMount* Mount = Definition->FindMount(Fitting.MountId);
        if (!Mount || !Fitting.Item) continue;
        TObjectPtr<UStaticMeshComponent>& Visual = FittingVisuals.FindOrAdd(Fitting.MountId);
        if (!Visual)
        {
            Visual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
                *FString::Printf(TEXT("Fitting_%s"), *Fitting.MountId.ToString())), RF_Transient);
            Visual->SetupAttachment(HullCollision);
            Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Visual->RegisterComponent();
        }
        if (Mount->Type == EEWShipMountType::Railing) MakeRailingSolid(Visual);
        // The mount's own look wins: the ship's rig decides how a fitting sits on it.
        const bool bMountLook = !Mount->FittedMesh.IsNull();
        FTransform Local = bMountLook ? Mount->FittedMeshTransform : Fitting.Item->FittingMeshTransform;
        UStaticMesh* Mesh = bMountLook ? Mount->FittedMesh.LoadSynchronous() : Fitting.Item->FittingMesh.LoadSynchronous();
        // A flag is the item's own cloth (any flag on any staff), flown at the top of the staff its halyard rises to.
        if (Mount->Type == EEWShipMountType::Flag && !bMountLook) Local = Fitting.Item->FittingMeshTransform * Mount->FittedMeshTransform;
        if (!Mesh)
        {
            // Stand-in box resting on the mount point until real fitting art exists.
            Mesh = StandInCube();
            const FVector Scale = StandInScale(Fitting.Item);
            Local = FTransform(FRotator::ZeroRotator, FVector(0, 0, Scale.Z * 50.f), Scale);
        }
        // Sails follow the helmsman's setting: rolled on their spars when furled, lowered toward their foot at half.
        bool bShown = true;
        if (Mount->Type == EEWShipMountType::Sail && Mesh != StandInCube())
        {
            if (SailState == EEWSailState::Furled)
            {
                Mesh = bMountLook ? Mount->FittedFurledMesh.LoadSynchronous() : Fitting.Item->FittingFurledMesh.LoadSynchronous();
                bShown = Mesh != nullptr;
            }
            else if (SailState == EEWSailState::Half)
            {
                Local.SetScale3D(Local.GetScale3D() * FVector(1, 1, .55f));
            }
        }
        Visual->SetStaticMesh(Mesh);
        Visual->SetVisibility(bShown);
        Visual->SetRelativeTransform(Local * (Mount->Type == EEWShipMountType::Cannon ? GunMountTransform(*Mount) : Mount->Transform));
        if (Mount->Type == EEWShipMountType::Sail) SailLooks.Add(Fitting.MountId, Local);
        if (Mount->Type == EEWShipMountType::Sail && !Mount->MastMesh.IsNull())
        {
            // The assembly's own mast, standing in the socket (the hull has only the empty collar).
            TObjectPtr<UStaticMeshComponent>& Mast = MastVisuals.FindOrAdd(Fitting.MountId);
            if (!Mast)
            {
                Mast = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
                    *FString::Printf(TEXT("Mast_%s"), *Fitting.MountId.ToString())), RF_Transient);
                Mast->SetupAttachment(HullCollision);
                Mast->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                Mast->RegisterComponent();
            }
            Mast->SetStaticMesh(Mount->MastMesh.LoadSynchronous());
            Mast->SetRelativeTransform(Mount->Transform);
        }
        if (Mount->Type == EEWShipMountType::Flag)
        {
            // Its wear frays and holes the cloth (M_Flag_v1); it streams to the wind each frame (ShowFlags).
            Visual->SetCustomPrimitiveDataFloat(0, Fitting.Wear);
            if (Visual->BoundsScale < 2.f) Visual->SetBoundsScale(2.f);
        }
    }
    for (auto It = SailLooks.CreateIterator(); It; ++It) if (!FittingVisuals.Contains(It.Key())) It.RemoveCurrent();
    for (auto It = FlagYaw.CreateIterator(); It; ++It) if (!FittingVisuals.Contains(It.Key())) It.RemoveCurrent();
    // An empty railing hardpoint keeps its plain railing (owner, October 17), shown and solid until a module replaces it.
    for (const FEWShipMount& Mount : Definition->Mounts)
    {
        UStaticMesh* Plain = Mount.EmptyMesh.IsNull() ? nullptr : Mount.EmptyMesh.LoadSynchronous();
        TObjectPtr<UStaticMeshComponent>* Shown = EmptyMountVisuals.Find(Mount.MountId);
        if (!Plain || GetFitting(Mount.MountId))
        {
            if (Shown && *Shown) (*Shown)->DestroyComponent();
            EmptyMountVisuals.Remove(Mount.MountId);
            continue;
        }
        if (!Shown || !*Shown)
        {
            UStaticMeshComponent* Visual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
                *FString::Printf(TEXT("Empty_%s"), *Mount.MountId.ToString())), RF_Transient);
            Visual->SetupAttachment(HullCollision);
            Visual->SetStaticMesh(Plain);
            Visual->SetRelativeTransform(Mount.Transform);
            MakeRailingSolid(Visual);
            Visual->RegisterComponent();
            EmptyMountVisuals.Add(Mount.MountId, Visual);
        }
    }
    ShowSailTrim();

    // A helm's turning part (wheel, tiller) is its own piece, so it can turn with the rudder.
    for (auto It = TurningVisuals.CreateIterator(); It; ++It)
    {
        const UEWItemDefinition* Item = GetFitting(It.Key());
        if (!Item || Item->FittingTurningMesh.IsNull())
        {
            if (It.Value()) It.Value()->DestroyComponent();
            TurningRest.Remove(It.Key());
            It.RemoveCurrent();
        }
    }
    for (const FEWInstalledFitting& Fitting : Fittings)
    {
        const FEWShipMount* Mount = Definition->FindMount(Fitting.MountId);
        UStaticMesh* Turning = Fitting.Item ? Fitting.Item->FittingTurningMesh.LoadSynchronous() : nullptr;
        if (!Mount || !Turning) continue;
        TObjectPtr<UStaticMeshComponent>& Visual = TurningVisuals.FindOrAdd(Fitting.MountId);
        if (!Visual)
        {
            Visual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
                *FString::Printf(TEXT("Turning_%s"), *Fitting.MountId.ToString())), RF_Transient);
            Visual->SetupAttachment(HullCollision);
            Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Visual->RegisterComponent();
        }
        Visual->SetStaticMesh(Turning);
        TurningRest.Add(Fitting.MountId, Fitting.Item->FittingTurningPivot * Fitting.Item->FittingMeshTransform
            * (Mount->Type == EEWShipMountType::Cannon ? GunMountTransform(*Mount) : Mount->Transform));
    }
    ShowTurning(0.f);
}

void AEWShip::ShowTurning(float DeltaSeconds)
{
    // Ease toward the replicated blade angle so a client's wheel turns smoothly between updates.
    ShownRudderAngle = DeltaSeconds > 0.f ? FMath::FInterpConstantTo(ShownRudderAngle, RudderAngle, DeltaSeconds, RudderRate * 1.5f) : RudderAngle;
    for (const TPair<FName, TObjectPtr<UStaticMeshComponent>>& Pair : TurningVisuals)
    {
        const UEWItemDefinition* Item = GetFitting(Pair.Key);
        const FTransform* Rest = TurningRest.Find(Pair.Key);
        if (!Item || !Rest || !Pair.Value) continue;
        // A cannon's barrel is aimed; a helm's wheel or tiller turns with the rudder.
        const FRotator Turn = Item->FittingMountType == EEWShipMountType::Cannon ? GetCannonAim(Pair.Key) : Item->FittingTurnAtFull * ShownRudderAngle;
        Pair.Value->SetRelativeTransform(FTransform(Turn) * *Rest);
    }
}

void AEWShip::ShowSailTrim()
{
    if (!Definition) return;
    // Every sail's look has its origin where it turns, on the mast or the stay, with Z up it. A boom and a jib's
    // clew both lie aft, so swinging the sails out to starboard turns them about Z the negative way.
    for (const TPair<FName, FTransform>& Look : SailLooks)
    {
        const FEWShipMount* Mount = Definition->FindMount(Look.Key);
        const TObjectPtr<UStaticMeshComponent>* Visual = FittingVisuals.Find(Look.Key);
        if (Mount && Visual && *Visual)
            (*Visual)->SetRelativeTransform(FTransform(FRotator(0, -ShownSailAngle, 0)) * Look.Value * Mount->Transform);
        // The mast turns about its own upright axis with the sail it carries.
        if (const TObjectPtr<UStaticMeshComponent>* Mast = MastVisuals.Find(Look.Key); Mount && Mast && *Mast)
            (*Mast)->SetRelativeTransform(FTransform(FRotator(0, -ShownSailAngle, 0)) * Mount->Transform);
    }
}

void AEWShip::ShowSailFill(float DeltaSeconds)
{
    const UEWWindSubsystem* Wind = UEWWindSubsystem::GetForWorld(this);
    if (!Wind) return;
    const FVector Blow = Wind->GetWindDirection();
    for (auto It = SailFill.CreateIterator(); It; ++It) if (!SailLooks.Contains(It.Key())) It.RemoveCurrent();
    for (const TPair<FName, FTransform>& Look : SailLooks)
    {
        const TObjectPtr<UStaticMeshComponent>* Visual = FittingVisuals.Find(Look.Key);
        if (!Visual || !*Visual || !(*Visual)->GetStaticMesh()) continue;
        UStaticMeshComponent* Sail = *Visual;
        // The cloth bellies across its thinnest side (built so: Y for gaff sails and jibs, X for square sails).
        const FVector Extent = Sail->GetStaticMesh()->GetBounds().BoxExtent;
        const FVector Across = Sail->GetComponentTransform().TransformVectorNoScale(Extent.X < Extent.Y ? FVector::ForwardVector : FVector::RightVector);
        // Square on to the wind it fills; with the wind along it, it hangs slack (tuning: slack below 7 degrees of
        // incidence, full from about 33).
        const float Strike = FVector::DotProduct(Blow, Across.GetSafeNormal2D());
        const float Target = SailState == EEWSailState::Furled ? 0.f : FMath::Sign(Strike) * FMath::SmoothStep(.12f, .55f, FMath::Abs(Strike));
        float& Shown = SailFill.FindOrAdd(Look.Key);
        // Fills and empties over about a second: no pop when the sail swings through the wind.
        Shown = DeltaSeconds > 0.f ? FMath::FInterpTo(Shown, Target, DeltaSeconds, SailFillRate) : Target;
        Sail->SetCustomPrimitiveDataFloat(0, Shown);
        // The cloth moves beyond the mesh's bounds when it bellies the other way.
        if (Sail->BoundsScale < 2.f) Sail->SetBoundsScale(2.f);
    }
}

FTransform AEWShip::GetFlagLookWorld(const FEWShipMount& Mount, const UEWItemDefinition* Item) const
{
    const FTransform Local = !Mount.FittedMesh.IsNull() || !Item ? Mount.FittedMeshTransform : Item->FittingMeshTransform * Mount.FittedMeshTransform;
    return Local * Mount.Transform * GetActorTransform();
}

float AEWShip::GetFlagWear(FName MountId) const
{
    const FEWInstalledFitting* Found = Fittings.FindByPredicate([MountId](const FEWInstalledFitting& F) { return F.MountId == MountId; });
    return Found && Found->Item && Found->Item->FittingMountType == EEWShipMountType::Flag ? Found->Wear : -1.f;
}

void AEWShip::ShowFlags(float DeltaSeconds)
{
    const UEWWindSubsystem* Wind = UEWWindSubsystem::GetForWorld(this);
    if (!Wind || !Definition) return;
    // The wind a flag feels aboard: the world's wind less the ship's own way through the water.
    const FVector Apparent = Wind->GetWindDirection() * FlagWindSpeed - GetActorForwardVector() * Speed;
    const float Downwind = FMath::RadiansToDegrees(FMath::Atan2(Apparent.Y, Apparent.X));
    const float Flutter = FMath::Clamp(Apparent.Size2D() / 1200.f, .3f, 1.5f);
    for (const FEWInstalledFitting& Fitting : Fittings)
    {
        if (!Fitting.Item || Fitting.Item->FittingMountType != EEWShipMountType::Flag) continue;
        const TObjectPtr<UStaticMeshComponent>* Visual = FittingVisuals.Find(Fitting.MountId);
        if (!Visual || !*Visual) continue;
        float& Yaw = FlagYaw.FindOrAdd(Fitting.MountId, Downwind);
        Yaw = DeltaSeconds > 0.f ? FMath::FixedTurn(Yaw, Downwind, FlagSwingRate * DeltaSeconds) : Downwind;
        // Upright on its staff whatever the ship's roll, the hoist at the staff and the fly streaming out along +X.
        (*Visual)->SetWorldRotation(FRotator(0.f, Yaw, 0.f));
        (*Visual)->SetCustomPrimitiveDataFloat(1, Flutter);
    }
}

void AEWShip::WearFlags(const FVector& Where)
{
    if (!HasAuthority() || !Definition) return;
    bool bChanged = false;
    for (int32 Index = Fittings.Num() - 1; Index >= 0; --Index)
    {
        FEWInstalledFitting& Fitting = Fittings[Index];
        const FEWShipMount* Mount = Definition->FindMount(Fitting.MountId);
        if (!Mount || !Fitting.Item || Fitting.Item->FittingMountType != EEWShipMountType::Flag) continue;
        const bool bNear = FVector::Dist(GetFlagLookWorld(*Mount, Fitting.Item).GetLocation(), Where) < FlagNearHitRange;
        Fitting.Wear = FMath::Min(1.f, Fitting.Wear + FlagWearPerHit + (bNear ? FlagWearNearHit : 0.f));
        // Shot to pieces: the cloth is gone and nothing comes back; the staff (part of the hull) stays.
        if (Fitting.Wear >= 1.f) Fittings.RemoveAt(Index);
        bChanged = true;
    }
    if (bChanged) RefreshFittingVisuals();
}

void AEWShip::MakeRailingSolid(UStaticMeshComponent* Visual)
{
    Visual->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Visual->SetCollisionResponseToAllChannels(ECR_Ignore);
    Visual->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
}

bool AEWShip::IsMountOpen(FName MountId) const
{
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Mount) return false;
    if (Mount->ParentMount.IsNone()) return true;
    const UEWItemDefinition* Module = GetFitting(Mount->ParentMount);
    return Module && Module->FittingCannonSlots >= Mount->ParentSlot;
}

UEWItemDefinition* AEWShip::GetFitting(FName MountId) const
{
    const FEWInstalledFitting* Found = Fittings.FindByPredicate([MountId](const FEWInstalledFitting& F) { return F.MountId == MountId; });
    return Found ? Found->Item : nullptr;
}

bool AEWShip::HasFittingOfType(EEWShipMountType Type) const
{
    return Fittings.ContainsByPredicate([Type](const FEWInstalledFitting& F) { return F.Item && F.Item->FittingMountType == Type; });
}

FTransform AEWShip::GetMountWorldTransform(FName MountId) const
{
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    return Mount ? Mount->Transform * GetActorTransform() : FTransform::Identity;
}

const UPrimitiveComponent* AEWShip::TraceAimedComponent(const AEWCharacter* Character) const
{
    if (!IsValid(Character) || !Character->GetWorld() || !Character->GetController()
        || Character->GetController()->GetPawn() != Character) return nullptr;
    FVector Eye; FRotator Rotation;
    Character->GetActorEyesViewPoint(Eye, Rotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWShipAim), false, Character);
    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(Hit, Eye, Eye + Rotation.Vector() * FEWInteractionTargeting::Range, ECC_Visibility, Query)
        || Hit.GetActor() != this) return nullptr;
    return Hit.GetComponent();
}

FName AEWShip::FindAimedMount(const AEWCharacter* Character) const
{
    const UPrimitiveComponent* Aimed = TraceAimedComponent(Character);
    if (!Aimed) return NAME_None;
    for (const auto& Pair : MountTargets) if (Pair.Value == Aimed) return Pair.Key;
    return NAME_None;
}

int32 AEWShip::FindAimedBoardingPoint(const AEWCharacter* Character) const
{
    const UPrimitiveComponent* Aimed = TraceAimedComponent(Character);
    return Aimed ? BoardingTargets.IndexOfByKey(Aimed) : INDEX_NONE;
}

FVector AEWShip::GetBoardingPointWorld(int32 Index) const
{
    return Definition && Definition->BoardingPoints.IsValidIndex(Index)
        ? GetActorTransform().TransformPosition(Definition->BoardingPoints[Index]) : FVector::ZeroVector;
}

float AEWShip::GetDeckHeight() const
{
    return Definition ? Definition->GetDeckHeight() : 0.f;
}

bool AEWShip::IsAboard(const AEWCharacter* Character) const
{
    if (!IsValid(Character) || !Definition) return false;
    if (Character->GetHelmShip() == this) return true;
    if (const auto* Base = Cast<UPrimitiveComponent>(Character->GetMovementBaseObject()); Base && Base->GetOwner() == this) return true;
    // Standing over the deck counts too, for the moment before movement settles onto it.
    const FVector Local = GetActorTransform().InverseTransformPosition(Character->GetActorLocation());
    const FVector& E = Definition->HullExtent;
    // Anywhere from the hold floor up, within the hull's footprint.
    const float Floor = bModelledHull ? Definition->HoldFloorHeight : Definition->GetDeckHeight();
    return FMath::Abs(Local.X) <= E.X + 10.f && FMath::Abs(Local.Y) <= E.Y + 10.f && Local.Z >= Floor;
}

FVector AEWShip::BucketPoint() const
{
    if (!Definition) return FVector::ZeroVector;
    return FVector(Definition->CargoHatchPoint.X - 110.f, Definition->CargoHatchPoint.Y, Definition->GetDeckHeight());
}

FVector AEWShip::GetBucketWorld() const
{
    return GetActorTransform().TransformPosition(BucketPoint());
}

bool AEWShip::IsAimingAtBucket(const AEWCharacter* Character) const
{
    return BucketTarget && TraceAimedComponent(Character) == BucketTarget;
}

int32 AEWShip::GetLeakCount() const
{
    // The sea's surface in the ship's own space (the swell and heel aside): holes under it, or just above where the
    // sea washes over, let water in. The deeper she settles, the more holes go under.
    const float Waterline = SurfaceZ - GetActorLocation().Z;
    int32 Count = 0;
    for (const FEWHullHole& Hole : Holes) if (Hole.Local.Z < Waterline + WaterlineWash) ++Count;
    return Count;
}

float AEWShip::GetSettle() const
{
    return MaxSettle * FMath::Clamp(WaterAboard / FMath::Max(GetWeightCapacity(), 1.f), 0.f, 1.f);
}

void AEWShip::StartSinking()
{
    if (!HasAuthority() || bSinking) return;
    bSinking = true;
    SinkingFor = 0.f;
    // Everyone at a station lets go; the crew are left standing on a deck that is going under.
    if (IsValid(Helmsman)) LeaveHelm(Helmsman, true);
    for (const FEWCannonState& Cannon : Cannons)
        if (AEWCharacter* Gunner = GetCannonGunner(Cannon.MountId)) LeaveCannon(Gunner, true);
    SetCapstanWorker(nullptr);
    Rudder = 0.f;
    SailTrimDirection = 0;
    // Her hold and her fittings float up in crates round where she went down (DECIDED, delegated: fittings too).
    TArray<FEWInventoryEntry> Goods = Cargo ? Cargo->GetInventoryEntries() : TArray<FEWInventoryEntry>();
    for (const FEWInstalledFitting& Fitting : Fittings)
        if (Fitting.Item) { FEWInventoryEntry Entry; Entry.ItemDefinition = Fitting.Item; Entry.Quantity = 1; Goods.Add(Entry); }
    const FVector Middle = GetActorLocation();
    for (int32 First = 0, Crate = 0; First < Goods.Num(); First += AEWWreckCrate::SlotsPerCrate, ++Crate)
    {
        const float Angle = Crate * 2.39996f;
        const FVector Where(Middle.X + FMath::Cos(Angle) * (250.f + 120.f * Crate), Middle.Y + FMath::Sin(Angle) * (250.f + 120.f * Crate), SurfaceZ);
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        auto* Wreck = GetWorld()->SpawnActor<AEWWreckCrate>(Where, FRotator(0, FMath::RadiansToDegrees(Angle), 0), Params);
        if (!Wreck) continue;
        Wreck->SurfaceZ = SurfaceZ;
        Wreck->GetContents()->SetMaxSlots(AEWWreckCrate::SlotsPerCrate);
        for (int32 i = First; i < FMath::Min(First + AEWWreckCrate::SlotsPerCrate, Goods.Num()); ++i)
            Wreck->GetContents()->AddItem(Goods[i].ItemDefinition, Goods[i].Quantity);
    }
    if (Cargo) for (const FEWInventoryEntry& Entry : Cargo->GetInventoryEntries()) Cargo->RemoveItem(Entry.ItemDefinition, Entry.Quantity);
    ForceNetUpdate();
}

void AEWShip::UpdateLeaks(float DeltaSeconds)
{
    if (!HasAuthority() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    // A destroyed hull, or one full of water, goes down (never a ship that cannot sink).
    if (!bSinking && Definition && !Definition->bCannotSink
        && ((HullHealth == 0.f) || WaterAboard >= GetWeightCapacity() * 1.5f - KINDA_SMALL_NUMBER))
        StartSinking();
    if (bSinking) return;
    const int32 Leaks = GetLeakCount();
    if (!Leaks) return;
    // Until sinking exists (M2), the water stops rising once she holds half again her capacity.
    const float Before = WaterAboard;
    WaterAboard = FMath::Min(WaterAboard + Leaks * LeakPerHole * DeltaSeconds, GetWeightCapacity() * 1.5f);
    if (FMath::FloorToInt(Before / 10.f) != FMath::FloorToInt(WaterAboard / 10.f)) ForceNetUpdate();
}

bool AEWShip::IsAimingAtCargoHatch(const AEWCharacter* Character) const
{
    return CargoHatchTarget && TraceAimedComponent(Character) == CargoHatchTarget;
}

FVector AEWShip::GetCargoHatchWorld() const
{
    return Definition ? GetActorTransform().TransformPosition(Definition->CargoHatchPoint) : GetActorLocation();
}

bool AEWShip::CanAccessCargo(const AEWCharacter* Character) const
{
    return Cargo && CanModifyFittings(Character)
        && (IsAboard(Character) || FVector::Dist(Character->GetActorLocation(), GetCargoHatchWorld()) <= CargoReach);
}

float AEWShip::GetLoad() const
{
    if (!HasAuthority()) return Load;
    float Total = (Cargo ? Cargo->GetTotalWeight() : 0.f) + WaterAboard;
    for (const FEWInstalledFitting& Fitting : Fittings) if (Fitting.Item) Total += Fitting.Item->UnitWeight;
    return Total;
}

float AEWShip::GetWeightCapacity() const
{
    return Definition ? Definition->WeightCapacity : 1.f;
}

float AEWShip::GetLoadSpeedFactor() const
{
    const float Ratio = GetLoad() / FMath::Max(GetWeightCapacity(), 1.f);
    if (Ratio > 1.f) return .4f;
    if (Ratio <= .5f) return 1.f;
    return FMath::Lerp(1.f, .6f, (Ratio - .5f) / .5f);
}

void AEWShip::UpdateLoad(float DeltaSeconds)
{
    if (!HasAuthority() || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds < 0.f) return;
    Load = GetLoad();
    const bool bWasOverloaded = bOverloaded, bWasSwamped = bSwamped;
    bOverloaded = Load > GetWeightCapacity();
    if (!bOverloaded)
    {
        // Lightening below capacity clears the countdown and frees a swamped ship.
        OverloadSecondsLeft = OverloadGraceSeconds;
        bSwamped = false;
    }
    else if (!bSwamped)
    {
        OverloadSecondsLeft = FMath::Max(0.f, OverloadSecondsLeft - DeltaSeconds);
        bSwamped = OverloadSecondsLeft <= 0.f;
    }
    if (bWasOverloaded != bOverloaded || bWasSwamped != bSwamped) ForceNetUpdate();
}

bool AEWShip::IsAimingAtAnchor(const AEWCharacter* Character) const
{
    return AnchorTarget && TraceAimedComponent(Character) == AnchorTarget;
}

FVector AEWShip::GetAnchorPointWorld() const
{
    return Definition ? GetActorTransform().TransformPosition(Definition->AnchorPoint) : GetActorLocation();
}

bool AEWShip::SetAnchored(AEWCharacter* Character, bool bNewAnchored)
{
    if (!HasAuthority() || bChangingFittings || !CanModifyFittings(Character) || bAnchored == bNewAnchored) return false;
    bAnchored = bNewAnchored;
    if (bAnchored) LayAnchor();
    bChainTaut = false;
    ForceNetUpdate();
    return true;
}

FVector AEWShip::HawseLocal() const
{
    // At the stem, half way up the bow: where the chain runs out of the hull.
    if (!Definition) return FVector::ZeroVector;
    return FVector(Definition->HullExtent.X * .88f, 0.f, Definition->GetDeckHeight() * .5f);
}

FVector AEWShip::GetHawseWorld() const
{
    return GetActorTransform().TransformPosition(HawseLocal());
}

void AEWShip::LayAnchor()
{
    // The anchor goes straight down from the hawse to the bottom (the sea floor or whatever lies there).
    const FVector Hawse = GetHawseWorld();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWAnchorBed), false, this);
    for (TActorIterator<AWaterBody> It(GetWorld()); It; ++It) Query.AddIgnoredActor(*It);
    FHitResult Hit;
    const FVector Deepest = Hawse - FVector(0, 0, 6000.f);
    AnchorBed = GetWorld()->LineTraceSingleByChannel(Hit, Hawse, Deepest, ECC_Visibility, Query) ? Hit.ImpactPoint : Deepest;
    const float Depth = FMath::Max(GetActorLocation().Z - AnchorBed.Z, 100.f);
    ChainReach = FMath::Clamp(Depth * ChainSlackPerDepth, MinChainSlack, MaxChainSlack);
}

float AEWShip::ChainLength() const
{
    const float Depth = FMath::Max(GetHawseWorld().Z - AnchorBed.Z, 0.f);
    return FMath::Sqrt(FMath::Square(ChainReach) + FMath::Square(Depth));
}

int32 AEWShip::GetChainLinkCount() const
{
    return ChainLinks ? ChainLinks->GetInstanceCount() : 0;
}

void AEWShip::ShowChain(float DeltaSeconds)
{
    if (GetNetMode() == NM_DedicatedServer || !Definition) return;
    if (!ChainLinks)
    {
        ChainLinks = NewObject<UInstancedStaticMeshComponent>(this, NAME_None, RF_Transient);
        ChainLinks->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder")));
        if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
        {
            UMaterialInstanceDynamic* Iron = UMaterialInstanceDynamic::Create(Base, this);
            Iron->SetVectorParameterValue(TEXT("Color"), FLinearColor(.035f, .033f, .03f));
            ChainLinks->SetMaterial(0, Iron);
        }
        ChainLinks->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        ChainLinks->SetCastShadow(false);
        ChainLinks->SetUsingAbsoluteLocation(true);
        ChainLinks->SetUsingAbsoluteRotation(true);
        ChainLinks->SetUsingAbsoluteScale(true);
        ChainLinks->RegisterComponent();
        ChainLinks->SetWorldTransform(FTransform::Identity);
        bShownAnchored = bAnchored;
        ChainOut = bAnchored ? 1.f : 0.f;   // a ship found at anchor has her chain out already
    }
    if (bAnchored && !bShownAnchored) ChainOut = 0.f;   // just dropped: it pays out from the hawse
    bShownAnchored = bAnchored;
    // Paying out over the drop's rattle; coming in at the capstan over the heave; out again if the heave stops.
    const float Wanted = !bAnchored ? 0.f : (CapstanWorker ? 0.f : 1.f);
    const float Rate = CapstanWorker ? 1.f / AnchorHoldSeconds : 1.f / 2.2f;
    ChainOut = FMath::FInterpConstantTo(ChainOut, Wanted, DeltaSeconds, Rate);
    // The bow dips when the chain snubs her up.
    if (ChainCatches != ShownChainCatches)
    {
        ShownChainCatches = ChainCatches;
        ChainJerk = 1.f;
    }
    ChainJerk = FMath::FInterpConstantTo(ChainJerk, 0.f, DeltaSeconds, .8f);
    ChainLinks->ClearInstances();
    if (ChainOut <= .01f || ChainReach <= 0.f) return;
    const FVector Hawse = GetHawseWorld();
    // Where the anchor is: on the bottom once out, on its way down (or up) before.
    const FVector Bed = AnchorBed;
    const FVector Below(Hawse.X, Hawse.Y, Bed.Z);
    const FVector End = ChainOut >= 1.f ? Bed : FMath::Lerp(Hawse, FMath::Lerp(Below, Bed, ChainOut), ChainOut);
    const float Length = ChainLength() * ChainOut;
    const float Span = FVector::Dist(Hawse, End);
    // Slack chain sags into a curve (and lies along the bottom); taut, it runs nearly straight.
    const float Sag = .5f * FMath::Sqrt(FMath::Max(FMath::Square(Length) - FMath::Square(Span), 0.f)) + 10.f;
    const int32 Links = FMath::Clamp(int32(Span / 28.f), 2, 400);
    FVector Last = Hawse;
    for (int32 k = 1; k <= Links; ++k)
    {
        const float T = float(k) / Links;
        FVector P = FMath::Lerp(Hawse, End, T) - FVector(0, 0, Sag * 4.f * T * (1.f - T));
        P.Z = FMath::Max(P.Z, Bed.Z + 4.f);
        const FVector Mid = (Last + P) / 2.f;
        const FVector Along = P - Last;
        // Each link a short iron bar, alternate ones turned a quarter, about 4 cm thick.
        const FRotator Turn = FRotationMatrix::MakeFromZ(Along.GetSafeNormal()).Rotator() + FRotator(0, 0, k % 2 ? 90.f : 0.f);
        ChainLinks->AddInstance(FTransform(Turn, Mid, FVector(.05f, .03f, FMath::Max(Along.Size(), 1.f) / 100.f)), true);
        Last = P;
    }
}

bool AEWShip::ClimbAboard(AEWCharacter* Character, int32 BoardingIndex)
{
    if (!HasAuthority() || bChangingFittings || !CanModifyFittings(Character) || Character->GetHelmShip()
        || !Definition->BoardingPoints.IsValidIndex(BoardingIndex) || IsAboard(Character)) return false;
    const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const float HalfHeight = Capsule ? Capsule->GetScaledCapsuleHalfHeight() : 90.f;
    // Step onto the deck about a metre inboard of the ladder's head, clear of the bulwark; if something stands there
    // (a stern ladder comes up behind the helm), a little further in or to either side.
    float Bottom, Top;
    GetLadderSpan(BoardingIndex, Bottom, Top);
    const FVector Head = GetLadderLineLocal(BoardingIndex, Top);
    const FVector Outward = GetLadderOutward(BoardingIndex);
    const FVector Across = FVector::CrossProduct(FVector::UpVector, Outward);
    FVector Destination = FVector::ZeroVector;
    bool bFound = false;
    for (const float In : {110.f, 180.f, 250.f})
    {
        for (const float Aside : {0.f, 90.f, -90.f})
        {
            FVector Deck = Head - Outward * In + Across * Aside;
            if (FMath::Abs(Outward.Y) > .5f && Deck.Y * Outward.Y < 0.f) Deck.Y = 0.f;   // never past the centreline
            // On whichever deck is there: the main deck, or a raised quarterdeck at the stern.
            float Floor = Definition->GetDeckHeight();
            FCollisionQueryParams Query(SCENE_QUERY_STAT(EWShipBoarding), false, Character);
            FHitResult Hit;
            const FTransform& Frame = GetActorTransform();
            if (GetWorld()->LineTraceSingleByChannel(Hit, Frame.TransformPosition(FVector(Deck.X, Deck.Y, Top + 400.f)),
                    Frame.TransformPosition(FVector(Deck.X, Deck.Y, Floor - 40.f)), ECC_Visibility, Query) && Hit.GetActor() == this)
                Floor = Frame.InverseTransformPosition(Hit.ImpactPoint).Z;
            Deck.Z = Floor + HalfHeight + 2.f;
            const FVector Candidate = GetActorTransform().TransformPosition(Deck);
            if (!Capsule || !GetWorld()->OverlapBlockingTestByChannel(Candidate, FQuat::Identity, ECC_Pawn, Capsule->GetCollisionShape(), Query))
            {
                Destination = Candidate;
                bFound = true;
                break;
            }
        }
        if (bFound) break;
    }
    if (!bFound) return false;
    Character->SetActorLocation(Destination, false, nullptr, ETeleportType::TeleportPhysics);
    if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement()) Movement->SetMovementMode(MOVE_Falling);
    Character->ForceNetUpdate();
    return true;
}

EEWInteractionMode AEWShip::GetInteractionModeFor_Implementation(AEWCharacter* Character) const
{
    // A ladder is grabbed with a press; fittings, the anchor and the hold keep a deliberate hold.
    return FindAimedBoardingPoint(Character) != INDEX_NONE ? EEWInteractionMode::Press : EEWInteractionMode::Hold;
}

void AEWShip::GetLadderSpan(int32 BoardingIndex, float& Bottom, float& Top) const
{
    const FVector Point = Definition && Definition->BoardingPoints.IsValidIndex(BoardingIndex)
        ? Definition->BoardingPoints[BoardingIndex] : FVector::ZeroVector;
    Bottom = Point.Z - 10.f;
    Top = FMath::Max(Bottom + 20.f, GetDeckHeight() + 30.f);
    // A ladder with a head given (up a stern to a quarterdeck) is climbed until the hands are at its head.
    if (Definition && Definition->LadderTops.IsValidIndex(BoardingIndex) && !Definition->LadderTops[BoardingIndex].IsNearlyZero())
        Top = FMath::Max(Top, Definition->LadderTops[BoardingIndex].Z - 90.f);
}

FVector AEWShip::GetLadderOutward(int32 BoardingIndex) const
{
    const FVector Point = Definition && Definition->BoardingPoints.IsValidIndex(BoardingIndex)
        ? Definition->BoardingPoints[BoardingIndex] : FVector::ZeroVector;
    if (FMath::Abs(Point.Y) >= 1.f) return FVector(0, FMath::Sign(Point.Y), 0);
    return FVector(Point.X >= 0.f ? 1.f : -1.f, 0, 0);
}

FVector AEWShip::GetLadderLineLocal(int32 BoardingIndex, float Height) const
{
    if (!Definition || !Definition->BoardingPoints.IsValidIndex(BoardingIndex)) return FVector(0, 0, Height);
    const FVector Point = Definition->BoardingPoints[BoardingIndex];
    const FVector Head = Definition->LadderTops.IsValidIndex(BoardingIndex) ? Definition->LadderTops[BoardingIndex] : FVector::ZeroVector;
    if (Head.IsNearlyZero() || FMath::IsNearlyEqual(Head.Z, Point.Z)) return FVector(Point.X, Point.Y, Height);
    // Along the straight line from the foot to the head (and on past either end, at the same lean).
    const float Alpha = (Height - Point.Z) / (Head.Z - Point.Z);
    return FVector(FMath::Lerp(Point.X, Head.X, Alpha), FMath::Lerp(Point.Y, Head.Y, Alpha), Height);
}

FTransform AEWShip::GetLadderPoseLocal(int32 BoardingIndex, float Height, float Radius) const
{
    const FVector Outward = GetLadderOutward(BoardingIndex);
    // Just outboard of the rungs, which run a little inside the boarding point, facing the hull.
    return FTransform((-Outward).Rotation(), GetLadderLineLocal(BoardingIndex, Height) + Outward * (Radius - 18.f));
}

bool AEWShip::StartClimb(AEWCharacter* Character, int32 BoardingIndex)
{
    if (!HasAuthority() || bChangingFittings || !CanModifyFittings(Character) || Character->GetHelmShip() || Character->IsOnLadder()
        || !Definition->BoardingPoints.IsValidIndex(BoardingIndex) || IsAboard(Character)) return false;
    float Bottom, Top;
    GetLadderSpan(BoardingIndex, Bottom, Top);
    const float Here = GetActorTransform().InverseTransformPosition(Character->GetActorLocation()).Z;
    Character->SetLadder(this, BoardingIndex, FMath::Clamp(Here, Bottom, Top));
    return true;
}

bool AEWShip::CanModifyFittings(const AEWCharacter* Character) const
{
    return Definition && IsValid(Character) && !Character->IsActorBeingDestroyed() && !IsActorBeingDestroyed()
        && Character->GetWorld() == GetWorld() && Character->GetController() && Character->GetController()->GetPawn() == Character
        && Character->GetInventoryComponent() && Character->GetSurvivalComponent()
        && Character->GetSurvivalComponent()->GetHealth() > 0;
}

UEWItemDefinition* AEWShip::FindCarriedFitting(const AEWCharacter* Character, const FEWShipMount& Mount) const
{
    for (const FEWInventoryEntry& Entry : Character->GetInventoryComponent()->GetInventoryEntries())
        if (Entry.Quantity > 0 && UEWShipDefinition::Accepts(Mount, Entry.ItemDefinition)) return Entry.ItemDefinition;
    return nullptr;
}

EEWFittingResult AEWShip::InstallFitting(AEWCharacter* Character, FName MountId)
{
    if (!HasAuthority() || bChangingFittings) return EEWFittingResult::Busy;
    if (!CanModifyFittings(Character)) return EEWFittingResult::NotAllowed;
    const FEWShipMount* Mount = Definition->FindMount(MountId);
    if (!Mount) return EEWFittingResult::NoMount;
    if (!IsMountOpen(MountId)) return EEWFittingResult::NeedsRailing;
    if (GetFitting(MountId)) return EEWFittingResult::Occupied;
    UEWItemDefinition* Item = FindCarriedFitting(Character, *Mount);
    if (!Item) return EEWFittingResult::NoFitting;
    TGuardValue<bool> Guard(bChangingFittings, true);
    // The unit leaves the inventory before it appears on the ship, so a failed removal installs nothing.
    if (Character->GetInventoryComponent()->RemoveItem(Item, 1) != 1) return EEWFittingResult::NoFitting;
    Fittings.Add({MountId, Item});
    RefreshFittingVisuals();
    ForceNetUpdate();
    return EEWFittingResult::Installed;
}

EEWFittingResult AEWShip::RemoveFitting(AEWCharacter* Character, FName MountId)
{
    if (!HasAuthority() || bChangingFittings) return EEWFittingResult::Busy;
    if (!CanModifyFittings(Character)) return EEWFittingResult::NotAllowed;
    const int32 Index = Fittings.IndexOfByPredicate([MountId](const FEWInstalledFitting& F) { return F.MountId == MountId; });
    if (Index == INDEX_NONE) return EEWFittingResult::NoMount;
    if (Definition && Definition->IsBuiltIn(MountId)) return EEWFittingResult::NotAllowed;
    if (Helmsman && Fittings[Index].Item && Fittings[Index].Item->FittingMountType == EEWShipMountType::Helm)
        return EEWFittingResult::Occupied;
    // A railing comes off only once the cannons in its places are out.
    if (Definition)
        for (const FEWShipMount& Child : Definition->Mounts)
            if (Child.ParentMount == MountId && GetFitting(Child.MountId)) return EEWFittingResult::RailingHoldsCannons;
    TGuardValue<bool> Guard(bChangingFittings, true);
    // A torn flag taken down is lost: wear is never undone (owner, October 17: no repair, only a new flag).
    const bool bTornFlag = Fittings[Index].Item && Fittings[Index].Item->FittingMountType == EEWShipMountType::Flag && Fittings[Index].Wear > 0.f;
    // The fitting stays on the ship unless the inventory accepts it.
    if (!bTornFlag && Character->GetInventoryComponent()->AddItem(Fittings[Index].Item, 1) != 1) return EEWFittingResult::InventoryFull;
    Fittings.RemoveAt(Index);
    RefreshFittingVisuals();
    ForceNetUpdate();
    return EEWFittingResult::Removed;
}

bool AEWShip::CanInteract_Implementation(AEWCharacter* Character) const
{
    if (bSinking || bChangingFittings || !CanModifyFittings(Character)) return false;
    if (Helmsman == Character) return true;  // Leave the helm.
    if (IsGunnerHere(Character)) return true;  // Leave the cannon.
    if (IsAimingAtAnchor(Character)) return true;
    if (IsAimingAtBucket(Character)) return IsAboard(Character) && WaterAboard > 0.f;
    if (IsAimingAtCargoHatch(Character)) return CanAccessCargo(Character);
    if (FindAimedBoardingPoint(Character) != INDEX_NONE) return !IsAboard(Character) && !Character->GetHelmShip() && !Character->IsOnLadder();
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition->FindMount(MountId);
    if (!Mount || !IsMountOpen(MountId)) return false;
    if (const UEWItemDefinition* Installed = GetFitting(MountId))
    {
        // An installed helm is taken and a cannon manned, not removed; removing them is a Builder's Plan action.
        if (Installed->FittingMountType == EEWShipMountType::Cannon)
            return !GetCannonGunner(MountId) && !Character->GetHelmShip() && !Character->GetGunShip() && !Character->bIsCrouched && !Character->IsProne();
        return Installed->FittingMountType != EEWShipMountType::Helm
            || (!Helmsman && !Character->GetHelmShip() && !Character->bIsCrouched && !Character->IsProne());
    }
    return FindCarriedFitting(Character, *Mount) != nullptr;
}

FText AEWShip::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    if (Character && Helmsman == Character)
    {
        FText Status = FText::GetEmpty();
        if (bSwamped) Status = NSLOCTEXT("Elitewake", "HelmSwamped", "  -  Swamped: too heavy to sail. Lighten the hold");
        else if (bOverloaded) Status = FText::Format(NSLOCTEXT("Elitewake", "HelmOverloaded", "  -  Overloaded: lighten the hold within {0} s"),
            FText::AsNumber(FMath::CeilToInt(OverloadSecondsLeft)));
        else if (bAnchored) Status = NSLOCTEXT("Elitewake", "HelmAnchored", "  -  Anchored");
        if (WaterAboard >= 1.f)
            Status = FText::Format(NSLOCTEXT("Elitewake", "HelmWater", "{0}  -  Taking water: {1} kg aboard"), Status,
                FText::AsNumber(FMath::RoundToInt(WaterAboard)));
        if (HullHealth >= 0.f && HullHealth < GetMaxHullHealth())
            Status = FText::Format(NSLOCTEXT("Elitewake", "HelmHull", "{0}  -  Hull {1}%"), Status,
                FText::AsNumber(FMath::RoundToInt(100.f * HullHealth / GetMaxHullHealth())));
        if (Definition && Definition->bPaddled)
            return FText::Format(NSLOCTEXT("Elitewake", "LeavePaddlesStatus", "Put down the paddles  (W/S stroke, A/D steer){0}"), Status);
        return FText::Format(NSLOCTEXT("Elitewake", "LeaveHelmStatus", "Leave the helm  (W/S sails, A/D rudder, Shift + A/D trim){0}"), Status);
    }
    if (IsGunnerHere(Character))
    {
        const FName Mount = Character->GetGunMount();
        const FText State = IsCannonLoaded(Mount) ? NSLOCTEXT("Elitewake", "CannonLoaded", "Loaded")
            : IsCannonLoading(Mount) ? NSLOCTEXT("Elitewake", "CannonLoading", "Loading...")
            : NSLOCTEXT("Elitewake", "CannonEmpty", "Empty: carry round shot to load it");
        if (const FEWShipMount* Port = Definition ? Definition->FindMount(Mount) : nullptr; Port && Port->bGunport)
        {
            const FText PortState = !IsGunportOpen(Mount) ? NSLOCTEXT("Elitewake", "PortShut", "Port shut: Up opens it")
                : GetGunportOpening(Mount) < .99f ? NSLOCTEXT("Elitewake", "PortOpening", "Running out...")
                : NSLOCTEXT("Elitewake", "PortOpen", "Port open: Down shuts it");
            return FText::Format(NSLOCTEXT("Elitewake", "LeaveCannonPort", "Leave the cannon  (mouse aims, Left Mouse fires)  -  {0}  -  {1}"), State, PortState);
        }
        return FText::Format(NSLOCTEXT("Elitewake", "LeaveCannon", "Leave the cannon  (mouse aims, Left Mouse fires)  -  {0}"), State);
    }
    if (IsAimingAtAnchor(Character))
        return bAnchored ? NSLOCTEXT("Elitewake", "RaiseAnchor", "Raise anchor") : NSLOCTEXT("Elitewake", "DropAnchor", "Drop anchor");
    if (IsAimingAtBucket(Character))
        return WaterAboard > 0.f ? FText::Format(NSLOCTEXT("Elitewake", "BailWater", "Bail water  ({0} kg aboard)"), FText::AsNumber(FMath::RoundToInt(WaterAboard)))
            : NSLOCTEXT("Elitewake", "BucketDry", "Bucket  (no water aboard)");
    if (IsAimingAtCargoHatch(Character)) return NSLOCTEXT("Elitewake", "OpenHold", "Open the hold");
    if (FindAimedBoardingPoint(Character) != INDEX_NONE)
        return IsAboard(Character) ? FText::GetEmpty() : NSLOCTEXT("Elitewake", "GrabLadder", "Climb the ladder");
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Mount) return FText::GetEmpty();
    if (const UEWItemDefinition* Installed = GetFitting(MountId))
        return Installed->FittingMountType == EEWShipMountType::Cannon
            ? (GetCannonGunner(MountId) ? FText::GetEmpty() : NSLOCTEXT("Elitewake", "ManCannon", "Man the cannon"))
            : Installed->FittingMountType == EEWShipMountType::Helm
            ? (Helmsman ? FText::GetEmpty() : Definition->bPaddled ? NSLOCTEXT("Elitewake", "TakePaddles", "Take up the paddles")
                : NSLOCTEXT("Elitewake", "TakeHelm", "Take the helm"))
            : FText::Format(NSLOCTEXT("Elitewake", "RemoveFitting", "Remove {0}"), Installed->DisplayName);
    if (const UEWItemDefinition* Carried = IsValid(Character) && Character->GetInventoryComponent() ? FindCarriedFitting(Character, *Mount) : nullptr)
        return FText::Format(NSLOCTEXT("Elitewake", "InstallFitting", "Install {0}"), Carried->DisplayName);
    return FText::Format(NSLOCTEXT("Elitewake", "EmptyMount", "Empty {0} mount"), MountTypeName(*Mount));
}

float AEWShip::GetHoldDurationFor_Implementation(AEWCharacter* Character) const
{
    if (IsAimingAtBucket(Character)) return BailHoldSeconds;
    return Definition && !Definition->CapstanMesh.IsNull() && IsAimingAtAnchor(Character) ? AnchorHoldSeconds : FittingHoldSeconds;
}

void AEWShip::HoldChanged_Implementation(AEWCharacter* Character, bool bHolding)
{
    if (!HasAuthority()) return;
    if (bHolding && Definition && !Definition->CapstanMesh.IsNull() && IsAimingAtAnchor(Character)) SetCapstanWorker(Character);
    else if (!bHolding && (!Character || CapstanWorker == Character)) SetCapstanWorker(nullptr);
}

void AEWShip::SetCapstanWorker(AEWCharacter* Worker)
{
    if (CapstanWorker == Worker) return;
    CapstanWorker = Worker;
    OnRep_CapstanWorker();
    ForceNetUpdate();
}

void AEWShip::OnRep_CapstanWorker()
{
    if (ShownCapstanWorker.Get() == CapstanWorker) return;
    if (AEWCharacter* Previous = ShownCapstanWorker.Get()) Previous->SetCapstanShip(nullptr);
    if (CapstanWorker) CapstanWorker->SetCapstanShip(this);
    ShownCapstanWorker = CapstanWorker;
}

bool AEWShip::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !Character || !Character->HasAuthority() || !CanInteract_Implementation(Character)
        || FEWInteractionTargeting::FindTarget(Character) != this) return false;
    if (Helmsman == Character) return LeaveHelm(Character);
    if (IsGunnerHere(Character)) return LeaveCannon(Character);
    if (IsAimingAtAnchor(Character)) return SetAnchored(Character, !bAnchored);
    if (IsAimingAtBucket(Character))
    {
        // One stroke of the bucket over the side.
        WaterAboard = FMath::Max(0.f, WaterAboard - BailPerStroke);
        ForceNetUpdate();
        return true;
    }
    if (IsAimingAtCargoHatch(Character))
    {
        // The server agrees the hold may be used; the owning client opens its screen.
        auto* PC = Cast<AEWPlayerController>(Character->GetController());
        if (!PC || !CanAccessCargo(Character)) return false;
        PC->ClientOpenContainer(this);
        return true;
    }
    if (const int32 Ladder = FindAimedBoardingPoint(Character); Ladder != INDEX_NONE) return StartClimb(Character, Ladder);
    const FName MountId = FindAimedMount(Character);
    const UEWItemDefinition* Installed = GetFitting(MountId);
    if (Installed && Installed->FittingMountType == EEWShipMountType::Helm) return TakeHelm(Character);
    if (Installed && Installed->FittingMountType == EEWShipMountType::Cannon) return ManCannon(Character, MountId);
    const EEWFittingResult Result = Installed ? RemoveFitting(Character, MountId) : InstallFitting(Character, MountId);
    return Result == EEWFittingResult::Installed || Result == EEWFittingResult::Removed;
}

// ---- Helm and sailing ----

namespace
{
    float SailWeight(EEWSailSize Size)
    {
        return Size == EEWSailSize::Large ? 3.f : Size == EEWSailSize::Medium ? 2.f : Size == EEWSailSize::Small ? 1.f : 0.f;
    }
}

const FEWShipMount* AEWShip::FindHelmMount() const
{
    return Definition ? Definition->Mounts.FindByPredicate([](const FEWShipMount& M) { return M.Type == EEWShipMountType::Helm; }) : nullptr;
}

FVector AEWShip::GetHelmSeatLocal(float CapsuleHalfHeight) const
{
    const FEWShipMount* Helm = FindHelmMount();
    const FVector Wheel = Helm ? Helm->Transform.GetLocation() : FVector::ZeroVector;
    const FVector Stand(Wheel.X - 60.f, Wheel.Y, 0.f);
    // Stand just aft of the wheel, on the deck under it: a modelled hull may raise the helm onto an aft deck.
    // The mount sits above its own deck, so look down from there.
    float Floor = GetDeckHeight();
    if (bModelledHull && HullVisual)
    {
        const FTransform& Ship = GetActorTransform();
        FHitResult Hit;
        if (HullVisual->LineTraceComponent(Hit, Ship.TransformPosition(FVector(Stand.X, Stand.Y, Wheel.Z)),
                Ship.TransformPosition(FVector(Stand.X, Stand.Y, Floor - 20.f)), FCollisionQueryParams(SCENE_QUERY_STAT(EWHelmSeat), true)))
            Floor = FMath::Max(Floor, Ship.InverseTransformPosition(Hit.ImpactPoint).Z);
    }
    return FVector(Stand.X, Stand.Y, Floor + CapsuleHalfHeight + 2.f);
}

bool AEWShip::GetCannonFrame(FName MountId, FTransform& Frame) const
{
    const UEWItemDefinition* Item = GetFitting(MountId);
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Item || !Mount || Item->FittingMountType != EEWShipMountType::Cannon) return false;
    Frame = Item->FittingTurningPivot * Item->FittingMeshTransform * GunMountTransform(*Mount);
    return true;
}

FTransform AEWShip::GunMountTransform(const FEWShipMount& Mount) const
{
    if (!Mount.bGunport) return Mount.Transform;
    // As built, the cannon stands run out at its port, the muzzle in the opening; shut, it is run in behind it.
    return FTransform(FVector(-CannonRunIn * (1.f - GetGunportOpening(Mount.MountId)), 0.f, 0.f)) * Mount.Transform;
}

bool AEWShip::IsGunportOpen(FName MountId) const
{
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    return !Mount || !Mount->bGunport || OpenGunports.Contains(MountId);
}

float AEWShip::GetGunportOpening(FName MountId) const
{
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    return !Mount || !Mount->bGunport ? 1.f : GunportOpening.FindRef(MountId);
}

bool AEWShip::SetGunportOpen(AEWCharacter* Character, bool bOpen)
{
    if (!HasAuthority() || !IsGunnerHere(Character)) return false;
    const FName MountId = Character->GetGunMount();
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Mount || !Mount->bGunport || OpenGunports.Contains(MountId) == bOpen) return false;
    if (bOpen) OpenGunports.Add(MountId);
    else OpenGunports.Remove(MountId);
    ForceNetUpdate();
    return true;
}

void AEWShip::ShowGunports(float DeltaSeconds)
{
    if (!Definition) return;
    const bool bDraw = GetNetMode() != NM_DedicatedServer;
    for (const FEWShipMount& Mount : Definition->Mounts)
    {
        if (!Mount.bGunport) continue;
        float& Opening = GunportOpening.FindOrAdd(Mount.MountId, 0.f);
        const float Was = Opening;
        Opening = FMath::FInterpConstantTo(Opening, OpenGunports.Contains(Mount.MountId) ? 1.f : 0.f, DeltaSeconds, GunportRate);
        TObjectPtr<UStaticMeshComponent>& Cover = CoverVisuals.FindOrAdd(Mount.MountId);
        if (bDraw && !Cover && !Mount.CoverMesh.IsNull())
        {
            Cover = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
                *FString::Printf(TEXT("Cover_%s"), *Mount.MountId.ToString())), RF_Transient);
            Cover->SetupAttachment(HullCollision);
            Cover->SetStaticMesh(Mount.CoverMesh.LoadSynchronous());
            Cover->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Cover->RegisterComponent();
            Cover->SetRelativeTransform(FTransform(Mount.CoverSlide * Opening) * Mount.CoverTransform * Mount.Transform);
        }
        if (Opening == Was) continue;
        // The cover slides aside along the hull and the cannon runs out behind it, together.
        if (Cover) Cover->SetRelativeTransform(FTransform(Mount.CoverSlide * Opening) * Mount.CoverTransform * Mount.Transform);
        if (const UEWItemDefinition* Item = GetFitting(Mount.MountId); Item && Item->FittingMountType == EEWShipMountType::Cannon)
        {
            if (const TObjectPtr<UStaticMeshComponent>* Visual = FittingVisuals.Find(Mount.MountId); Visual && *Visual)
                (*Visual)->SetRelativeTransform(Item->FittingMeshTransform * GunMountTransform(Mount));
            if (TurningRest.Contains(Mount.MountId))
                TurningRest.Add(Mount.MountId, Item->FittingTurningPivot * Item->FittingMeshTransform * GunMountTransform(Mount));
        }
    }
}

AEWCharacter* AEWShip::GetCannonGunner(FName MountId) const
{
    const FEWCannonState* Cannon = FindCannon(MountId);
    return Cannon ? Cannon->Gunner.Get() : nullptr;
}

bool AEWShip::IsCannonLoaded(FName MountId) const
{
    const FEWCannonState* Cannon = FindCannon(MountId);
    return Cannon && Cannon->bLoaded;
}

bool AEWShip::IsCannonLoading(FName MountId) const
{
    const FEWCannonState* Cannon = FindCannon(MountId);
    return Cannon && Cannon->bLoading;
}

FRotator AEWShip::GetCannonAim(FName MountId) const
{
    const FEWCannonState* Cannon = FindCannon(MountId);
    return Cannon ? FRotator(Cannon->Pitch, Cannon->Yaw, 0.f) : FRotator::ZeroRotator;
}

FTransform AEWShip::GetCannonMuzzleWorld(FName MountId) const
{
    FTransform Frame;
    if (!GetCannonFrame(MountId, Frame)) return GetActorTransform();
    const float Length = GetFitting(MountId)->CannonMuzzleLength;
    return FTransform(FVector(Length, 0, 0)) * FTransform(GetCannonAim(MountId)) * Frame * GetActorTransform();
}

FTransform AEWShip::GetGunnerSeatLocal(FName MountId, float HalfHeight) const
{
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Mount) return FTransform::Identity;
    // Behind the carriage, standing on the deck, facing out through the port.
    const FVector At = Mount->Transform.TransformPosition(FVector(-130.f, 0.f, -CannonMountHeight + HalfHeight + 2.f));
    return FTransform(FRotator(0.f, Mount->Transform.Rotator().Yaw, 0.f), At);
}

bool AEWShip::IsGunnerHere(const AEWCharacter* Character) const
{
    return Character && Character->GetGunShip() == this && GetCannonGunner(Character->GetGunMount()) == Character;
}

bool AEWShip::ManCannon(AEWCharacter* Character, FName MountId)
{
    FTransform Frame;
    if (!HasAuthority() || bChangingFittings || !CanModifyFittings(Character) || !GetCannonFrame(MountId, Frame)
        || GetCannonGunner(MountId) || Character->GetHelmShip() || Character->GetGunShip() || Character->IsOnLadder()
        || Character->bIsCrouched || Character->IsProne())
        return false;
    FEWCannonState* Cannon = FindCannon(MountId);
    if (!Cannon)
    {
        Cannon = &Cannons.AddDefaulted_GetRef();
        Cannon->MountId = MountId;
    }
    Cannon->Gunner = Character;
    Character->SetGunPost(this, MountId);
    ForceNetUpdate();
    return true;
}

bool AEWShip::LeaveCannon(AEWCharacter* Character, bool bForce)
{
    if (!HasAuthority() || !Character || Character->GetGunShip() != this) return false;
    const FName MountId = Character->GetGunMount();
    if (FEWCannonState* Cannon = FindCannon(MountId))
        if (Cannon->Gunner == Character) Cannon->Gunner = nullptr;
    Character->SetGunPost(nullptr, NAME_None);
    // Step back from the carriage onto the deck.
    if (!Character->IsActorBeingDestroyed())
    {
        const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
        const FTransform Seat = GetGunnerSeatLocal(MountId, Capsule ? Capsule->GetScaledCapsuleHalfHeight() : 90.f);
        Character->SetActorLocation(GetActorTransform().TransformPosition(Seat.GetLocation() + FVector(0, 0, 10.f)), false, nullptr, ETeleportType::TeleportPhysics);
    }
    ForceNetUpdate();
    return true;
}

bool AEWShip::AimCannon(AEWCharacter* Character, float Yaw, float Pitch)
{
    if (!HasAuthority() || !IsGunnerHere(Character) || !FMath::IsFinite(Yaw) || !FMath::IsFinite(Pitch)) return false;
    FEWCannonState* Cannon = FindCannon(Character->GetGunMount());
    Cannon->Yaw = FMath::Clamp(Yaw, -CannonTraverse, CannonTraverse);
    Cannon->Pitch = FMath::Clamp(Pitch, -CannonDepression, CannonElevation);
    return true;
}

bool AEWShip::FireCannon(AEWCharacter* Character)
{
    if (!HasAuthority() || !IsGunnerHere(Character)) return false;
    const FName MountId = Character->GetGunMount();
    FEWCannonState* Cannon = FindCannon(MountId);
    if (!Cannon->bLoaded) return false;
    // Not through a shut port, nor before the cannon is run out.
    if (GetGunportOpening(MountId) < .99f) return false;
    const FTransform Muzzle = GetCannonMuzzleWorld(MountId);
    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.Instigator = Character;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AEWCannonBall* Shot = GetWorld()->SpawnActor<AEWCannonBall>(Muzzle.GetLocation(), Muzzle.Rotator(), Params);
    if (!Shot) return false;
    // The shot keeps the ship's own way through the water.
    Shot->Launch(this, Character, Muzzle.GetRotation().GetForwardVector() * CannonMuzzleSpeed + GetActorForwardVector() * Speed);
    Cannon->bLoaded = false;
    ForceNetUpdate();
    return true;
}

void AEWShip::UpdateCannons(float DeltaSeconds)
{
    bool bChanged = false;
    for (FEWCannonState& Cannon : Cannons)
    {
        AEWCharacter* Gunner = Cannon.Gunner.Get();
        FTransform Frame;
        if (Cannon.Gunner && (!IsValid(Gunner) || Gunner->GetGunShip() != this || !CanModifyFittings(Gunner) || !GetCannonFrame(Cannon.MountId, Frame)))
        {
            if (IsValid(Gunner)) LeaveCannon(Gunner, true);
            Cannon.Gunner = nullptr;
            bChanged = true;
            continue;
        }
        if (!Gunner || Cannon.bLoaded) continue;
        if (Cannon.bLoading)
        {
            float& Left = CannonLoadLeft.FindOrAdd(Cannon.MountId);
            Left -= DeltaSeconds;
            if (Left <= 0.f) { Cannon.bLoading = false; Cannon.bLoaded = true; bChanged = true; }
            continue;
        }
        // Loading takes one round shot from the gunner and a while to ram home.
        UEWItemDefinition* Ammo = GetFitting(Cannon.MountId)->CannonAmmo.LoadSynchronous();
        UEWInventoryComponent* Carried = Gunner->GetInventoryComponent();
        if (Ammo && Carried && Carried->GetItemCount(Ammo) > 0 && Carried->RemoveItem(Ammo, 1) == 1)
        {
            Cannon.bLoading = true;
            CannonLoadLeft.Add(Cannon.MountId, CannonLoadSeconds);
            bChanged = true;
        }
    }
    if (bChanged) ForceNetUpdate();
}

float AEWShip::GetMaxHullHealth() const
{
    return Definition ? Definition->HullHealth : 1.f;
}

void AEWShip::TakeRoundShot(const FVector& Where, const FVector& Normal, AEWCharacter* Gunner)
{
    if (!HasAuthority()) return;
    if (HullHealth < 0.f && Definition) HullHealth = Definition->HullHealth;
    if (HullHealth <= 0.f) return;
    (void)Gunner;
    HullHealth = FMath::Max(0.f, HullHealth - RoundShotDamage);
    WearFlags(Where);
    FEWHullHole Hole;
    Hole.Local = GetActorTransform().InverseTransformPosition(Where);
    Hole.Normal = GetActorTransform().InverseTransformVectorNoScale(Normal.GetSafeNormal());
    Holes.Add(Hole);
    OnRep_Holes();
    ForceNetUpdate();
}

void AEWShip::OnRep_Holes()
{
    static UStaticMesh* HoleMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Elitewake/World/Ships/SM_ShotHole_v1.SM_ShotHole_v1"));
    if (!HoleMesh) return;
    // Each hole is drawn where it struck, flat on the planking and a hair proud of it.
    for (int32 i = HoleVisuals.Num(); i < FMath::Min(Holes.Num(), MaxShownHoles); ++i)
    {
        auto* Visual = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
            *FString::Printf(TEXT("ShotHole_%d"), i)), RF_Transient);
        Visual->SetupAttachment(HullCollision);
        Visual->SetStaticMesh(HoleMesh);
        Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        const FVector Normal = FVector(Holes[i].Normal).GetSafeNormal();
        Visual->SetRelativeLocationAndRotation(FVector(Holes[i].Local) + Normal * 1.5f, FRotationMatrix::MakeFromZ(Normal).Rotator());
        Visual->RegisterComponent();
        HoleVisuals.Add(Visual);
    }
}

bool AEWShip::IsValidHelmsman(const AEWCharacter* Character) const
{
    return Character && Helmsman == Character && Character->GetHelmShip() == this && CanModifyFittings(Character);
}

bool AEWShip::TakeHelm(AEWCharacter* Character)
{
    if (!HasAuthority() || bChangingFittings || Helmsman || !CanModifyFittings(Character)
        || Character->GetHelmShip() || Character->bIsCrouched || Character->IsProne() || !HasFittingOfType(EEWShipMountType::Helm))
        return false;
    Helmsman = Character;
    Rudder = 0.f;
    SailTrimDirection = 0;
    Character->SetHelmShip(this);
    ForceNetUpdate();
    return true;
}

bool AEWShip::LeaveHelm(AEWCharacter* Character, bool bForce)
{
    if (!HasAuthority() || !Character || Helmsman != Character) return false;
    const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const float HalfHeight = Capsule ? Capsule->GetScaledCapsuleHalfHeight() : 90.f;
    // Step off beside the wheel, or forward of it where the hull is too narrow beside it. Exits start a little
    // above the deck so boards and stringers proud of it never block them; the survivor settles onto them.
    const FVector Seat = GetHelmSeatLocal(HalfHeight) + FVector(0, 0, 10.f);
    FVector Exit = GetActorTransform().TransformPosition(Seat + FVector(0, 90.f, 0));
    if (Capsule)
    {
        FCollisionQueryParams Query(SCENE_QUERY_STAT(EWShipHelmExit), false, Character);
        bool bFree = false;
        for (const FVector& Offset : {FVector(0, 90.f, 0), FVector(0, -90.f, 0), FVector(150.f, 0, 0), FVector(150.f, 70.f, 0), FVector(150.f, -70.f, 0)})
        {
            const FVector Candidate = GetActorTransform().TransformPosition(Seat + Offset);
            if (!GetWorld()->OverlapBlockingTestByChannel(Candidate, FQuat::Identity, ECC_Pawn, Capsule->GetCollisionShape(), Query))
            {
                Exit = Candidate;
                bFree = true;
                break;
            }
        }
        if (!bFree && !bForce) return false;
    }
    Helmsman = nullptr;
    Rudder = 0.f;
    SailTrimDirection = 0;  // Sails stay as they were set and trimmed; the ship keeps sailing until someone changes them.
    Character->SetHelmShip(nullptr);
    if (!Character->IsActorBeingDestroyed()) Character->SetActorLocation(Exit, false, nullptr, ETeleportType::TeleportPhysics);
    ForceNetUpdate();
    return true;
}

bool AEWShip::SetRudder(AEWCharacter* Character, float NewRudder)
{
    if (!HasAuthority() || !IsValidHelmsman(Character) || !FMath::IsFinite(NewRudder) || FMath::Abs(NewRudder) > 1.f) return false;
    const auto* PC = Cast<AEWPlayerController>(Character->GetController());
    if (!PC || PC->GetInteractionComponent()->IsMenuBlocked()) return false;
    Rudder = NewRudder;
    return true;
}

bool AEWShip::StepSails(AEWCharacter* Character, int32 Direction)
{
    if (!HasAuthority() || !IsValidHelmsman(Character) || (Direction != 1 && Direction != -1)) return false;
    const auto* PC = Cast<AEWPlayerController>(Character->GetController());
    if (!PC || PC->GetInteractionComponent()->IsMenuBlocked()) return false;
    SailState = static_cast<EEWSailState>(FMath::Clamp(static_cast<int32>(SailState) + Direction, 0, 2));
    RefreshFittingVisuals();
    return true;
}

bool AEWShip::SetSailTrim(AEWCharacter* Character, int32 Direction)
{
    if (!HasAuthority() || !IsValidHelmsman(Character) || Direction < -1 || Direction > 1) return false;
    SailTrimDirection = static_cast<int8>(Direction);
    return true;
}

bool AEWShip::HasTrimmableSails() const
{
    return Definition && !Definition->bPaddled
        && Definition->Mounts.ContainsByPredicate([](const FEWShipMount& M) { return M.Type == EEWShipMountType::Sail; });
}

float AEWShip::GetBestSailAngle() const
{
    const UEWWindSubsystem* Wind = GetWorld() ? GetWorld()->GetSubsystem<UEWWindSubsystem>() : nullptr;
    if (!Wind) return 0.f;
    // Where the wind blows toward, relative to the bow: 0 running before it, 180 heading into it, positive when it
    // blows across toward starboard. The sails go out on the side it blows toward: square across at a run, half way
    // on a beam reach, along the centreline heading into it.
    const float Toward = FRotator::NormalizeAxis(Wind->GetWindYaw() - GetActorRotation().Yaw);
    return (Toward >= 0.f ? 1.f : -1.f) * FMath::Min(MaxSailAngle, 90.f - FMath::Abs(Toward) * .5f);
}

float AEWShip::GetTrimQuality() const
{
    const float Best = GetBestSailAngle();
    float Error = FMath::Abs(SailAngle - Best);
    // Running nearly dead before the wind, the sails draw on either side.
    if (FMath::Abs(Best) > MaxSailAngle - 10.f) Error = FMath::Min(Error, FMath::Abs(SailAngle + Best));
    // Sharp enough that trim matters: about 70% a quarter of the way out, nothing from 60 degrees off (tuning).
    return FMath::Cos(FMath::DegreesToRadians(FMath::Min(Error * 1.5f, 90.f)));
}

float AEWShip::GetWindFactor() const
{
    const UEWWindSubsystem* Wind = GetWorld() ? GetWorld()->GetSubsystem<UEWWindSubsystem>() : nullptr;
    if (!Wind) return 1.f;
    // Badly trimmed sails lose the heading's advantage, down to the least any sail gives, so a ship always makes
    // some headway.
    const float Heading = Wind->GetHeadingFactor(GetActorForwardVector());
    return UEWWindSubsystem::MinUpwindFactor + (Heading - UEWWindSubsystem::MinUpwindFactor) * GetTrimQuality();
}

float AEWShip::GetFittedSailFraction() const
{
    if (!Definition) return 0.f;
    float Capacity = 0.f, Fitted = 0.f;
    for (const FEWShipMount& Mount : Definition->Mounts)
    {
        if (Mount.Type != EEWShipMountType::Sail) continue;
        Capacity += SailWeight(Mount.SailSize);
        if (GetFitting(Mount.MountId)) Fitted += SailWeight(Mount.SailSize);
    }
    return Capacity > 0.f ? Fitted / Capacity : 0.f;
}

float AEWShip::ComputeTargetSpeed() const
{
    // At anchor the sails still drive her: the chain, not the anchor, stops her (StepSimulation).
    if (!Definition || bSwamped || SailState == EEWSailState::Furled) return 0.f;
    const float SailSet = SailState == EEWSailState::Full ? 1.f : .5f;
    // Paddlers set their own pace whatever the wind, with no sails to fill.
    if (Definition->bPaddled) return Definition->TopSpeed * SailSet * GetLoadSpeedFactor();
    return Definition->TopSpeed * SailingPace * SailSet * GetFittedSailFraction() * GetWindFactor() * GetLoadSpeedFactor();
}

void AEWShip::SimulateSailing(float DeltaSeconds)
{
    if (!HasAuthority() || !Definition || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    // Steps run from the last simulated pose, not the blended one shown since, unless something else moved the ship.
    if (bHasSimulatedPose && GetActorTransform().Equals(ShownPose, .01f)) SetActorTransform(SimulatedPose);
    else PreviousSimulatedPose = GetActorTransform();
    SimulationRemainder += FMath::Min(DeltaSeconds, MaxCatchUpSeconds);
    while (SimulationRemainder >= SimulationStep)
    {
        SimulationRemainder -= SimulationStep;
        PreviousSimulatedPose = GetActorTransform();
        StepSimulation(SimulationStep);
    }
    SimulatedPose = ShownPose = GetActorTransform();
    bHasSimulatedPose = true;
}

void AEWShip::ShowSimulatedPose()
{
    if (!bHasSimulatedPose) return;
    const float Alpha = FMath::Clamp(SimulationRemainder / SimulationStep, 0.f, 1.f);
    FTransform Shown;
    Shown.Blend(PreviousSimulatedPose, SimulatedPose, Alpha);
    SetActorTransform(Shown);
    ShownPose = GetActorTransform();
}

float AEWShip::CurrentTurnRate() const
{
    if (!Definition) return 0.f;
    return RudderAngle * Definition->TurnRate * FMath::Clamp(Speed / FullSteerageSpeed, MinSteerage, 1.f);
}

void AEWShip::PostNetReceiveLocationAndRotation()
{
    const FTransform Shown = GetActorTransform();
    Super::PostNetReceiveLocationAndRotation();
    NetPose = GetActorTransform();
    NetPoseTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
    // The first update, or one far from what is shown (a teleport), is taken at once; otherwise glide to it.
    if (!bHasNetPose || FVector::Dist(Shown.GetLocation(), NetPose.GetLocation()) > ClientSnapDistance)
    {
        bHasNetPose = true;
        return;
    }
    SetActorTransform(Shown);
}

void AEWShip::SmoothClientMotion(float DeltaSeconds)
{
    if (!bHasNetPose || !GetWorld()) return;
    // Carry the last update forward at the ship's replicated speed and turn, then ease toward that.
    const float Ahead = FMath::Clamp(float(GetWorld()->GetTimeSeconds() - NetPoseTime), 0.f, MaxClientPrediction);
    const FRotator Heading = NetPose.Rotator() + FRotator(0, CurrentTurnRate() * Ahead, 0);
    const FVector Along = FRotator(0, Heading.Yaw, 0).Vector();   // the swell's roll and pitch never move it
    FTransform Predicted(Heading, NetPose.GetLocation() + Along * Speed * Ahead, NetPose.GetScale3D());
    FTransform Shown;
    Shown.Blend(GetActorTransform(), Predicted, 1.f - FMath::Exp(-ClientCatchUpRate * DeltaSeconds));
    SetActorTransform(Shown);
}

float AEWShip::SwayScale() const
{
    return Definition ? FMath::Clamp(250.f / FMath::Max(Definition->HullExtent.Y, 1.f), .6f, 2.f) : 1.f;
}

void AEWShip::GetSwayAt(float Time, float& OutRoll, float& OutPitch, float& OutRise) const
{
    // Each ship rides its own swell (offset by its name), so a fleet never rocks in step.
    const float Phase = float(GetTypeHash(GetFName()) % 628) * .01f;
    const float Scale = SwayScale();
    OutRoll = Heel + SwellRoll * Scale * FMath::Sin(Time * .9f + Phase);
    OutPitch = SwellPitch * Scale * FMath::Sin(Time * .7f + Phase * 1.7f + 1.3f);
    OutRise = SwellRise * Scale * FMath::Sin(Time * .8f + Phase * .6f);
}

void AEWShip::StepSimulation(float Step)
{
    if (bSinking)
    {
        // Going down by the bow, slowly at first, then faster; gone once she is well under.
        SinkingFor += Step;
        Speed = 0.f;
        const float F = FMath::Clamp(SinkingFor / SinkSeconds, 0.f, 1.f);
        if (!bHasRestZ) { RestZ = GetActorLocation().Z; bHasRestZ = true; }
        FVector Here = GetActorLocation();
        Here.Z = RestZ - GetSettle() - SinkDepth * F * F;
        SetActorLocationAndRotation(Here, FRotator(-SinkPitch * FMath::Min(1.f, F * 2.f), GetActorRotation().Yaw, 6.f * F), false, nullptr, ETeleportType::None);
        if (F >= 1.f && HasAuthority()) Destroy();
        return;
    }
    if (SailTrimDirection != 0 && HasTrimmableSails())
        SailAngle = FMath::Clamp(SailAngle + SailTrimDirection * SailTrimRate * Step, -MaxSailAngle, MaxSailAngle);
    // The rudder swings over rather than snapping, so a ship eases into and out of a turn.
    RudderAngle = FMath::FInterpConstantTo(RudderAngle, Rudder, Step, RudderRate);
    const float Target = ComputeTargetSpeed();
    Speed = FMath::FInterpConstantTo(Speed, Target, Step, Target > Speed ? Acceleration : bAnchored ? AnchorDrag : Deceleration);
    if (bAnchored && ChainReach > 0.f)
    {
        // The chain's pull: free while there is slack, slowing her over the last of it, holding her once taut.
        const FVector Away = (GetHawseWorld() - AnchorBed).GetSafeNormal2D();
        const float Range = FVector::Dist2D(GetHawseWorld(), AnchorBed);
        const bool bOpening = FVector::DotProduct(GetActorForwardVector(), Away) > 0.f;
        const float Free = ChainReach * (1.f - ChainTensionShare);
        if (bOpening && Range > Free)
        {
            const float Tension = FMath::Clamp((Range - Free) / (ChainReach - Free), 0.f, 1.f);
            // Her speed allowed falls with the tension, down to a slow creep that takes up the last of the slack (tuning).
            Speed = FMath::Min(Speed, FMath::Max((Definition->TopSpeed > 0.f ? Definition->TopSpeed : 600.f) * .5f * (1.f - Tension), 30.f));
            // Once the chain is taut she rides to it, held, until the swell or the wind gives it slack again: the
            // swell rocking her bow must not let her creep.
            if (Tension >= 1.f || bChainTaut) Speed = 0.f;
        }
        if (!bChainTaut && Range >= ChainReach * .97f)
        {
            bChainTaut = true;
            ++ChainCatches;   // snubbed up: the clank, and her bow dips
        }
        else if (bChainTaut && Range < ChainReach * .9f) bChainTaut = false;
    }
    // The swell rocks every ship, moving or not; under sail it also leans to leeward, more with more wind in the
    // sails. Movement follows the heading alone, never the roll or pitch.
    if (!bHasRestZ) { RestZ = GetActorLocation().Z; bHasRestZ = true; }
    SwayTime += Step;
    const float SailSet = SailState == EEWSailState::Full ? 1.f : SailState == EEWSailState::Half ? .5f : 0.f;
    const float WantedHeel = HasTrimmableSails() && !bAnchored
        ? MaxHeel * SwayScale() * SailSet * GetFittedSailFraction() * GetWindFactor() * (SailAngle >= 0.f ? 1.f : -1.f) : 0.f;
    Heel = FMath::FInterpConstantTo(Heel, WantedHeel, Step, 2.f);
    float Roll, Pitch, Rise;
    GetSwayAt(SwayTime, Roll, Pitch, Rise);
    Pitch -= 1.5f * ChainJerk * FMath::Sin(ChainJerk * PI);   // the bow dips as the chain snubs her up
    const float Yaw = GetActorRotation().Yaw;
    // At anchor the rudder does nothing; otherwise a stopped ship may still turn to free itself.
    if (Speed <= 1.f && (bAnchored || FMath::IsNearlyZero(Rudder)))
    {
        Speed = FMath::Max(Speed, 0.f);
        FVector Here = GetActorLocation();
        Here.Z = RestZ + Rise - GetSettle();
        SetActorLocationAndRotation(Here, FRotator(Pitch, Yaw, Roll), false, nullptr, ETeleportType::None);
        return;
    }
    const FRotator Heading(0, Yaw + CurrentTurnRate() * Step, 0);
    FVector Next = GetActorLocation() + Heading.Vector() * Speed * Step;
    Next.Z = RestZ + Rise - GetSettle();
    const FRotator Rotation(Pitch, Heading.Yaw, Roll);
    // People never stop a ship: survivors on deck ride with it and swimmers are pushed aside.
    // Hulls, land and other world geometry still block the sweep.
    HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
    FHitResult Hit;
    SetActorLocationAndRotation(Next, Rotation, true, &Hit);
    if (!bModelledHull) HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    if (Hit.bBlockingHit)
    {
        if (!bAgainstObstacle)
            UE_LOG(LogEW, Log, TEXT("Ship %s stopped by %s (%s) at %s"), *GetName(), *GetNameSafe(Hit.GetActor()),
                *GetNameSafe(Hit.GetComponent()), *GetActorLocation().ToCompactString());
        bAgainstObstacle = true;
        Speed = 0.f;
    }
    else bAgainstObstacle = false;
}

void AEWShip::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ShowWake(DeltaSeconds);
    if (TurningVisuals.Num()) ShowTurning(DeltaSeconds);
    if (CapstanWorker && CapstanVisual)
    {
        // Heaving in turns it one way; letting the anchor go runs it the other, faster.
        CapstanYaw = FMath::Fmod(CapstanYaw + (bAnchored ? CapstanTurnRate : -1.5f * CapstanTurnRate) * DeltaSeconds, 360.f);
        CapstanVisual->SetRelativeRotation(FRotator(0, CapstanYaw, 0));
    }
    if (ShownSailAngle != SailAngle)
    {
        // Swing at the trim rate, a little faster to catch up on a client, never overshooting.
        ShownSailAngle = FMath::FInterpConstantTo(ShownSailAngle, SailAngle, DeltaSeconds, SailTrimRate * 1.5f);
        ShowSailTrim();
    }
    if (GetNetMode() != NM_DedicatedServer && SailLooks.Num()) ShowSailFill(DeltaSeconds);
    if (GetNetMode() != NM_DedicatedServer) ShowFlags(DeltaSeconds);
    ShowGunports(DeltaSeconds);
    ShowChain(DeltaSeconds);
    if (!HasAuthority())
    {
        SmoothClientMotion(DeltaSeconds);
        return;
    }
    if (Helmsman && !IsValidHelmsman(Helmsman))
    {
        if (IsValid(Helmsman)) LeaveHelm(Helmsman, true);
        else Helmsman = nullptr;
        Rudder = 0.f;
        SailTrimDirection = 0;
    }
    UpdateLeaks(DeltaSeconds);
    UpdateLoad(DeltaSeconds);
    UpdateCannons(DeltaSeconds);
    // An open menu centres the rudder and stops the sails swinging; they keep their setting and trim.
    if (Helmsman)
        if (const auto* PC = Cast<AEWPlayerController>(Helmsman->GetController()); !PC || PC->GetInteractionComponent()->IsMenuBlocked())
        {
            Rudder = 0.f;
            SailTrimDirection = 0;
        }
    SimulateSailing(DeltaSeconds);
    ShowSimulatedPose();
}

void AEWShip::EndPlay(const EEndPlayReason::Type Reason)
{
    if (HasAuthority() && IsValid(Helmsman)) LeaveHelm(Helmsman, true);
    Super::EndPlay(Reason);
}
