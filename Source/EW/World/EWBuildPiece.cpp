#include "World/EWBuildPiece.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWBuildPiece::AEWBuildPiece()
{
    bReplicates = true;
    SetReplicateMovement(false);
    PrimaryActorTick.bCanEverTick = false;
    Slab = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Slab"));
    SetRootComponent(Slab);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) Slab->SetStaticMesh(Cube.Object);
    Slab->SetCollisionProfileName(TEXT("BlockAll"));
    Slab->SetMobility(EComponentMobility::Movable);
}

void AEWBuildPiece::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWBuildPiece, TopZ);
    DOREPLIFETIME(AEWBuildPiece, BottomZ);
}

void AEWBuildPiece::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyShape();
}

void AEWBuildPiece::Configure(float InTopZ, float InBottomZ)
{
    TopZ = InTopZ;
    BottomZ = FMath::Min(InBottomZ, InTopZ - 5.f);
    ApplyShape();
}

void AEWBuildPiece::OnRep_Shape() { ApplyShape(); }

void AEWBuildPiece::ApplyShape()
{
    // The engine cube is 100 cm a side, centred: scale it to the footprint and to the slab's height, and move it to its middle.
    const float Height = FMath::Max(TopZ - BottomZ, 5.f);
    Slab->SetWorldScale3D(FVector(HalfSize * 2.f / 100.f, HalfSize * 2.f / 100.f, Height / 100.f));
    FVector Location = GetActorLocation();
    Location.Z = (TopZ + BottomZ) * .5f;
    SetActorLocation(Location);
}
