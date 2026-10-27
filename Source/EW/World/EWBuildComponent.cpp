#include "World/EWBuildComponent.h"
#include "EWCharacter.h"
#include "World/EWBuildPiece.h"
#include "World/EWBuildZones.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Styling/AppStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SCanvas.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
    const TCHAR* const GhostMaterial = TEXT("/Game/Elitewake/UI/M_PlacementGhost_v1.M_PlacementGhost_v1");
    const FLinearColor Blue(.12f, .45f, 1.f), Red(1.f, .1f, .08f);
    constexpr float Half = AEWBuildPiece::HalfSize;
    constexpr float DialRadius = 215.f;
    constexpr float DialDeadZone = .35f;

    // Clockwise from the top, the owner's list.
    EEWBuildPieceType SlotType(int32 Slot) { return static_cast<EEWBuildPieceType>(FMath::Clamp(Slot, 0, UEWBuildComponent::SlotCount - 1)); }
}

UEWBuildComponent::UEWBuildComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.f;
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
    ShowDial(false);
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
    AimBase = nullptr;
    bAimOk = false;
    AimReason.Reset();
    if (Mode == EEWBuildMode::Off)
    {
        ShowDial(false);
        if (GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false);
        if (GEngine) GEngine->RemoveOnScreenDebugMessage(7701);
    }
    else if (Mode == EEWBuildMode::Demolish) ShowDial(false);
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

void UEWBuildComponent::CycleMaterial(int32 Direction)
{
    MaterialIndex = (MaterialIndex + (Direction >= 0 ? 1 : -1) + AEWBuildPiece::MaterialCount) % AEWBuildPiece::MaterialCount;
}

void UEWBuildComponent::StepSlot(int32 Direction)
{
    const int32 Now = static_cast<int32>(SelectedType);
    SelectedType = SlotType((Now + (Direction >= 0 ? 1 : -1) + SlotCount) % SlotCount);
    HoveredSlot = static_cast<int32>(SelectedType);
}

void UEWBuildComponent::SelectSlot(int32 Slot)
{
    SelectedType = SlotType(Slot);
    HoveredSlot = static_cast<int32>(SelectedType);
    ShowDial(false);
}

void UEWBuildComponent::ToggleDial()
{
    if (Mode != EEWBuildMode::Place) return;
    ShowDial(!bDialOpen);
}

void UEWBuildComponent::SetDialPointer(float X, float Y)
{
    DialPointer = FVector2D(X, Y).GetClampedToMaxSize(1.f);
    if (DialPointer.Size() < DialDeadZone) return;
    float Degrees = FMath::RadiansToDegrees(FMath::Atan2(DialPointer.X, DialPointer.Y));
    if (Degrees < 0.f) Degrees += 360.f;
    HoveredSlot = FMath::RoundToInt(Degrees / (360.f / SlotCount)) % SlotCount;
}

void UEWBuildComponent::ShowDial(bool bShow)
{
    APlayerController* PC = Cast<APlayerController>(GetOwner());
    if (bShow == bDialOpen) return;
    bDialOpen = bShow;
    if (bLookLocked != bShow && PC)
    {
        PC->SetIgnoreLookInput(bShow);
        bLookLocked = bShow;
    }
    if (!GEngine || !GEngine->GameViewport || !PC || !PC->IsLocalController()) return;
    if (!bShow)
    {
        if (DialWidget.IsValid()) GEngine->GameViewport->RemoveViewportWidgetContent(DialWidget.ToSharedRef());
        DialWidget.Reset();
        return;
    }
    DialPointer = FVector2D::ZeroVector;
    HoveredSlot = static_cast<int32>(SelectedType);
    const FSlateBrush* White = FAppStyle::GetBrush("WhiteBrush");
    TSharedRef<SCanvas> Canvas = SNew(SCanvas);
    const FVector2D Middle(420.f, 290.f);
    for (int32 Slot = 0; Slot < SlotCount; ++Slot)
    {
        const float A = FMath::DegreesToRadians(Slot * (360.f / SlotCount));
        const FVector2D At = Middle + FVector2D(FMath::Sin(A), -FMath::Cos(A)) * FVector2D(DialRadius * 1.9f, DialRadius) - FVector2D(75.f, 18.f);
        const FText Label = FText::FromString(AEWBuildPiece::TypeName(SlotType(Slot)));
        Canvas->AddSlot().Position(At).Size(FVector2D(150.f, 36.f))
        [
            SNew(SBorder).BorderImage(White).Padding(4.f)
            .BorderBackgroundColor_Lambda([this, Slot]() { return Slot == HoveredSlot ? FLinearColor(1.f, .75f, .15f, .95f) : FLinearColor(.02f, .03f, .05f, .8f); })
            [
                SNew(STextBlock).Text(Label).Justification(ETextJustify::Center).AutoWrapText(true)
                .ColorAndOpacity_Lambda([this, Slot]() { return Slot == HoveredSlot ? FSlateColor(FLinearColor::Black) : FSlateColor(FLinearColor::White); })
            ]
        ];
    }
    Canvas->AddSlot().Position(Middle - FVector2D(110.f, 22.f)).Size(FVector2D(220.f, 44.f))
    [
        SNew(STextBlock).Justification(ETextJustify::Center).ColorAndOpacity(FLinearColor::White)
        .Text_Lambda([this]()
        {
            return FText::FromString(FString::Printf(TEXT("%s\n%s (LB / RB)"), AEWBuildPiece::TypeName(SlotType(HoveredSlot)), AEWBuildPiece::MaterialName(MaterialIndex)));
        })
    ];
    Canvas->AddSlot()
    .Position(TAttribute<FVector2D>::CreateLambda([this, Middle]() { return Middle + FVector2D(DialPointer.X, -DialPointer.Y) * FVector2D(DialRadius * 1.9f, DialRadius) - FVector2D(6.f, 6.f); }))
    .Size(FVector2D(12.f, 12.f))
    [
        SNew(SBorder).BorderImage(White).BorderBackgroundColor(FLinearColor(1.f, .2f, .2f, 1.f))
    ];
    DialWidget = SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Center)
    [
        SNew(SBox).WidthOverride(840.f).HeightOverride(580.f)[Canvas]
    ];
    GEngine->GameViewport->AddViewportWidgetContent(DialWidget.ToSharedRef(), 60);
}

void UEWBuildComponent::UpdateDial(float DeltaSeconds)
{
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    if (!PC) return;
    FVector2D Stick(PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX) + PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX),
                    PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY) + PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY));
    float DX = 0.f, DY = 0.f;
    PC->GetInputMouseDelta(DX, DY);
    if (Stick.Size() > .2f) SetDialPointer(Stick.X, Stick.Y);
    else if (DX != 0.f || DY != 0.f) SetDialPointer(DialPointer.X + DX * .03f, DialPointer.Y + DY * .03f);
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
    if (Key == EKeys::Escape)
    {
        if (bPressed) { if (bDialOpen) ShowDial(false); else SetMode(EEWBuildMode::Off); }
        return true;
    }
    if (Key == EKeys::Tab || Key == EKeys::Gamepad_FaceButton_Top) { if (bPressed) ToggleDial(); return true; }
    if (Key == EKeys::Q || Key == EKeys::Gamepad_DPad_Left) { if (bPressed) RotateStep(-1); return true; }
    if (Key == EKeys::E || Key == EKeys::Gamepad_DPad_Right) { if (bPressed) RotateStep(1); return true; }
    if (Key == EKeys::Z || Key == EKeys::Gamepad_LeftShoulder) { if (bPressed) CycleMaterial(-1); return true; }
    if (Key == EKeys::C || Key == EKeys::Gamepad_RightShoulder) { if (bPressed) CycleMaterial(1); return true; }
    if (Key == EKeys::X || Key == EKeys::Gamepad_FaceButton_Right) { if (bPressed) ToggleDemolish(); return true; }
    if (Key == EKeys::MouseScrollUp || Key == EKeys::MouseScrollDown)
    {
        if (bPressed && Mode == EEWBuildMode::Place && !bDialOpen) StepSlot(Key == EKeys::MouseScrollUp ? 1 : -1);
        return true;
    }
    if (Key == EKeys::LeftMouseButton || Key == EKeys::Gamepad_RightTrigger || Key == EKeys::Gamepad_FaceButton_Bottom)
    {
        if (bPressed) Confirm();
        return true;
    }
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

bool UEWBuildComponent::AttachAllowed(UWorld* World, AEWBuildPiece* Base, EEWBuildPieceType Type, float Yaw, FVector& OutLocation, FVector& OutSize, FString& Reason)
{
    Reason.Reset();
    // A "cell" is a foundation or a ceiling: pieces stand on the top of one, and every chain of cells ends on a foundation
    // (a ceiling's Base is the cell under it), so you may build off a ceiling as long as everything below stands on a foundation.
    const bool bCell = Base && (Base->GetPieceType() == EEWBuildPieceType::Foundation || Base->GetPieceType() == EEWBuildPieceType::RightCeiling);
    if (!bCell) { Reason = TEXT("Needs a foundation (or a ceiling on one) to attach to."); return false; }
    AEWBuildPiece::AttachedTransform(Base, Type, Yaw, OutLocation, OutSize);
    const bool bPillar = Type == EEWBuildPieceType::TopCorner || Type == EEWBuildPieceType::RightLowerCorner
        || Type == EEWBuildPieceType::BottomLeftCorner || Type == EEWBuildPieceType::LeftTopCorner;
    const bool bRoofing = Type == EEWBuildPieceType::RightCeiling || Type == EEWBuildPieceType::Roof;
    bool bWallOnCell = false, bWallBesidePillar = false;
    for (TActorIterator<AEWBuildPiece> It(World); It; ++It)
    {
        if (*It == Base) continue;
        if (It->GetPieceType() == Type && FVector::Dist(It->GetActorLocation(), OutLocation) < 10.f)
        {
            Reason = TEXT("Already built here.");
            return false;
        }
        if (It->GetBase() != Base) continue;
        const bool bWall = It->GetPieceType() == EEWBuildPieceType::TopWall || It->GetPieceType() == EEWBuildPieceType::HalfWall;
        if (It->GetPieceType() == EEWBuildPieceType::TopWall) bWallOnCell = true;
        if (bWall && FVector::Dist2D(It->GetActorLocation(), OutLocation) < 250.f) bWallBesidePillar = true;
    }
    if (bPillar && !bWallBesidePillar) { Reason = TEXT("A corner goes where walls meet: build a wall on this edge first."); return false; }
    if (bRoofing && !bWallOnCell) { Reason = TEXT("Needs a wall under it to rest on."); return false; }
    return true;
}

void UEWBuildComponent::UpdateAim()
{
    AimedPiece = nullptr;
    AimBase = nullptr;
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
            ShowGhost(AimedPiece->GetActorLocation(), AimedPiece->GetActorRotation().Yaw, AimedPiece->Slab->GetComponentScale() * 100.f + FVector(10.f), false);
        else if (GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false);
        return;
    }
    if (SelectedType != EEWBuildPieceType::Foundation)
    {
        // Attached pieces: the foundation looked at (or the one under the piece looked at, or the nearest to where the aim lands).
        AEWBuildPiece* Base = Cast<AEWBuildPiece>(Hit.GetActor());
        if (Base && Base->GetPieceType() != EEWBuildPieceType::Foundation && Base->GetPieceType() != EEWBuildPieceType::RightCeiling) Base = Base->GetBase();
        if (!Base)
        {
            float Best = Half * 1.5f;
            for (TActorIterator<AEWBuildPiece> It(World); It; ++It)
            {
                const float D = FVector::Dist2D(It->GetActorLocation(), Hit.ImpactPoint);
                if (It->GetPieceType() == EEWBuildPieceType::Foundation && D < Best) { Best = D; Base = *It; }
            }
        }
        AimBase = Base;
        FVector Location, Size;
        FString Why;
        bAimOk = AttachAllowed(World, Base, SelectedType, YawDegrees, Location, Size, Why);
        if (bAimOk && FVector::Dist2D(Survivor->GetActorLocation(), Location) > Reach) { bAimOk = false; Why = TEXT("Too far away."); }
        AimReason = Why;
        if (!Base) { if (GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false); return; }
        AimLocation = Location;
        ShowGhost(Location, Base->GetActorRotation().Yaw, Size, bAimOk);
        return;
    }
    // Where the foundation would stand: on a grid, or edge to edge with the nearest piece if one is close.
    FVector Centre(FMath::GridSnap(Hit.ImpactPoint.X, SnapGrid), FMath::GridSnap(Hit.ImpactPoint.Y, SnapGrid), 0.f);
    float Yaw = YawDegrees;
    bool bSnapped = false;
    float Best = SnapPieceRange;
    for (TActorIterator<AEWBuildPiece> It(World); It; ++It)
    {
        if (It->GetPieceType() != EEWBuildPieceType::Foundation) continue;
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
    ShowGhost(FVector(Centre.X, Centre.Y, (Top + Bottom) * .5f), Yaw, FVector(Half * 2.f, Half * 2.f, FMath::Max(Top - Bottom, 5.f)), bAimOk);
}

void UEWBuildComponent::ShowGhost(const FVector& Centre, float Yaw, const FVector& Size, bool bOk)
{
    if (!GhostActor) return;
    UStaticMeshComponent* Mesh = GhostActor->GetStaticMeshComponent();
    Mesh->SetWorldScale3D(Size / 100.f);
    Mesh->SetWorldLocationAndRotation(Centre, FRotator(0.f, Yaw, 0.f));
    Glow->SetVectorParameterValue(TEXT("Colour"), bOk ? Blue : Red);
    Mesh->SetVisibility(true);
}

void UEWBuildComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    if (Mode == EEWBuildMode::Off) return;
    const AEWCharacter* Survivor = GetSurvivor();
    if (!Survivor || Survivor->GetHelmShip() || Survivor->GetGunShip() || Survivor->IsOnLadder()) { SetMode(EEWBuildMode::Off); return; }
    if (bDialOpen) UpdateDial(DeltaSeconds);
    else UpdateAim();
#if !UE_BUILD_SHIPPING
    if (GEngine)
    {
        const FString Line = bDialOpen
            ? FString::Printf(TEXT("BUILD MODE  PIECE DIAL  point at a piece: mouse or either stick   Pick: left mouse / A / RT   Close: Tab / Y / Esc"))
            : FString::Printf(TEXT("BUILD MODE  %s [%s]  [%s]  Rotate: Q/E or d-pad   Material: Z/C or LB/RB   Dial: Tab or Y   %s: X or B button   Leave: B or right stick"),
                Mode == EEWBuildMode::Demolish ? TEXT("DEMOLISH") : AEWBuildPiece::TypeName(SelectedType), AEWBuildPiece::MaterialName(MaterialIndex),
                bAimOk ? TEXT("OK") : *AimReason, Mode == EEWBuildMode::Demolish ? TEXT("Place") : TEXT("Demolish"));
        GEngine->AddOnScreenDebugMessage(7701, .2f, bAimOk || bDialOpen ? FColor::Cyan : FColor::Orange, Line);
    }
#endif
}

void UEWBuildComponent::Confirm()
{
    if (bDialOpen) { SelectSlot(HoveredSlot); return; }
    if (Mode == EEWBuildMode::Place && bAimOk) ServerPlace(SelectedType, AimLocation, YawDegrees, MaterialIndex, AimBase);
    else if (Mode == EEWBuildMode::Demolish && bAimOk && AimedPiece) ServerDemolish(AimedPiece);
}

void UEWBuildComponent::ServerPlace_Implementation(EEWBuildPieceType Type, FVector Location, float InYawDegrees, int32 Material, AEWBuildPiece* BasePiece)
{
    const AEWCharacter* Survivor = GetSurvivor();
    UWorld* World = GetWorld();
    if (!Survivor || !World) return;
    Material = FMath::Clamp(Material, 0, AEWBuildPiece::MaterialCount - 1);
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    // The server decides: reach, then the same rules the ghost used.
    if (Type == EEWBuildPieceType::Foundation)
    {
        float Top, Bottom;
        FString Why;
        if (FVector::Dist2D(Survivor->GetActorLocation(), Location) > Reach + 300.f) return;
        if (!PlacementAllowed(World, Location, InYawDegrees, Top, Bottom, Why)) return;
        if (AEWBuildPiece* Piece = World->SpawnActor<AEWBuildPiece>(AEWBuildPiece::StaticClass(),
            FTransform(FRotator(0.f, InYawDegrees, 0.f), FVector(Location.X, Location.Y, (Top + Bottom) * .5f)), Params))
        {
            Piece->Configure(Top, Bottom);
            Piece->SetMaterialIndex(Material);
        }
        return;
    }
    FVector Placed, Size;
    FString Why;
    if (!AttachAllowed(World, BasePiece, Type, InYawDegrees, Placed, Size, Why)) return;
    if (FVector::Dist2D(Survivor->GetActorLocation(), Placed) > Reach + 300.f) return;
    if (AEWBuildPiece* Piece = World->SpawnActor<AEWBuildPiece>(AEWBuildPiece::StaticClass(), FTransform(FRotator(0.f, BasePiece->GetActorRotation().Yaw, 0.f), Placed), Params))
        Piece->ConfigureAttached(Type, Size, Material, BasePiece);
}

void UEWBuildComponent::ServerDemolish_Implementation(AEWBuildPiece* Piece)
{
    const AEWCharacter* Survivor = GetSurvivor();
    if (!Piece || !Survivor) return;
    if (FVector::Dist(Survivor->GetActorLocation(), Piece->GetActorLocation()) > Reach + Half + 300.f) return;
    // Taking a piece away takes everything that stands on it.
    {
        TArray<AEWBuildPiece*> Doomed;
        Doomed.Add(Piece);
        for (int32 I = 0; I < Doomed.Num(); ++I)
            for (TActorIterator<AEWBuildPiece> It(GetWorld()); It; ++It)
                if (It->GetBase() == Doomed[I]) Doomed.AddUnique(*It);
        for (int32 I = Doomed.Num() - 1; I > 0; --I) Doomed[I]->Destroy();
    }
    Piece->Destroy();
}
