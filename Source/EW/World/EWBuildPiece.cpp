#include "World/EWBuildPiece.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
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
    DOREPLIFETIME(AEWBuildPiece, PieceType);
    DOREPLIFETIME(AEWBuildPiece, Size);
    DOREPLIFETIME(AEWBuildPiece, MaterialIndex);
    DOREPLIFETIME(AEWBuildPiece, Base);
}

const TCHAR* AEWBuildPiece::TypeName(EEWBuildPieceType Type)
{
    switch (Type)
    {
    case EEWBuildPieceType::TopWall: return TEXT("Top wall");
    case EEWBuildPieceType::TopCorner: return TEXT("Top corner");
    case EEWBuildPieceType::HalfWall: return TEXT("Half wall");
    case EEWBuildPieceType::RightCeiling: return TEXT("Right ceiling");
    case EEWBuildPieceType::RightLowerCorner: return TEXT("Right lower corner");
    case EEWBuildPieceType::Roof: return TEXT("Roof");
    case EEWBuildPieceType::BottomSpiralStaircase: return TEXT("Bottom spiral staircase");
    case EEWBuildPieceType::BottomLeftCorner: return TEXT("Bottom left corner");
    case EEWBuildPieceType::LShapeStaircase: return TEXT("L-shape staircase");
    case EEWBuildPieceType::LeftUShapeStaircase: return TEXT("Left U-shaped staircase");
    case EEWBuildPieceType::LeftTopCorner: return TEXT("Left top corner");
    default: return TEXT("Foundation");
    }
}

const TCHAR* AEWBuildPiece::MaterialName(int32 Material)
{
    static const TCHAR* const Names[MaterialCount] = {TEXT("Thatch"), TEXT("Wood"), TEXT("Stone"), TEXT("Metal")};   // placeholder, TBD
    return Names[FMath::Clamp(Material, 0, MaterialCount - 1)];
}

FLinearColor AEWBuildPiece::MaterialTint(int32 Material)
{
    static const FLinearColor Tints[MaterialCount] = {{.55f, .45f, .15f, 1.f}, {.32f, .18f, .08f, 1.f}, {.35f, .35f, .37f, 1.f}, {.2f, .26f, .32f, 1.f}};
    return Tints[FMath::Clamp(Material, 0, MaterialCount - 1)];
}

void AEWBuildPiece::Spec(EEWBuildPieceType Type, FVector& Size, FVector& LocalOffset, float& Lift)
{
    constexpr float H = HalfSize, W = WallHeight, T = 20.f, P = 40.f;
    Lift = 0.f;
    switch (Type)
    {
    case EEWBuildPieceType::TopWall:            Size = {T, H * 2, W};       LocalOffset = {H - T * .5f, 0, 0}; break;
    case EEWBuildPieceType::HalfWall:           Size = {T, H * 2, W * .5f}; LocalOffset = {H - T * .5f, 0, 0}; break;
    case EEWBuildPieceType::TopCorner:          Size = {P, P, W};           LocalOffset = {H - P * .5f, H - P * .5f, 0}; break;
    case EEWBuildPieceType::RightLowerCorner:   Size = {P, P, W};           LocalOffset = {-H + P * .5f, H - P * .5f, 0}; break;
    case EEWBuildPieceType::BottomLeftCorner:   Size = {P, P, W};           LocalOffset = {-H + P * .5f, -H + P * .5f, 0}; break;
    case EEWBuildPieceType::LeftTopCorner:      Size = {P, P, W};           LocalOffset = {H - P * .5f, -H + P * .5f, 0}; break;
    case EEWBuildPieceType::RightCeiling:       Size = {H * 2, H * 2, T};   LocalOffset = {0, 0, 0}; Lift = W; break;
    case EEWBuildPieceType::Roof:               Size = {H * 2, H * 2, T * 3}; LocalOffset = {0, 0, 0}; Lift = W + T; break;
    case EEWBuildPieceType::BottomSpiralStaircase: Size = {H, H, W};        LocalOffset = {0, 0, 0}; break;
    case EEWBuildPieceType::LShapeStaircase:    Size = {H * 1.5f, H, W * .75f}; LocalOffset = {-H * .25f, -H * .5f, 0}; break;
    case EEWBuildPieceType::LeftUShapeStaircase: Size = {H * 2, H, W * .75f}; LocalOffset = {0, -H * .5f, 0}; break;
    default:                                    Size = {H * 2, H * 2, T};   LocalOffset = {0, 0, 0}; break;
    }
}

void AEWBuildPiece::AttachedTransform(const AEWBuildPiece* Base, EEWBuildPieceType Type, float Yaw, FVector& OutLocation, FVector& OutSize)
{
    FVector Offset; float Lift;
    Spec(Type, OutSize, Offset, Lift);
    // The slot is a fixed place on the foundation (top edge, right-lower corner, ...), so it follows the foundation's own facing, not the player's.
    const FVector Rotated = FRotator(0.f, Base->GetActorRotation().Yaw, 0.f).RotateVector(Offset);
    const FVector B = Base->GetActorLocation();
    OutLocation = FVector(B.X + Rotated.X, B.Y + Rotated.Y, Base->GetTopZ() + Lift + OutSize.Z * .5f);
}

void AEWBuildPiece::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyShape();
}

void AEWBuildPiece::Configure(float InTopZ, float InBottomZ)
{
    PieceType = EEWBuildPieceType::Foundation;
    TopZ = InTopZ;
    BottomZ = FMath::Min(InBottomZ, InTopZ - 5.f);
    ApplyShape();
}

void AEWBuildPiece::ConfigureAttached(EEWBuildPieceType InType, const FVector& InSize, int32 InMaterial, AEWBuildPiece* InBase)
{
    PieceType = InType;
    Size = InSize;
    MaterialIndex = InMaterial;
    Base = InBase;
    TopZ = GetActorLocation().Z + InSize.Z * .5f;
    BottomZ = GetActorLocation().Z - InSize.Z * .5f;
    ApplyShape();
}

void AEWBuildPiece::SetMaterialIndex(int32 InMaterial)
{
    MaterialIndex = FMath::Clamp(InMaterial, 0, MaterialCount - 1);
    ApplyShape();
}

void AEWBuildPiece::OnRep_Shape() { ApplyShape(); }

void AEWBuildPiece::ApplyShape()
{
    // The engine cube is 100 cm a side, centred: scale it to the piece, and for the foundation move it to the middle of its height.
    if (PieceType == EEWBuildPieceType::Foundation)
    {
        if (TopZ <= BottomZ) return;     // not configured yet (OnConstruction at spawn): leave the spawn transform alone
        const float Height = FMath::Max(TopZ - BottomZ, 5.f);
        Slab->SetWorldScale3D(FVector(HalfSize * 2.f / 100.f, HalfSize * 2.f / 100.f, Height / 100.f));
        FVector Location = GetActorLocation();
        Location.Z = (TopZ + BottomZ) * .5f;
        SetActorLocation(Location);
    }
    else if (!Size.IsZero())
    {
        Slab->SetWorldScale3D(Size / 100.f);
    }
    if (!Tint)
    {
        if (UMaterialInterface* Basic = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"), nullptr, LOAD_Quiet | LOAD_NoWarn))
            Tint = UMaterialInstanceDynamic::Create(Basic, this);
        if (Tint) Slab->SetMaterial(0, Tint);
    }
    if (Tint) Tint->SetVectorParameterValue(TEXT("Color"), MaterialTint(MaterialIndex));
}
