#include "World/EWBuildComponent.h"
#include "EWCharacter.h"
#include "World/EWBuildPiece.h"
#include "World/EWBuildZones.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
    const TCHAR* const GhostMaterial = TEXT("/Game/Elitewake/UI/M_PlacementGhost_v1.M_PlacementGhost_v1");
    const FLinearColor Blue(.12f, .45f, 1.f), Red(1.f, .1f, .08f);
    constexpr float Half = AEWBuildPiece::HalfSize;
}

UEWBuildComponent::UEWBuildComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .03f;
    SetIsReplicatedByDefault(true);
}

AEWCharacter* UEWBuildComponent::GetSurvivor() const
{
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    return PC ? Cast<AEWCharacter>(PC->GetPawn()) : nullptr;
}

void UEWBuildComponent::BeginPlay()
{
    Super::BeginPlay();
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    if (!PC || !PC->IsLocalController() || GetNetMode() == NM_DedicatedServer) { SetComponentTickEnabled(false); return; }
    UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, GhostMaterial, nullptr, LOAD_Quiet | LOAD_NoWarn);
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (!Base || !Cube) { SetComponentTickEnabled(false); return; }
    Glow = UMaterialInstanceDynamic::Create(Base, this);
    FActorSpawnParameters Params;
    Params.ObjectFlags = RF_Transient;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    GhostActor = GetWorld()->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), FTransform::Identity, Params);
    if (!GhostActor) { SetComponentTickEnabled(false); return; }
    GhostActor->SetReplicates(false);
    UStaticMeshComponent* Mesh = GhostActor->GetStaticMeshComponent();
    Mesh->SetMobility(EComponentMobility::Movable);
    Mesh->SetStaticMesh(Cube);
    Mesh->SetMaterial(0, Glow);
    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Mesh->SetCastShadow(false);
    Mesh->SetVisibility(false);
}

void UEWBuildComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    if (GhostActor) GhostActor->Destroy();
    Super::EndPlay(Reason);
}

bool UEWBuildComponent::IsGhostShowing() const
{
    return GhostActor && GhostActor->GetStaticMeshComponent()->IsVisible();
}

void UEWBuildComponent::SetMode(EEWBuildMode NewMode)
{
    Mode = NewMode;
    AimedPiece = nullptr;
    bAimOk = false;
    AimReason.Reset();
    if (Mode == EEWBuildMode::Off && GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false);
    if (Mode == EEWBuildMode::Off && GEngine) GEngine->RemoveOnScreenDebugMessage(7701);
}

void UEWBuildComponent::ToggleBuildMode()
{
    const AEWCharacter* Survivor = GetSurvivor();
    if (Mode != EEWBuildMode::Off) { SetMode(EEWBuildMode::Off); return; }
    if (!Survivor || Survivor->GetHelmShip() || Survivor->GetGunShip() || Survivor->IsOnLadder()) return;
    SetMode(EEWBuildMode::Place);
}

void UEWBuildComponent::ToggleDemolish()
{
    if (Mode == EEWBuildMode::Place) SetMode(EEWBuildMode::Demolish);
    else if (Mode == EEWBuildMode::Demolish) SetMode(EEWBuildMode::Place);
}

void UEWBuildComponent::RotateStep(int32 Direction)
{
    YawDegrees = FMath::UnwindDegrees(YawDegrees + 90.f * (Direction >= 0 ? 1 : -1));
}

bool UEWBuildComponent::HandleKey(const FInputKeyEventArgs& Params)
{
    const bool bPressed = Params.Event == IE_Pressed;
    const FKey& Key = Params.Key;
    if (Key == EKeys::B || Key == EKeys::Gamepad_RightThumbstick)
    {
        if (bPressed) ToggleBuildMode();
        return Mode != EEWBuildMode::Off || bPressed;
    }
    if (Mode == EEWBuildMode::Off) return false;
    if (Key == EKeys::Escape) { if (bPressed) SetMode(EEWBuildMode::Off); return true; }
    if (Key == EKeys::Q || Key == EKeys::Gamepad_LeftShoulder) { if (bPressed) RotateStep(-1); return true; }
    if (Key == EKeys::E || Key == EKeys::Gamepad_RightShoulder) { if (bPressed) RotateStep(1); return true; }
    if (Key == EKeys::X || Key == EKeys::Gamepad_FaceButton_Right) { if (bPressed) ToggleDemolish(); return true; }
    if (Key == EKeys::LeftMouseButton || Key == EKeys::Gamepad_RightTrigger) { if (bPressed) Confirm(); return true; }
    return false;
}

bool UEWBuildComponent::PlacementAllowed(UWorld* World, const FVector& Location, float Yaw, float& OutTop, float& OutBottom, FString& Reason)
{
    Reason = UEWBuildZones::CheckFootprint(World, Location.X, Location.Y, Half, Half, Yaw);
    float Low, High;
    if (!UEWBuildZones::GetFootprintGround(World, Location.X, Location.Y, Half, Half, Yaw, Low, High))
    {
        if (Reason.IsEmpty()) Reason = TEXT("No ground here.");
        return false;
    }
    OutTop = High + AEWBuildPiece::TopAboveGround;
    OutBottom = Low - AEWBuildPiece::SinkBelowGround;
    return Reason.IsEmpty();
}

void UEWBuildComponent::UpdateAim()
{
    AimedPiece = nullptr;
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    const AEWCharacter* Survivor = GetSurvivor();
    UWorld* World = GetWorld();
    if (!PC || !Survivor || !World) { bAimOk = false; return; }
    FVector EyeLocation; FRotator EyeRotation;
    PC->GetPlayerViewPoint(EyeLocation, EyeRotation);
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildAim), false, Survivor);
    if (GhostActor) Params.AddIgnoredActor(GhostActor);
    const FVector End = EyeLocation + EyeRotation.Vector() * (Reach + 600.f);
    if (!World->LineTraceSingleByChannel(Hit, EyeLocation, End, ECC_Visibility, Params))
    {
        bAimOk = false;
        AimReason = TEXT("Look at the ground.");
        if (GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false);
        return;
    }
    if (Mode == EEWBuildMode::Demolish)
    {
        AimedPiece = Cast<AEWBuildPiece>(Hit.GetActor());
        bAimOk = AimedPiece && FVector::Dist(Survivor->GetActorLocation(), AimedPiece->GetActorLocation()) <= Reach + Half;
        AimReason = !AimedPiece ? TEXT("Look at a piece to remove it.") : bAimOk ? FString() : TEXT("Too far away.");
        if (AimedPiece)
        {
            const float Mid = AimedPiece->GetActorLocation().Z;
            const float Top = AimedPiece->GetTopZ();
            ShowGhost(AimedPiece->GetActorLocation(), AimedPiece->GetActorRotation().Yaw, Top + 5.f, Mid - (Top - Mid) - 5.f, false);
        }
        else if (GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false);
        return;
    }
    // Where the foundation would stand: on a grid, or edge to edge with the nearest piece if one is close.
    FVector Centre(FMath::GridSnap(Hit.ImpactPoint.X, SnapGrid), FMath::GridSnap(Hit.ImpactPoint.Y, SnapGrid), 0.f);
    float Yaw = YawDegrees;
    bool bSnapped = false;
    float Best = SnapPieceRange;
    for (TActorIterator<AEWBuildPiece> It(World); It; ++It)
    {
        const FRotator PieceRot = It->GetActorRotation();
        const FVector Forward = PieceRot.RotateVector(FVector::ForwardVector), Right = PieceRot.RotateVector(FVector::RightVector);
        const FVector Base = It->GetActorLocation();
        const FVector Steps[4] = {Forward, -Forward, Right, -Right};
        for (const FVector& Step : Steps)
        {
            const FVector Slot = Base + Step * (Half * 2.f);
            const float D = FVector::Dist2D(Slot, Hit.ImpactPoint);
            if (D < Best) { Best = D; bSnapped = true; Centre = FVector(Slot.X, Slot.Y, 0.f); Yaw = PieceRot.Yaw; }
        }
    }
    if (bSnapped) YawDegrees = Yaw;
    AimLocation = Centre;
    float Top = 0.f, Bottom = 0.f;
    FString Why;
    bAimOk = PlacementAllowed(World, Centre, Yaw, Top, Bottom, Why);
    if (bAimOk && FVector::Dist2D(Survivor->GetActorLocation(), Centre) > Reach) { bAimOk = false; Why = TEXT("Too far away."); }
    AimReason = Why;
    AimLocation.Z = (Top + Bottom) * .5f;
    ShowGhost(Centre, Yaw, Top, Bottom, bAimOk);
}

void UEWBuildComponent::ShowGhost(const FVector& Centre, float Yaw, float TopZ, float BottomZ, bool bOk)
{
    if (!GhostActor) return;
    UStaticMeshComponent* Mesh = GhostActor->GetStaticMeshComponent();
    const float Height = FMath::Max(TopZ - BottomZ, 5.f);
    Mesh->SetWorldScale3D(FVector(Half * 2.f / 100.f, Half * 2.f / 100.f, Height / 100.f));
    Mesh->SetWorldLocationAndRotation(FVector(Centre.X, Centre.Y, (TopZ + BottomZ) * .5f), FRotator(0.f, Yaw, 0.f));
    Glow->SetVectorParameterValue(TEXT("Colour"), bOk ? Blue : Red);
    Mesh->SetVisibility(true);
}

void UEWBuildComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    if (Mode == EEWBuildMode::Off) return;
    const AEWCharacter* Survivor = GetSurvivor();
    if (!Survivor || Survivor->GetHelmShip() || Survivor->GetGunShip() || Survivor->IsOnLadder()) { SetMode(EEWBuildMode::Off); return; }
    UpdateAim();
#if !UE_BUILD_SHIPPING
    if (GEngine)
    {
        const FString Line = FString::Printf(TEXT("BUILD MODE  %s   [%s]  Rotate: Q/E or LB/RB   %s: X or B button   Leave: B or right stick"),
            Mode == EEWBuildMode::Demolish ? TEXT("DEMOLISH") : TEXT("FOUNDATION"), bAimOk ? TEXT("OK") : *AimReason,
            Mode == EEWBuildMode::Demolish ? TEXT("Place") : TEXT("Demolish"));
        GEngine->AddOnScreenDebugMessage(7701, .2f, bAimOk ? FColor::Cyan : FColor::Orange, Line);
    }
#endif
}

void UEWBuildComponent::Confirm()
{
    if (Mode == EEWBuildMode::Place && bAimOk) ServerPlace(AimLocation, YawDegrees);
    else if (Mode == EEWBuildMode::Demolish && bAimOk && AimedPiece) ServerDemolish(AimedPiece);
}

void UEWBuildComponent::ServerPlace_Implementation(FVector Location, float InYawDegrees)
{
    const AEWCharacter* Survivor = GetSurvivor();
    UWorld* World = GetWorld();
    if (!Survivor || !World) return;
    float Top, Bottom;
    FString Why;
    // The server decides: reach, then the same zone and ground rules the ghost used.
    if (FVector::Dist2D(Survivor->GetActorLocation(), Location) > Reach + 300.f) return;
    if (!PlacementAllowed(World, Location, InYawDegrees, Top, Bottom, Why)) return;
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    if (AEWBuildPiece* Piece = World->SpawnActor<AEWBuildPiece>(AEWBuildPiece::StaticClass(),
        FTransform(FRotator(0.f, InYawDegrees, 0.f), FVector(Location.X, Location.Y, (Top + Bottom) * .5f)), Params))
        Piece->Configure(Top, Bottom);
}

void UEWBuildComponent::ServerDemolish_Implementation(AEWBuildPiece* Piece)
{
    const AEWCharacter* Survivor = GetSurvivor();
    if (!Piece || !Survivor) return;
    if (FVector::Dist(Survivor->GetActorLocation(), Piece->GetActorLocation()) > Reach + Half + 300.f) return;
    Piece->Destroy();
}
