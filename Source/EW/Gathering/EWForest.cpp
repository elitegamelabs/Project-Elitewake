#include "EWForest.h"
#include "EWCharacter.h"
#include "EWHarvestTree.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWForest::AEWForest()
{
    bReplicates = true;
    SetReplicateMovement(false);
    bAlwaysRelevant = true;           // a stand spans much of an island; what is down must be known wherever the survivor is
    SetNetUpdateFrequency(2.f);
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 5.f;

    Trees = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Trees"));
    SetRootComponent(Trees);
    Trees->SetMobility(EComponentMobility::Movable);     // instances are hidden and regrown at run time
    Trees->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Trees->SetCollisionResponseToAllChannels(ECR_Ignore);
    Trees->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Trees->SetCanEverAffectNavigation(false);
    Trees->InstanceEndCullDistance = 200000;     // 2 km (tuning, measured against the minimum machine)
    Trees->InstanceStartCullDistance = 180000;

    Trunks = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Trunks"));
    Trunks->SetupAttachment(Trees);
    Trunks->SetMobility(EComponentMobility::Movable);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (Cylinder.Succeeded()) Trunks->SetStaticMesh(Cylinder.Object);
    Trunks->SetHiddenInGame(true);
    Trunks->SetVisibility(false);
    Trunks->SetCastShadow(false);
    Trunks->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Trunks->SetCollisionResponseToAllChannels(ECR_Block);
    Trunks->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);   // aiming goes to the tree itself
    Trunks->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
}

void AEWForest::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWForest, Removed);
}

void AEWForest::BeginPlay()
{
    Super::BeginPlay();
    CaptureAuthored();
    SyncHidden();
    SetActorTickEnabled(HasAuthority());
}

int32 AEWForest::GetTreeCount() const
{
    return Trees ? Trees->GetInstanceCount() : 0;
}

void AEWForest::CaptureAuthored()
{
    if (Authored.Num() || !Trees) return;
    const int32 Count = Trees->GetInstanceCount();
    Authored.SetNum(Count);
    for (int32 i = 0; i < Count; ++i) Trees->GetInstanceTransform(i, Authored[i], true);
}

FTransform AEWForest::GetTreeTransform(int32 Index) const
{
    if (Authored.IsValidIndex(Index)) return Authored[Index];
    FTransform Out;
    if (Trees && Index >= 0 && Index < Trees->GetInstanceCount()) Trees->GetInstanceTransform(Index, Out, true);
    return Out;
}

void AEWForest::ShowInstance(int32 Index, bool bShow)
{
    CaptureAuthored();
    if (!Authored.IsValidIndex(Index)) return;
    const FTransform& Tree = Authored[Index];
    // Hidden = shrunk to nothing where it stood (the instance keeps its index, so every index stays the same tree).
    FTransform Shown = Tree;
    if (!bShow) Shown.SetScale3D(FVector(KINDA_SMALL_NUMBER));
    Trees->UpdateInstanceTransform(Index, Shown, true, true, true);
    if (Trunks && Index < Trunks->GetInstanceCount())
    {
        FTransform Trunk;
        Trunks->GetInstanceTransform(Index, Trunk, true);
        if (bShow)
        {
            const FVector Scale = Tree.GetScale3D().GetAbs();
            const float Radius = TrunkRadius * FMath::Max(Scale.X, Scale.Y), Half = TrunkHalfHeight * Scale.Z;
            Trunk = FTransform(FQuat::Identity, Tree.GetLocation() + FVector(0, 0, Half), FVector(Radius / 50.f, Radius / 50.f, Half / 50.f));
        }
        else Trunk.SetScale3D(FVector(KINDA_SMALL_NUMBER));
        Trunks->UpdateInstanceTransform(Index, Trunk, true, true, true);
    }
    if (bShow) Hidden.Remove(Index); else Hidden.Add(Index);
}

void AEWForest::SyncHidden()
{
    const TSet<int32> Down(Removed);
    for (int32 Index : Down) if (!Hidden.Contains(Index)) ShowInstance(Index, false);
    for (int32 Index : TSet<int32>(Hidden)) if (!Down.Contains(Index)) ShowInstance(Index, true);
}

void AEWForest::OnRep_Removed()
{
    SyncHidden();
}

AEWHarvestTree* AEWForest::PromoteAimed(AEWCharacter* Survivor)
{
    if (!HasAuthority() || !IsValid(Survivor)) return nullptr;
    FVector Eye; FRotator View;
    Survivor->GetActorEyesViewPoint(Eye, View);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWForestAim), false, Survivor);
    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(Hit, Eye, Eye + View.Vector() * FEWInteractionTargeting::Range, ECC_Visibility, Query)
        || Hit.GetComponent() != Trees || Hit.Item == INDEX_NONE) return nullptr;
    return Promote(Hit.Item);
}

AEWHarvestTree* AEWForest::Promote(int32 Index)
{
    CaptureAuthored();
    if (!HasAuthority() || !Authored.IsValidIndex(Index) || Removed.Contains(Index) || !Trees->GetStaticMesh()) return nullptr;
    const FTransform& Tree = Authored[Index];
    const FVector Scale = Tree.GetScale3D().GetAbs();
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    Params.bDeferConstruction = true;
    AEWHarvestTree* Actor = GetWorld()->SpawnActor<AEWHarvestTree>(AEWHarvestTree::StaticClass(),
        FTransform(Tree.GetRotation(), Tree.GetLocation()), Params);
    if (!Actor) return nullptr;
    Actor->Mesh->SetStaticMesh(Trees->GetStaticMesh());
    Actor->Mesh->SetRelativeScale3D(Scale);
    for (int32 Slot = 0; Slot < Trees->GetNumMaterials(); ++Slot) Actor->Mesh->SetMaterial(Slot, Trees->GetMaterial(Slot));
    Actor->Wood = Wood; Actor->Thatch = Thatch;
    // A bigger tree holds more wood: girth squared times height, at scale 1 the model's base amount.
    const float Size = FMath::Max(Scale.X, Scale.Y) * FMath::Max(Scale.X, Scale.Y) * Scale.Z;
    Actor->WoodRemaining = FMath::Clamp(FMath::RoundToInt(BaseWood * Size), 3, 36);
    Actor->ThatchRemaining = FMath::Clamp(FMath::RoundToInt(BaseThatch * Size), 1, 12);
    Actor->BlockerRadius = TrunkRadius * FMath::Max(Scale.X, Scale.Y);
    Actor->BlockerHalfHeight = TrunkHalfHeight * Scale.Z;
    Actor->FinishSpawning(FTransform(Tree.GetRotation(), Tree.GetLocation()));
    Removed.Add(Index);
    RemovedAt.Add(Index, GetWorld()->GetTimeSeconds());
    ShowInstance(Index, false);
    ForceNetUpdate();
    return Actor;
}

bool AEWForest::PlaceIsClear(int32 Index) const
{
    // A tree does not grow back through a survivor, an animal, a log still lying there or anything built in its place.
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWForestRegrow), false, this);
    const FVector At = Authored[Index].GetLocation() + FVector(0, 0, 150.f);
    return !GetWorld()->OverlapAnyTestByChannel(At, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(120.f), Query);
}

void AEWForest::RegrowAllNow()
{
    for (auto& Entry : RemovedAt) Entry.Value = -1e9;
    NextRegrowCheck = 0.0;
    Tick(0.f);
}

void AEWForest::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority() || RemovedAt.Num() == 0) return;
    const double Now = GetWorld()->GetTimeSeconds();
    if (Now < NextRegrowCheck) return;
    NextRegrowCheck = Now + 5.0;
    TArray<int32> Grown;
    for (const auto& Entry : RemovedAt)
        if (Now - Entry.Value >= RegrowSeconds && PlaceIsClear(Entry.Key)) Grown.Add(Entry.Key);
    for (int32 Index : Grown)
    {
        RemovedAt.Remove(Index);
        Removed.Remove(Index);
        ShowInstance(Index, true);
    }
    if (Grown.Num()) ForceNetUpdate();
}
