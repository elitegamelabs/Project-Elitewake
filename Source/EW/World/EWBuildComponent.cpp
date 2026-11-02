#include "World/EWBuildComponent.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "EWControllerIcons.h"
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
#include "Engine/Texture2D.h"
#include "Styling/AppStyle.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/SOverlay.h"
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

    // The second wheel (owner, October 27: doors, frames, windows): a frame is a wall with an opening, a leaf fills it. Placeholder set, TBD.
    struct FFitting { const TCHAR* Label; EEWBuildPieceType Type; int32 Design; };
    const FFitting Fittings[UEWBuildComponent::FittingCount] = {
        {TEXT("Door frame"), EEWBuildPieceType::TopWall, 1}, {TEXT("Door"), EEWBuildPieceType::Door, 0},
        {TEXT("Window frame"), EEWBuildPieceType::TopWall, 2}, {TEXT("Window"), EEWBuildPieceType::Window, 0}};
    // Option backgrounds are semi-transparent (owner, October 27), dark enough to read white on the parchment.
    const FLinearColor OptionIdle(.04f, .03f, .02f, .62f), OptionHot(1.f, .75f, .15f, .78f);
    // The dial's middle text: tar-dark ink (#181815, CLAUDE.md 9.1) on the parchment.
    const FLinearColor Ink(.009f, .009f, .007f, 1.f);
    const TCHAR* const ParchmentTexture = TEXT("/Game/Elitewake/UI/Journal/T_JournalParchment.T_JournalParchment");
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

bool UEWBuildComponent::IsOnFoot() const
{
    // On foot: not at a helm, a gun, a sail's lines (LB trims there) or a ladder.
    const AEWCharacter* Survivor = GetSurvivor();
    return Survivor && !Survivor->GetHelmShip() && !Survivor->GetGunShip() && !Survivor->GetLinesShip() && !Survivor->IsOnLadder();
}

bool UEWBuildComponent::EnterBuildMode()
{
    if (Mode != EEWBuildMode::Off) return true;
    if (!IsOnFoot()) return false;
    SetMode(EEWBuildMode::Place);
    // Owner, November 1: entering shows the piece dial at once, with no second press.
    bFittingsWheel = false;
    ShowDial(true);
    return true;
}

void UEWBuildComponent::LeaveBuildMode()
{
    SetMode(EEWBuildMode::Off);
}

void UEWBuildComponent::ToggleBuildMode()
{
    if (Mode != EEWBuildMode::Off) LeaveBuildMode();
    else EnterBuildMode();
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

void UEWBuildComponent::CycleDesign(int32 Direction)
{
    DesignIndex = (DesignIndex + (Direction >= 0 ? 1 : -1) + AEWBuildPiece::DesignCount) % AEWBuildPiece::DesignCount;
}

void UEWBuildComponent::StepSlot(int32 Direction)
{
    const int32 Now = FMath::Min(static_cast<int32>(SelectedType), SlotCount - 1);
    SelectedType = SlotType((Now + (Direction >= 0 ? 1 : -1) + SlotCount) % SlotCount);
    HoveredSlot = FMath::Min(static_cast<int32>(SelectedType), SlotCount - 1);
}

void UEWBuildComponent::SelectSlot(int32 Slot)
{
    SelectedType = SlotType(Slot);
    HoveredSlot = static_cast<int32>(SelectedType);
    ShowDial(false);
}

void UEWBuildComponent::SelectFitting(int32 Index)
{
    const FFitting& Fitting = Fittings[FMath::Clamp(Index, 0, FittingCount - 1)];
    SelectedType = Fitting.Type;
    DesignIndex = Fitting.Design;
    ShowDial(false);
}

void UEWBuildComponent::ToggleDial()
{
    if (Mode != EEWBuildMode::Place) return;
    const bool bClose = bDialOpen;
    if (bDialOpen) ShowDial(false);
    if (!bClose) { bFittingsWheel = false; ShowDial(true); }
}

void UEWBuildComponent::ToggleFittings()
{
    if (Mode != EEWBuildMode::Place) return;
    const bool bClose = bDialOpen && bFittingsWheel;
    if (bDialOpen) ShowDial(false);
    if (!bClose) { bFittingsWheel = true; ShowDial(true); }
}

void UEWBuildComponent::SetDialPointer(float X, float Y)
{
    DialPointer = FVector2D(X, Y).GetClampedToMaxSize(1.f);
    if (DialPointer.Size() < DialDeadZone) return;
    float Degrees = FMath::RadiansToDegrees(FMath::Atan2(DialPointer.X, DialPointer.Y));
    if (Degrees < 0.f) Degrees += 360.f;
    const int32 Count = bFittingsWheel ? FittingCount : SlotCount;
    HoveredSlot = FMath::RoundToInt(Degrees / (360.f / Count)) % Count;
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
        bFittingsWheel = false;
        if (DialWidget.IsValid()) GEngine->GameViewport->RemoveViewportWidgetContent(DialWidget.ToSharedRef());
        DialWidget.Reset();
        return;
    }
    DialPointer = FVector2D::ZeroVector;
    const int32 Count = bFittingsWheel ? FittingCount : SlotCount;
    HoveredSlot = bFittingsWheel ? 0 : FMath::Min(static_cast<int32>(SelectedType), SlotCount - 1);
    const FSlateBrush* White = FAppStyle::GetBrush("WhiteBrush");
    TSharedRef<SCanvas> Canvas = SNew(SCanvas);
    // Sized for CLAUDE.md 9.2 at 1080p: 18 px labels, 22 px middle text, the sheet behind every label.
    const FVector2D Middle(615.f, 330.f);
    const FVector2D DialScale(DialRadius * 2.3f, DialRadius * 1.3f);   // the ring's half-width and half-height, px
    const bool bFittings = bFittingsWheel;
    for (int32 Slot = 0; Slot < Count; ++Slot)
    {
        const float A = FMath::DegreesToRadians(Slot * (360.f / Count));
        const FVector2D At = Middle + FVector2D(FMath::Sin(A), -FMath::Cos(A)) * DialScale - FVector2D(110.f, 35.f);
        const FText Label = FText::FromString(bFittings ? Fittings[Slot].Label : AEWBuildPiece::TypeName(SlotType(Slot)));
        Canvas->AddSlot().Position(At).Size(FVector2D(220.f, 70.f))
        [
            SNew(SBorder).BorderImage(White).Padding(FMargin(4.f, 6.f))
            .BorderBackgroundColor_Lambda([this, Slot]() { return Slot == HoveredSlot ? OptionHot : OptionIdle; })
            [
                SNew(STextBlock).Text(Label).Justification(ETextJustify::Center).AutoWrapText(true).Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
                .ColorAndOpacity_Lambda([this, Slot]() { return Slot == HoveredSlot ? FSlateColor(FLinearColor::Black) : FSlateColor(FLinearColor::White); })
            ]
        ];
    }
    Canvas->AddSlot().Position(Middle - FVector2D(170.f, 70.f)).Size(FVector2D(340.f, 140.f))
    [
        // Dark ink on the parchment.
        SNew(STextBlock).Justification(ETextJustify::Center).ColorAndOpacity(Ink).Font(FCoreStyle::GetDefaultFontStyle("Regular", 22))
        .Text_Lambda([this, bFittings]()
        {
            // The controller's own button names (owner, November 1): RB / LB+RB and B on an Xbox pad, R1 / L1+R1 and Circle on a
            // PlayStation pad, plain words for any other; the keyboard's keys while the keyboard is in use.
            const auto* PC = Cast<AEWPlayerController>(GetOwner());
            const bool bPad = PC && PC->UsesControllerPrompts();
            const EEWGamepadFamily Family = PC ? PC->GetPromptFamily() : EEWGamepadFamily::Unknown;
            const auto Name = [Family](const FKey& Key) { return FEWControllerIcons::ButtonName(Key, Family); };
            const FString Materials = bPad ? FString::Printf(TEXT("%s / %s+%s"), *Name(EKeys::Gamepad_RightShoulder),
                *Name(EKeys::Gamepad_LeftShoulder), *Name(EKeys::Gamepad_RightShoulder)) : FString(TEXT("C / Z"));
            const FString Wheel = bPad ? Name(EKeys::Gamepad_FaceButton_Left) : FString(TEXT("F"));
            const FString Close = bPad ? Name(EKeys::Gamepad_FaceButton_Right) : FString(TEXT("Esc"));
            return FText::FromString(FString::Printf(TEXT("%s\n%s (%s)\n%s: %s\n%s: close"), bFittings ? Fittings[FMath::Clamp(HoveredSlot, 0, FittingCount - 1)].Label : AEWBuildPiece::TypeName(SlotType(HoveredSlot)),
                AEWBuildPiece::MaterialName(MaterialIndex), *Materials, *Wheel, bFittings ? TEXT("back to pieces") : TEXT("doors and windows"), *Close));
        })
    ];
    Canvas->AddSlot()
    .Position(TAttribute<FVector2D>::CreateLambda([this, Middle, DialScale]() { return Middle + FVector2D(DialPointer.X, -DialPointer.Y) * DialScale - FVector2D(6.f, 6.f); }))
    .Size(FVector2D(12.f, 12.f))
    [
        SNew(SBorder).BorderImage(White).BorderBackgroundColor(FLinearColor(1.f, .2f, .2f, 1.f))
    ];
    // The parchment behind the ring (owner, November 1), the journal's own sheet.
    if (!Parchment) Parchment = LoadObject<UTexture2D>(nullptr, ParchmentTexture, nullptr, LOAD_Quiet | LOAD_NoWarn);
    ParchmentBrush = FSlateBrush();
    ParchmentBrush.DrawAs = ESlateBrushDrawType::Image;
    ParchmentBrush.ImageSize = FVector2D(1310.f, 720.f);
    if (Parchment) ParchmentBrush.SetResourceObject(Parchment);
    DialWidget = SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Center)
    [
        SNew(SOverlay)
        + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
        [
            SNew(SBox).WidthOverride(1310.f).HeightOverride(720.f)
            [
                SNew(SImage).Image(&ParchmentBrush).Visibility(Parchment ? EVisibility::HitTestInvisible : EVisibility::Collapsed)
            ]
        ]
        + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
        [
            SNew(SBox).WidthOverride(1230.f).HeightOverride(660.f)[Canvas]
        ]
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

EEWBuildKeyAction UEWBuildComponent::ResolveKey(const FKey& Key, bool bPressed, bool bShoulderHeld, EEWBuildMode InMode, bool bInDialOpen)
{
    using A = EEWBuildKeyAction;
    // Owner, November 1: B (keyboard), or hold LB and press d-pad right (controller), enters and leaves.
    const bool bChord = Key == EKeys::Gamepad_DPad_Right && bShoulderHeld;
    if (InMode == EEWBuildMode::Off)
        // Nothing else is Build Mode's while it is off: d-pad right alone stays hotbar slot 3, R3 and LB stay where they are.
        return bPressed && (Key == EKeys::B || bChord) ? A::Enter : A::None;
    // LB is only ever half of a chord here; it reaches the controller, which tracks it (and the hotbar's LB + face buttons).
    if (Key == EKeys::Gamepad_LeftShoulder) return A::None;
    auto On = [bPressed](A Action) { return bPressed ? Action : A::Consume; };
    if (Key == EKeys::B || bChord) return On(A::Leave);
    // Escape and the B button close the dial first, then leave.
    if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right) return On(bInDialOpen ? A::CloseDial : A::Leave);
    if (Key == EKeys::Tab || Key == EKeys::Gamepad_FaceButton_Top) return On(A::ToggleDial);
    if (Key == EKeys::F || Key == EKeys::Gamepad_FaceButton_Left) return On(A::ToggleFittings);
    if (Key == EKeys::X || Key == EKeys::Gamepad_RightThumbstick) return On(A::ToggleDemolish);
    if (Key == EKeys::Q || Key == EKeys::Gamepad_DPad_Left) return On(A::RotateLeft);
    if (Key == EKeys::E || Key == EKeys::Gamepad_DPad_Right) return On(A::RotateRight);
    if (Key == EKeys::C) return On(A::MaterialNext);
    if (Key == EKeys::Z) return On(A::MaterialPrevious);
    if (Key == EKeys::Gamepad_RightShoulder) return On(bShoulderHeld ? A::MaterialPrevious : A::MaterialNext);
    if (Key == EKeys::R || Key == EKeys::Gamepad_DPad_Up) return On(A::DesignNext);
    if (Key == EKeys::Gamepad_DPad_Down) return On(A::DesignPrevious);
    if (Key == EKeys::MouseScrollUp) return On(A::SlotNext);
    if (Key == EKeys::MouseScrollDown) return On(A::SlotPrevious);
    if (Key == EKeys::LeftMouseButton || Key == EKeys::Gamepad_RightTrigger || Key == EKeys::Gamepad_FaceButton_Bottom) return On(A::Confirm);
    return A::None;
}

bool UEWBuildComponent::HandleKey(const FInputKeyEventArgs& Params, bool bShoulderHeld)
{
    // A release goes with its press.
    if (Params.Event == IE_Released && SwallowedReleases.Remove(Params.Key) > 0) return true;
    const bool bPressed = Params.Event == IE_Pressed;
    using A = EEWBuildKeyAction;
    const A Action = ResolveKey(Params.Key, bPressed, bShoulderHeld, Mode, bDialOpen);
    switch (Action)
    {
    case A::None: return false;
    case A::Consume: return true;
    case A::Enter:
        // Off a helm, gun, sail's lines or ladder only; otherwise the key goes on to whatever else it does there.
        if (!EnterBuildMode()) return false;
        break;
    case A::Leave: LeaveBuildMode(); break;
    case A::CloseDial: ShowDial(false); break;
    case A::ToggleDial: ToggleDial(); break;
    case A::ToggleFittings: ToggleFittings(); break;
    case A::ToggleDemolish: ToggleDemolish(); break;
    case A::RotateLeft: RotateStep(-1); break;
    case A::RotateRight: RotateStep(1); break;
    case A::MaterialNext: CycleMaterial(1); break;
    case A::MaterialPrevious: CycleMaterial(-1); break;
    case A::DesignNext: CycleDesign(1); break;
    case A::DesignPrevious: CycleDesign(-1); break;
    case A::SlotNext: case A::SlotPrevious:
        if (Mode == EEWBuildMode::Place && !bDialOpen) StepSlot(Action == A::SlotNext ? 1 : -1);
        break;
    case A::Confirm: Confirm(); break;
    }
    if (bPressed) SwallowedReleases.Add(Params.Key);
    return true;
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

bool UEWBuildComponent::AttachAllowed(UWorld* World, AEWBuildPiece* Base, EEWBuildPieceType Type, FVector& OutLocation, FVector& OutSize, FRotator& OutRotation, FString& Reason)
{
    Reason.Reset();
    // A "cell" is a foundation or a ceiling: pieces stand on the top of one, and every chain of cells ends on a foundation
    // (a ceiling's Base is the cell under it), so you may build off a ceiling as long as everything below stands on a foundation.
    // A full wall can also carry another wall straight above it, one high.
    auto IsCell = [](const AEWBuildPiece* P) { return P && (P->GetPieceType() == EEWBuildPieceType::Foundation || P->GetPieceType() == EEWBuildPieceType::RightCeiling); };
    if (AEWBuildPiece::IsFitting(Type))
    {
        const bool bDoor = Type == EEWBuildPieceType::Door;
        if (!Base || Base->GetPieceType() != EEWBuildPieceType::TopWall || Base->GetDesign() != (bDoor ? 1 : 2))
        { Reason = bDoor ? TEXT("A door goes in a door frame: build a wall with a doorway first.") : TEXT("A window goes in a window frame: build a wall with a window first."); return false; }
    }
    else if (Base && Base->GetPieceType() == EEWBuildPieceType::TopWall)
    {
        if (!AEWBuildPiece::IsWall(Type)) { Reason = TEXT("Only a wall stands on a wall."); return false; }
        if (!IsCell(Base->GetBase())) { Reason = TEXT("Walls stack one high."); return false; }
    }
    else if (!IsCell(Base)) { Reason = TEXT("Needs a foundation (or a ceiling on one) to attach to."); return false; }
    AEWBuildPiece::AttachedTransform(Base, Type, OutLocation, OutSize, OutRotation);
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
        if (AEWBuildPiece::IsStair(Type) && AEWBuildPiece::IsStair(It->GetPieceType())) { Reason = TEXT("This cell already has a staircase."); return false; }
        const bool bWall = AEWBuildPiece::IsWall(It->GetPieceType());
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
            ShowGhost(AimedPiece->GetActorLocation(), AimedPiece->GetActorRotation(), (AimedPiece->GetPieceType() == EEWBuildPieceType::Foundation ? AimedPiece->Slab->GetComponentScale() * 100.f : AimedPiece->GetPieceSize()) + FVector(10.f), false);
        else if (GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false);
        return;
    }
    if (SelectedType != EEWBuildPieceType::Foundation)
    {
        // Attached pieces: the foundation looked at (or the one under the piece looked at, or the nearest to where the aim lands).
        AEWBuildPiece* Base = Cast<AEWBuildPiece>(Hit.GetActor());
        const bool bStacking = Base && Base->GetPieceType() == EEWBuildPieceType::TopWall && (AEWBuildPiece::IsWall(SelectedType) || AEWBuildPiece::IsFitting(SelectedType));
        if (Base && !bStacking && Base->GetPieceType() != EEWBuildPieceType::Foundation && Base->GetPieceType() != EEWBuildPieceType::RightCeiling) Base = Base->GetBase();
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
        FRotator Rotation;
        FString Why;
        bAimOk = AttachAllowed(World, Base, SelectedType, Location, Size, Rotation, Why);
        if (bAimOk && FVector::Dist2D(Survivor->GetActorLocation(), Location) > Reach) { bAimOk = false; Why = TEXT("Too far away."); }
        AimReason = Why;
        if (!Base) { if (GhostActor) GhostActor->GetStaticMeshComponent()->SetVisibility(false); return; }
        AimLocation = Location;
        ShowGhost(Location, Rotation, Size, bAimOk);
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
    ShowGhost(FVector(Centre.X, Centre.Y, (Top + Bottom) * .5f), FRotator(0.f, Yaw, 0.f), FVector(Half * 2.f, Half * 2.f, FMath::Max(Top - Bottom, 5.f)), bAimOk);
}

void UEWBuildComponent::ShowGhost(const FVector& Centre, const FRotator& Rotation, const FVector& Size, bool bOk)
{
    if (!GhostActor) return;
    UStaticMeshComponent* Mesh = GhostActor->GetStaticMeshComponent();
    Mesh->SetWorldScale3D(Size / 100.f);
    Mesh->SetWorldLocationAndRotation(Centre, Rotation);
    Glow->SetVectorParameterValue(TEXT("Colour"), bOk ? Blue : Red);
    Mesh->SetVisibility(true);
}

void UEWBuildComponent::TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaSeconds, TickType, ThisTickFunction);
    if (Mode == EEWBuildMode::Off) return;
    if (!IsOnFoot()) { SetMode(EEWBuildMode::Off); return; }
    if (bDialOpen) UpdateDial(DeltaSeconds);
    else UpdateAim();
#if !UE_BUILD_SHIPPING
    if (GEngine)
    {
        const FString Line = bDialOpen
            ? FString::Printf(TEXT("BUILD MODE  %s  point at one: mouse or either stick   Pick: left mouse / A / RT   Other wheel: F / X   Close: Esc / B button   Leave: B key"), bFittingsWheel ? TEXT("DOORS AND WINDOWS") : TEXT("PIECE DIAL"))
            : FString::Printf(TEXT("BUILD MODE  %s [%s]  [%s]  Rotate: Q/E or d-pad L/R   Material: C/Z or RB / LB+RB   Design: R or d-pad U   Dial: Tab or Y   %s: X or R3   Leave: B or Esc (B button)"),
                Mode == EEWBuildMode::Demolish ? TEXT("DEMOLISH") : AEWBuildPiece::TypeName(SelectedType), AEWBuildPiece::MaterialName(MaterialIndex),
                bAimOk ? TEXT("OK") : *AimReason, Mode == EEWBuildMode::Demolish ? TEXT("Place") : TEXT("Demolish"));
        GEngine->AddOnScreenDebugMessage(7701, .2f, bAimOk || bDialOpen ? FColor::Cyan : FColor::Orange, Line);
    }
#endif
}

void UEWBuildComponent::Confirm()
{
    if (bDialOpen) { if (bFittingsWheel) SelectFitting(HoveredSlot); else SelectSlot(HoveredSlot); return; }
    if (Mode == EEWBuildMode::Place && bAimOk) ServerPlace(SelectedType, AimLocation, YawDegrees, MaterialIndex, DesignIndex, AimBase);
    else if (Mode == EEWBuildMode::Demolish && bAimOk && AimedPiece) ServerDemolish(AimedPiece);
}

void UEWBuildComponent::ServerPlace_Implementation(EEWBuildPieceType Type, FVector Location, float InYawDegrees, int32 Material, int32 InDesign, AEWBuildPiece* BasePiece)
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
    FRotator Rotation;
    FString Why;
    if (!AttachAllowed(World, BasePiece, Type, Placed, Size, Rotation, Why)) return;
    if (FVector::Dist2D(Survivor->GetActorLocation(), Placed) > Reach + 300.f) return;
    if (AEWBuildPiece* Piece = World->SpawnActor<AEWBuildPiece>(AEWBuildPiece::StaticClass(), FTransform(Rotation, Placed), Params))
        Piece->ConfigureAttached(Type, Size, Material, InDesign, BasePiece);
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
