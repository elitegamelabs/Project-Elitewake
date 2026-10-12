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
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "Net/UnrealNetwork.h"
#include "WaterBodyActor.h"

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
    DOREPLIFETIME(AEWShip, bAnchored);
    DOREPLIFETIME(AEWShip, Load);
    DOREPLIFETIME(AEWShip, bOverloaded);
    DOREPLIFETIME(AEWShip, bSwamped);
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
    if (Definition)
    {
        const FString Problem = Definition->Validate();
        if (!Problem.IsEmpty()) UE_LOG(LogEW, Error, TEXT("Ship definition %s is invalid: %s"), *GetNameSafe(Definition), *Problem);
    }
    ApplyDefinition();
    RefreshFittingVisuals();
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
    for (UBoxComponent* Target : BoardingTargets) if (Target) Target->DestroyComponent();
    BoardingTargets.Reset();
    for (UStaticMeshComponent* Ladder : LadderVisuals) if (Ladder) Ladder->DestroyComponent();
    LadderVisuals.Reset();
    if (AnchorTarget) AnchorTarget->DestroyComponent();
    if (AnchorVisual) AnchorVisual->DestroyComponent();
    AnchorTarget = nullptr; AnchorVisual = nullptr;
    if (CargoHatchTarget) CargoHatchTarget->DestroyComponent();
    if (CargoHatchVisual) CargoHatchVisual->DestroyComponent();
    CargoHatchTarget = nullptr; CargoHatchVisual = nullptr;
    if (!Definition) return;
    if (HasAuthority() && Cargo) Cargo->SetMaxSlots(Definition->CargoSlots);
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

    for (int32 i = 0; i < Definition->BoardingPoints.Num(); ++i)
    {
        const FVector Point = Definition->BoardingPoints[i];
        // The ladder runs from below the waterline up the hull side, so it can be reached by a swimmer or from a dock.
        auto* Target = NewObject<UBoxComponent>(this, MakeUniqueObjectName(this, UBoxComponent::StaticClass(),
            *FString::Printf(TEXT("Ladder_%d"), i)), RF_Transient);
        Target->SetupAttachment(HullCollision);
        Target->SetRelativeLocation(Point);
        Target->SetBoxExtent(FVector(40, 25, 90));
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
        Ladder->SetRelativeTransform(FTransform(FRotator::ZeroRotator, Point, FVector(.6, .08, 1.8)));
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
        // The mount's own look wins: the ship's rig decides how a fitting sits on it.
        const bool bMountLook = !Mount->FittedMesh.IsNull();
        FTransform Local = bMountLook ? Mount->FittedMeshTransform : Fitting.Item->FittingMeshTransform;
        UStaticMesh* Mesh = bMountLook ? Mount->FittedMesh.LoadSynchronous() : Fitting.Item->FittingMesh.LoadSynchronous();
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
        Visual->SetRelativeTransform(Local * Mount->Transform);
    }
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
    float Total = Cargo ? Cargo->GetTotalWeight() : 0.f;
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
    ForceNetUpdate();
    return true;
}

bool AEWShip::ClimbAboard(AEWCharacter* Character, int32 BoardingIndex)
{
    if (!HasAuthority() || bChangingFittings || !CanModifyFittings(Character) || Character->GetHelmShip()
        || !Definition->BoardingPoints.IsValidIndex(BoardingIndex) || IsAboard(Character)) return false;
    const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const float HalfHeight = Capsule ? Capsule->GetScaledCapsuleHalfHeight() : 90.f;
    const FVector Point = Definition->BoardingPoints[BoardingIndex];
    // Step onto the deck about a metre inboard of the ladder, clear of the bulwark.
    const float Side = Point.Y >= 0.f ? 1.f : -1.f;
    const FVector Deck(Point.X, Side * FMath::Max(FMath::Abs(Point.Y) - 110.f, 0.f), Definition->GetDeckHeight() + HalfHeight + 2.f);
    const FVector Destination = GetActorTransform().TransformPosition(Deck);
    if (Capsule)
    {
        FCollisionQueryParams Query(SCENE_QUERY_STAT(EWShipBoarding), false, Character);
        if (GetWorld()->OverlapBlockingTestByChannel(Destination, FQuat::Identity, ECC_Pawn, Capsule->GetCollisionShape(), Query))
            return false;
    }
    Character->SetActorLocation(Destination, false, nullptr, ETeleportType::TeleportPhysics);
    if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement()) Movement->SetMovementMode(MOVE_Falling);
    Character->ForceNetUpdate();
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
    TGuardValue<bool> Guard(bChangingFittings, true);
    // The fitting stays on the ship unless the inventory accepts it.
    if (Character->GetInventoryComponent()->AddItem(Fittings[Index].Item, 1) != 1) return EEWFittingResult::InventoryFull;
    Fittings.RemoveAt(Index);
    RefreshFittingVisuals();
    ForceNetUpdate();
    return EEWFittingResult::Removed;
}

bool AEWShip::CanInteract_Implementation(AEWCharacter* Character) const
{
    if (bChangingFittings || !CanModifyFittings(Character)) return false;
    if (Helmsman == Character) return true;  // Leave the helm.
    if (IsAimingAtAnchor(Character)) return true;
    if (IsAimingAtCargoHatch(Character)) return CanAccessCargo(Character);
    if (FindAimedBoardingPoint(Character) != INDEX_NONE) return !IsAboard(Character) && !Character->GetHelmShip();
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition->FindMount(MountId);
    if (!Mount) return false;
    if (const UEWItemDefinition* Installed = GetFitting(MountId))
        // An installed helm is taken, not removed; removing it is a Builder's Plan action.
        return Installed->FittingMountType != EEWShipMountType::Helm
            || (!Helmsman && !Character->GetHelmShip() && !Character->bIsCrouched && !Character->IsProne());
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
        return FText::Format(NSLOCTEXT("Elitewake", "LeaveHelmStatus", "Leave the helm  (W/S sails, A/D rudder){0}"), Status);
    }
    if (IsAimingAtAnchor(Character))
        return bAnchored ? NSLOCTEXT("Elitewake", "RaiseAnchor", "Raise anchor") : NSLOCTEXT("Elitewake", "DropAnchor", "Drop anchor");
    if (IsAimingAtCargoHatch(Character)) return NSLOCTEXT("Elitewake", "OpenHold", "Open the hold");
    if (FindAimedBoardingPoint(Character) != INDEX_NONE)
        return IsAboard(Character) ? FText::GetEmpty() : NSLOCTEXT("Elitewake", "ClimbAboard", "Climb aboard");
    const FName MountId = FindAimedMount(Character);
    const FEWShipMount* Mount = Definition ? Definition->FindMount(MountId) : nullptr;
    if (!Mount) return FText::GetEmpty();
    if (const UEWItemDefinition* Installed = GetFitting(MountId))
        return Installed->FittingMountType == EEWShipMountType::Helm
            ? (Helmsman ? FText::GetEmpty() : NSLOCTEXT("Elitewake", "TakeHelm", "Take the helm"))
            : FText::Format(NSLOCTEXT("Elitewake", "RemoveFitting", "Remove {0}"), Installed->DisplayName);
    if (const UEWItemDefinition* Carried = IsValid(Character) && Character->GetInventoryComponent() ? FindCarriedFitting(Character, *Mount) : nullptr)
        return FText::Format(NSLOCTEXT("Elitewake", "InstallFitting", "Install {0}"), Carried->DisplayName);
    return FText::Format(NSLOCTEXT("Elitewake", "EmptyMount", "Empty {0} mount"), MountTypeName(*Mount));
}

bool AEWShip::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !Character || !Character->HasAuthority() || !CanInteract_Implementation(Character)
        || FEWInteractionTargeting::FindTarget(Character) != this) return false;
    if (Helmsman == Character) return LeaveHelm(Character);
    if (IsAimingAtAnchor(Character)) return SetAnchored(Character, !bAnchored);
    if (IsAimingAtCargoHatch(Character))
    {
        // The server agrees the hold may be used; the owning client opens its screen.
        auto* PC = Cast<AEWPlayerController>(Character->GetController());
        if (!PC || !CanAccessCargo(Character)) return false;
        PC->ClientOpenContainer(this);
        return true;
    }
    if (const int32 Ladder = FindAimedBoardingPoint(Character); Ladder != INDEX_NONE) return ClimbAboard(Character, Ladder);
    const FName MountId = FindAimedMount(Character);
    const UEWItemDefinition* Installed = GetFitting(MountId);
    if (Installed && Installed->FittingMountType == EEWShipMountType::Helm) return TakeHelm(Character);
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
    const float DeckTop = GetDeckHeight();
    // Stand just aft of the wheel, on the deck.
    return FVector(Wheel.X - 60.f, Wheel.Y, DeckTop + CapsuleHalfHeight + 2.f);
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
        for (const FVector& Offset : {FVector(0, 90.f, 0), FVector(0, -90.f, 0), FVector(150.f, 0, 0)})
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
    Rudder = 0.f;  // Sails stay as they were set; the ship keeps sailing until someone changes them.
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
    if (!Definition || bAnchored || bSwamped || SailState == EEWSailState::Furled) return 0.f;
    const float SailSet = SailState == EEWSailState::Full ? 1.f : .5f;
    const UEWWindSubsystem* Wind = GetWorld() ? GetWorld()->GetSubsystem<UEWWindSubsystem>() : nullptr;
    const float Heading = Wind ? Wind->GetHeadingFactor(GetActorForwardVector()) : 1.f;
    return Definition->TopSpeed * SailSet * GetFittedSailFraction() * Heading * GetLoadSpeedFactor();
}

void AEWShip::SimulateSailing(float DeltaSeconds)
{
    if (!HasAuthority() || !Definition || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    SimulationRemainder += FMath::Min(DeltaSeconds, MaxCatchUpSeconds);
    while (SimulationRemainder >= SimulationStep)
    {
        SimulationRemainder -= SimulationStep;
        StepSimulation(SimulationStep);
    }
}

void AEWShip::StepSimulation(float Step)
{
    const float Target = ComputeTargetSpeed();
    Speed = FMath::FInterpConstantTo(Speed, Target, Step, Target > Speed ? Acceleration : bAnchored ? AnchorDrag : Deceleration);
    // At anchor the rudder does nothing; otherwise a stopped ship may still turn to free itself.
    if (Speed <= 1.f && (bAnchored || FMath::IsNearlyZero(Rudder))) { Speed = FMath::Max(Speed, 0.f); return; }
    const float Steerage = FMath::Clamp(Speed / FullSteerageSpeed, MinSteerage, 1.f);
    const FRotator Rotation = GetActorRotation() + FRotator(0, Rudder * Definition->TurnRate * Steerage * Step, 0);
    // People never stop a ship: survivors on deck ride with it and swimmers are pushed aside.
    // Hulls, land and other world geometry still block the sweep.
    HullCollision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
    FHitResult Hit;
    SetActorLocationAndRotation(GetActorLocation() + Rotation.Vector() * Speed * Step, Rotation, true, &Hit);
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
    if (!HasAuthority()) return;
    if (Helmsman && !IsValidHelmsman(Helmsman))
    {
        if (IsValid(Helmsman)) LeaveHelm(Helmsman, true);
        else Helmsman = nullptr;
        Rudder = 0.f;
    }
    UpdateLoad(DeltaSeconds);
    // An open menu centres the rudder; the sails keep their setting.
    if (Helmsman)
        if (const auto* PC = Cast<AEWPlayerController>(Helmsman->GetController()); !PC || PC->GetInteractionComponent()->IsMenuBlocked())
            Rudder = 0.f;
    SimulateSailing(DeltaSeconds);
}

void AEWShip::EndPlay(const EEndPlayReason::Type Reason)
{
    if (HasAuthority() && IsValid(Helmsman)) LeaveHelm(Helmsman, true);
    Super::EndPlay(Reason);
}
