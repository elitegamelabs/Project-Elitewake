#include "World/EWBuildPiece.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWBuildPiece::AEWBuildPiece()
{
    bReplicates = true;
    SetReplicateMovement(false);
    PrimaryActorTick.bCanEverTick = false;
    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    Root->SetMobility(EComponentMobility::Movable);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    auto MakeBox = [&](const TCHAR* Name)
    {
        UStaticMeshComponent* Box = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Box->SetupAttachment(Root);
        if (Cube.Succeeded()) Box->SetStaticMesh(Cube.Object);
        Box->SetCollisionProfileName(TEXT("BlockAll"));
        Box->SetMobility(EComponentMobility::Movable);
        return Box;
    };
    Slab = MakeBox(TEXT("Slab"));
    Part1 = MakeBox(TEXT("Part1"));
    Part2 = MakeBox(TEXT("Part2"));
}

void AEWBuildPiece::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWBuildPiece, TopZ);
    DOREPLIFETIME(AEWBuildPiece, BottomZ);
    DOREPLIFETIME(AEWBuildPiece, PieceType);
    DOREPLIFETIME(AEWBuildPiece, Size);
    DOREPLIFETIME(AEWBuildPiece, MaterialIndex);
    DOREPLIFETIME(AEWBuildPiece, Design);
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

void AEWBuildPiece::StairSteps(EEWBuildPieceType Type, TArray<FStairStep>& Out)
{
    // Eight risers of 40 cm in a 400 cm cell (placeholder dimensions, tuning); x runs toward the cell's top edge, y to its right.
    // Each shape ends on the ceiling, which is the eighth step, so only seven blocks are listed.
    Out.Reset();
    if (Type == EEWBuildPieceType::BottomSpiralStaircase)
    {
        // A square winder round a central post: a 3 x 3 block of 100 cm squares, the ring of eight going round clockwise.
        const float Ring[8][2] = {{-150, -150}, {-150, -50}, {-150, 50}, {-50, 50}, {50, 50}, {50, -50}, {50, -150}, {-50, -150}};
        for (int32 I = 0; I < 7; ++I) Out.Add({Ring[I][0] - 50.f, Ring[I][0] + 50.f, Ring[I][1] - 50.f, Ring[I][1] + 50.f, 40.f * (I + 1)});
        Out.Add({-70.f, -30.f, -70.f, -30.f, StairRise - 20.f});      // the post
    }
    else if (Type == EEWBuildPieceType::LShapeStaircase)
    {
        // Up along the cell's low-y side, a square landing, then a turn to climb toward +y.
        for (int32 I = 0; I < 4; ++I) Out.Add({-200.f + 50.f * I, -150.f + 50.f * I, -200.f, 0.f, 40.f * (I + 1)});
        Out.Add({0.f, 200.f, -200.f, 0.f, 200.f});
        Out.Add({0.f, 200.f, 0.f, 50.f, 240.f});
        Out.Add({0.f, 200.f, 50.f, 100.f, 280.f});
    }
    else if (Type == EEWBuildPieceType::LeftUShapeStaircase)
    {
        // Up along one side, a wide landing, and back along the other side.
        for (int32 I = 0; I < 5; ++I) Out.Add({-200.f + 50.f * I, -150.f + 50.f * I, -200.f, 0.f, 40.f * (I + 1)});
        Out.Add({50.f, 200.f, -200.f, 200.f, 240.f});
        Out.Add({0.f, 50.f, 0.f, 200.f, 280.f});
    }
}

void AEWBuildPiece::AttachedTransform(const AEWBuildPiece* Base, EEWBuildPieceType Type, FVector& OutLocation, FVector& OutSize, FRotator& OutRotation)
{
    const FRotator BaseRotation(0.f, Base->GetActorRotation().Yaw, 0.f);
    const FVector B = Base->GetActorLocation();
    FVector Offset; float Lift;
    Spec(Type, OutSize, Offset, Lift);
    OutRotation = BaseRotation;
    if (Base->GetPieceType() == EEWBuildPieceType::TopWall)
    {
        // Stacked on a wall: straight above it, same facing.
        OutLocation = FVector(B.X, B.Y, B.Z + Base->GetPieceSize().Z * .5f + OutSize.Z * .5f);
        return;
    }
    if (IsStair(Type))
    {
        // The staircase fills the cell from its top up to the height of a ceiling's top, facing as the cell does.
        OutSize = FVector(HalfSize * 2.f, HalfSize * 2.f, StairRise);
        OutLocation = FVector(B.X, B.Y, Base->GetTopZ() + StairRise * .5f);
        return;
    }
    // The slot is a fixed place on the foundation (top edge, right-lower corner, ...), so it follows the foundation's own facing, not the player's.
    const FVector Rotated = BaseRotation.RotateVector(Offset);
    OutLocation = FVector(B.X + Rotated.X, B.Y + Rotated.Y, Base->GetTopZ() + Lift + OutSize.Z * .5f);
}

void AEWBuildPiece::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyShape();
}

void AEWBuildPiece::EndPlay(const EEndPlayReason::Type Reason)
{
    if (IsStair(PieceType) && Reason == EEndPlayReason::Destroyed) RefreshCeilingsOver();     // give the ceiling its cut-out back
    Super::EndPlay(Reason);
}

void AEWBuildPiece::Configure(float InTopZ, float InBottomZ)
{
    PieceType = EEWBuildPieceType::Foundation;
    TopZ = InTopZ;
    BottomZ = FMath::Min(InBottomZ, InTopZ - 5.f);
    ApplyShape();
}

void AEWBuildPiece::ConfigureAttached(EEWBuildPieceType InType, const FVector& InSize, int32 InMaterial, int32 InDesign, AEWBuildPiece* InBase)
{
    Design = IsWall(InType) ? FMath::Clamp(InDesign, 0, DesignCount - 1) : 0;
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

UStaticMeshComponent* AEWBuildPiece::ExtraBox(int32 Index)
{
    while (Extras.Num() <= Index)
    {
        UStaticMeshComponent* Box = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transient);
        Box->SetStaticMesh(Slab->GetStaticMesh());
        Box->SetMobility(EComponentMobility::Movable);
        Box->SetCollisionProfileName(TEXT("BlockAll"));
        Box->SetupAttachment(GetRootComponent());
        Box->RegisterComponent();
        Extras.Add(Box);
    }
    return Extras[Index];
}

void AEWBuildPiece::RefreshCeilingsOver()
{
    UWorld* World = GetWorld();
    if (!World || !Base) return;
    for (TActorIterator<AEWBuildPiece> It(World); It; ++It)
        if (It->PieceType == EEWBuildPieceType::RightCeiling && It->Base == Base) It->ApplyShape();
}

void AEWBuildPiece::ApplyShape()
{
    // The engine cube is 100 cm a side, centred: scale it to the piece. The foundation also moves to the middle of its height.
    Part1->SetVisibility(false);
    Part2->SetVisibility(false);
    Part1->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Part2->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    int32 ExtrasUsed = 0;
    // Put a box at Centre with Extent (both in the piece's frame, cm).
    auto Use = [](UStaticMeshComponent* Box, const FVector& Centre, const FVector& Extent)
    {
        Box->SetRelativeScale3D(Extent / 100.f);
        Box->SetRelativeLocation(Centre);
        Box->SetVisibility(true);
        Box->SetCollisionProfileName(TEXT("BlockAll"));
    };
    Slab->SetVisibility(true);
    Slab->SetCollisionProfileName(TEXT("BlockAll"));
    if (PieceType == EEWBuildPieceType::Foundation)
    {
        if (TopZ <= BottomZ) return;     // not configured yet (OnConstruction at spawn): leave the spawn transform alone
        const float Height = FMath::Max(TopZ - BottomZ, 5.f);
        Slab->SetRelativeScale3D(FVector(HalfSize * 2.f / 100.f, HalfSize * 2.f / 100.f, Height / 100.f));
        FVector Location = GetActorLocation();
        Location.Z = (TopZ + BottomZ) * .5f;
        SetActorLocation(Location);
    }
    else if (IsStair(PieceType) && !Size.IsZero())
    {
        // Real steps: a block per step, each up from the cell's top to the step's height.
        Slab->SetVisibility(false);
        Slab->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        TArray<FStairStep> Steps;
        StairSteps(PieceType, Steps);
        for (const FStairStep& S : Steps)
            Use(ExtraBox(ExtrasUsed++), FVector((S.X0 + S.X1) * .5f, (S.Y0 + S.Y1) * .5f, -Size.Z * .5f + S.Top * .5f), FVector(S.X1 - S.X0, S.Y1 - S.Y0, S.Top));
        RefreshCeilingsOver();
    }
    else if (PieceType == EEWBuildPieceType::RightCeiling && !Size.IsZero())
    {
        // Cut away where staircases on the same cell climb through (on a 50 cm grid); the rest is covered by a few boxes.
        constexpr int32 N = 8;
        constexpr float Cell = HalfSize * 2.f / N;
        bool Hole[N][N] = {};
        bool bAnyHole = false;
        if (Base)
            for (TActorIterator<AEWBuildPiece> It(GetWorld()); It; ++It)
            {
                if (!IsStair(It->PieceType) || It->Base != Base || It->IsActorBeingDestroyed()) continue;
                TArray<FStairStep> Steps;
                StairSteps(It->PieceType, Steps);
                for (const FStairStep& S : Steps)
                {
                    if (S.Top >= StairRise - 25.f) continue;      // the spiral's post goes up to the ceiling and does not cut it
                    for (int32 J = 0; J < N; ++J)
                        for (int32 I = 0; I < N; ++I)
                        {
                            const float X = -HalfSize + Cell * (I + .5f), Y = -HalfSize + Cell * (J + .5f);
                            if (X > S.X0 && X < S.X1 && Y > S.Y0 && Y < S.Y1) { Hole[J][I] = true; bAnyHole = true; }
                        }
                }
            }
        if (!bAnyHole)
        {
            Slab->SetRelativeScale3D(Size / 100.f);
            Slab->SetRelativeLocation(FVector::ZeroVector);
        }
        else
        {
            bool Done[N][N] = {};
            bool bFirst = true;
            for (int32 J = 0; J < N; ++J)
                for (int32 I = 0; I < N; ++I)
                {
                    if (Hole[J][I] || Done[J][I]) continue;
                    int32 I1 = I;
                    while (I1 + 1 < N && !Hole[J][I1 + 1] && !Done[J][I1 + 1]) ++I1;
                    int32 J1 = J;
                    for (bool bGrow = true; bGrow && J1 + 1 < N;)
                    {
                        for (int32 K = I; K <= I1; ++K) if (Hole[J1 + 1][K] || Done[J1 + 1][K]) bGrow = false;
                        if (bGrow) ++J1;
                    }
                    for (int32 Y = J; Y <= J1; ++Y) for (int32 X = I; X <= I1; ++X) Done[Y][X] = true;
                    const FVector Centre(-HalfSize + Cell * (I + I1 + 1) * .5f, -HalfSize + Cell * (J + J1 + 1) * .5f, 0.f);
                    const FVector Extent(Cell * (I1 - I + 1), Cell * (J1 - J + 1), Size.Z);
                    if (bFirst) { Use(Slab, Centre, Extent); bFirst = false; }
                    else Use(ExtraBox(ExtrasUsed++), Centre, Extent);
                }
            if (bFirst) { Slab->SetVisibility(false); Slab->SetCollisionEnabled(ECollisionEnabled::NoCollision); }
        }
    }
    else if (!Size.IsZero())
    {
        Slab->SetRelativeScale3D(Size / 100.f);
        Slab->SetRelativeLocation(FVector::ZeroVector);
        if (PieceType == EEWBuildPieceType::TopWall && Design == 1)
        {
            // Doorway: two jambs either side of the opening and a lintel over it (wall length runs along local Y).
            const float Jamb = (Size.Y - DoorWidth) * .5f, Over = Size.Z - DoorHeight;
            Slab->SetRelativeScale3D(FVector(Size.X, Jamb, Size.Z) / 100.f);
            Slab->SetRelativeLocation(FVector(0.f, -(DoorWidth + Jamb) * .5f, 0.f));
            Part1->SetRelativeScale3D(FVector(Size.X, Jamb, Size.Z) / 100.f);
            Part1->SetRelativeLocation(FVector(0.f, (DoorWidth + Jamb) * .5f, 0.f));
            Part2->SetRelativeScale3D(FVector(Size.X, DoorWidth, Over) / 100.f);
            Part2->SetRelativeLocation(FVector(0.f, 0.f, (Size.Z - Over) * .5f));
            for (UStaticMeshComponent* Part : {Part1.Get(), Part2.Get()})
            {
                Part->SetVisibility(true);
                Part->SetCollisionProfileName(TEXT("BlockAll"));
            }
        }
    }
    for (int32 I = ExtrasUsed; I < Extras.Num(); ++I)
    {
        Extras[I]->SetVisibility(false);
        Extras[I]->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    if (!Tint)
    {
        if (UMaterialInterface* Basic = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"), nullptr, LOAD_Quiet | LOAD_NoWarn))
            Tint = UMaterialInstanceDynamic::Create(Basic, this);
        if (Tint) { Slab->SetMaterial(0, Tint); Part1->SetMaterial(0, Tint); Part2->SetMaterial(0, Tint); }
    }
    if (Tint)
    {
        Tint->SetVectorParameterValue(TEXT("Color"), MaterialTint(MaterialIndex));
        for (UStaticMeshComponent* Box : Extras) if (Box) Box->SetMaterial(0, Tint);
    }
}
