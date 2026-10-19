#if WITH_DEV_AUTOMATION_TESTS
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWPlayerController.h"
#include "EWSurvivalComponent.h"
#include "EWInteractionComponent.h"
#include "Ships/EWWindSubsystem.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/AutomationTest.h"
#include <limits>

namespace EWShipTest
{
    UEWItemDefinition* Item(const TCHAR* Id, EEWShipMountType Type = EEWShipMountType::None, EEWSailSize Size = EEWSailSize::None)
    {
        auto* Def = NewObject<UEWItemDefinition>(GetTransientPackage());
        Def->ItemId = Id; Def->DisplayName = FText::FromString(Id);
        Def->FittingMountType = Type; Def->FittingSailSize = Size;
        return Def;
    }
    FEWShipMount Mount(const TCHAR* Id, EEWShipMountType Type, FVector Location, EEWSailSize Size = EEWSailSize::None)
    {
        FEWShipMount M; M.MountId = Id; M.Type = Type; M.SailSize = Size; M.Transform = FTransform(Location);
        return M;
    }
    void Aim(AEWPlayerController* PC, AEWCharacter* C, const AEWShip* Ship, FName MountId)
    {
        FVector Eye; FRotator Unused;
        C->GetActorEyesViewPoint(Eye, Unused);
        PC->SetControlRotation((Ship->GetMountWorldTransform(MountId).GetLocation() - Eye).Rotation());
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipFittingTest, "Elitewake.Ships.FittingAuthority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipFittingTest::RunTest(const FString& Parameters)
{
    using namespace EWShipTest;

    // Definition authoring rules.
    auto* Def = NewObject<UEWShipDefinition>(GetTransientPackage());
    Def->ShipId = TEXT("TestSloop");
    Def->Mounts = {Mount(TEXT("Helm"), EEWShipMountType::Helm, FVector(-250, 0, 130)),
                   Mount(TEXT("Mainsail"), EEWShipMountType::Sail, FVector(0, 0, 130), EEWSailSize::Medium),
                   Mount(TEXT("PortCannon"), EEWShipMountType::Cannon, FVector(0, -120, 130))};
    TestTrue(TEXT("Valid definition"), Def->Validate().IsEmpty());
    auto* Bad = DuplicateObject(Def, GetTransientPackage());
    Bad->Mounts.Add(Mount(TEXT("Helm"), EEWShipMountType::Helm, FVector::ZeroVector));
    TestFalse(TEXT("Duplicate mount ids rejected"), Bad->Validate().IsEmpty());
    Bad->Mounts = {Mount(TEXT("Sail"), EEWShipMountType::Sail, FVector::ZeroVector)};
    TestFalse(TEXT("Sail mount without a size rejected"), Bad->Validate().IsEmpty());

    UEWItemDefinition* Helm = Item(TEXT("TestHelm"), EEWShipMountType::Helm);
    UEWItemDefinition* MediumSail = Item(TEXT("TestMediumSail"), EEWShipMountType::Sail, EEWSailSize::Medium);
    UEWItemDefinition* SmallSail = Item(TEXT("TestSmallSail"), EEWShipMountType::Sail, EEWSailSize::Small);
    UEWItemDefinition* Plank = Item(TEXT("TestFiller"));
    TestTrue(TEXT("Helm fits helm mount"), UEWShipDefinition::Accepts(*Def->FindMount(TEXT("Helm")), Helm));
    TestTrue(TEXT("Medium sail fits medium mount"), UEWShipDefinition::Accepts(*Def->FindMount(TEXT("Mainsail")), MediumSail));
    TestFalse(TEXT("Small sail does not fit medium mount"), UEWShipDefinition::Accepts(*Def->FindMount(TEXT("Mainsail")), SmallSail));
    TestFalse(TEXT("Non-fitting item fits nothing"), UEWShipDefinition::Accepts(*Def->FindMount(TEXT("Helm")), Plank));

    // World setup: a survivor standing on the deck of a bare hull.
    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    auto* CharClass = LoadClass<AEWCharacter>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    auto* PCClass = LoadClass<AEWPlayerController>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.BP_ThirdPersonPlayerController_C"));
    if (!TestNotNull(TEXT("Survivor class"), CharClass) || !TestNotNull(TEXT("Controller class"), PCClass))
    { World->DestroyWorld(false); return false; }
    FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Ship = World->SpawnActorDeferred<AEWShip>(AEWShip::StaticClass(), FTransform::Identity);
    Ship->Definition = Def;
    Ship->FinishSpawning(FTransform::Identity);
    auto* C = World->SpawnActor<AEWCharacter>(CharClass, FVector(-120, 0, 186), FRotator::ZeroRotator, Params);
    auto* PC = World->SpawnActor<AEWPlayerController>(PCClass);
    PC->Possess(C);
    UEWInventoryComponent* Inventory = C->GetInventoryComponent();

    // A bare hull: aiming at an empty mount with nothing to fit offers no action.
    Aim(PC, C, Ship, TEXT("Helm"));
    TestEqual(TEXT("Aim finds the helm mount"), Ship->FindAimedMount(C), FName(TEXT("Helm")));
    TestFalse(TEXT("Nothing to install without a carried helm"), Ship->CanInteract_Implementation(C));
    TestFalse(TEXT("Bare hull has no helm"), Ship->HasFittingOfType(EEWShipMountType::Helm));

    // Install the helm through the ordinary interaction.
    Inventory->AddItem(Helm, 1);
    TestTrue(TEXT("Carried helm can be installed"), Ship->CanInteract_Implementation(C));
    TestTrue(TEXT("Interact installs the helm"), Ship->Interact_Implementation(C));
    TestEqual(TEXT("Helm left the inventory"), Inventory->GetItemCount(Helm), 0);
    TestEqual(TEXT("Helm is on the helm mount"), Ship->GetFitting(TEXT("Helm")), Helm);
    TestEqual(TEXT("Occupied mount refuses a second fitting"), Ship->InstallFitting(C, TEXT("Helm")), EEWFittingResult::Occupied);

    // A sail must match its mount's size.
    Inventory->AddItem(SmallSail, 1);
    Aim(PC, C, Ship, TEXT("Mainsail"));
    TestEqual(TEXT("Aim finds the mainsail mount"), Ship->FindAimedMount(C), FName(TEXT("Mainsail")));
    TestEqual(TEXT("Small sail cannot fill a medium mount"), Ship->InstallFitting(C, TEXT("Mainsail")), EEWFittingResult::NoFitting);
    TestEqual(TEXT("Rejected sail stays carried"), Inventory->GetItemCount(SmallSail), 1);
    Inventory->AddItem(MediumSail, 1);
    TestEqual(TEXT("Medium sail installs"), Ship->InstallFitting(C, TEXT("Mainsail")), EEWFittingResult::Installed);
    TestEqual(TEXT("The small sail was not taken"), Inventory->GetItemCount(SmallSail), 1);

    // Removal returns the fitting, but never loses it to a full inventory.
    Inventory->AddItem(Plank, Inventory->GetMaxSlotCount());
    TestEqual(TEXT("Full inventory blocks removal"), Ship->RemoveFitting(C, TEXT("Helm")), EEWFittingResult::InventoryFull);
    TestEqual(TEXT("Helm stays installed"), Ship->GetFitting(TEXT("Helm")), Helm);
    Inventory->RemoveItem(Plank, Inventory->GetItemCount(Plank));
    TestEqual(TEXT("Removal succeeds with room"), Ship->RemoveFitting(C, TEXT("Helm")), EEWFittingResult::Removed);
    TestEqual(TEXT("Helm returned to the inventory"), Inventory->GetItemCount(Helm), 1);
    TestNull(TEXT("Helm mount is empty again"), Ship->GetFitting(TEXT("Helm")));
    TestEqual(TEXT("Removing from an empty mount fails"), Ship->RemoveFitting(C, TEXT("Helm")), EEWFittingResult::NoMount);
    TestEqual(TEXT("Unknown mount rejected"), Ship->InstallFitting(C, TEXT("Bowsprit")), EEWFittingResult::NoMount);

    // A dead survivor cannot change fittings.
    C->GetSurvivalComponent()->ApplyDamage(100000.f);
    TestEqual(TEXT("Dead survivor rejected"), Ship->InstallFitting(C, TEXT("Helm")), EEWFittingResult::NotAllowed);
    TestEqual(TEXT("Dead survivor keeps the helm"), Inventory->GetItemCount(Helm), 1);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipSailingTest, "Elitewake.Ships.SailingAuthority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipSailingTest::RunTest(const FString& Parameters)
{
    using namespace EWShipTest;
    auto* Def = NewObject<UEWShipDefinition>(GetTransientPackage());
    Def->ShipId = TEXT("TestSloop");
    Def->TopSpeed = 700.f; Def->TurnRate = 30.f;
    Def->Mounts = {Mount(TEXT("Helm"), EEWShipMountType::Helm, FVector(-250, 0, 130)),
                   Mount(TEXT("Mainsail"), EEWShipMountType::Sail, FVector(0, 0, 130), EEWSailSize::Medium),
                   Mount(TEXT("Headsail"), EEWShipMountType::Sail, FVector(300, 0, 130), EEWSailSize::Small)};
    UEWItemDefinition* Helm = Item(TEXT("TestHelm"), EEWShipMountType::Helm);
    UEWItemDefinition* MediumSail = Item(TEXT("TestMediumSail"), EEWShipMountType::Sail, EEWSailSize::Medium);

    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    auto* CharClass = LoadClass<AEWCharacter>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    auto* PCClass = LoadClass<AEWPlayerController>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.BP_ThirdPersonPlayerController_C"));
    UEWWindSubsystem* Wind = World->GetSubsystem<UEWWindSubsystem>();
    if (!TestNotNull(TEXT("Survivor class"), CharClass) || !TestNotNull(TEXT("Controller class"), PCClass) || !TestNotNull(TEXT("Wind"), Wind))
    { World->DestroyWorld(false); return false; }
    auto SpawnShip = [&](FVector Location)
    {
        auto* S = World->SpawnActorDeferred<AEWShip>(AEWShip::StaticClass(), FTransform(Location));
        S->Definition = Def;
        S->FinishSpawning(FTransform(Location));
        return S;
    };
    // Two identical ships side by side, and a third hull dead ahead of the first to collide with.
    AEWShip* A = SpawnShip(FVector(0, 0, 0));
    AEWShip* B = SpawnShip(FVector(0, 3000, 0));
    // Keep the collision target clear of the anchor's permitted swing circle; it is repositioned for that check later.
    AEWShip* Blocker = SpawnShip(FVector(50000, 0, 0));
    FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* C = World->SpawnActor<AEWCharacter>(CharClass, FVector(-120, 0, 186), FRotator::ZeroRotator, Params);
    auto* Other = World->SpawnActor<AEWCharacter>(CharClass, FVector(-120, 60, 186), FRotator::ZeroRotator, Params);
    auto* PC = World->SpawnActor<AEWPlayerController>(PCClass);
    auto* OtherPC = World->SpawnActor<AEWPlayerController>(PCClass);
    PC->Possess(C); OtherPC->Possess(Other);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();
    C->GetInventoryComponent()->AddItem(Helm, 2);
    C->GetInventoryComponent()->AddItem(MediumSail, 2);

    // A bare hull cannot be steered or sailed.
    TestFalse(TEXT("No helm, no helmsman"), A->TakeHelm(C));
    TestEqual(TEXT("No sails fitted"), A->GetFittedSailFraction(), 0.f);
    TestTrue(TEXT("Ships start anchored"), A->IsAnchored());
    // These transient actors were spawned before this lightweight test world began play. Re-lay their anchors so
    // the chain has the same bed and reach that a map-spawned ship receives in BeginPlay.
    TestTrue(TEXT("Lift A's transient anchor"), A->SetAnchored(C, false));
    TestTrue(TEXT("Lay A's transient anchor"), A->SetAnchored(C, true));
    TestTrue(TEXT("Lift B's transient anchor"), B->SetAnchored(C, false));
    TestTrue(TEXT("Lay B's transient anchor"), B->SetAnchored(C, true));
    for (AEWShip* S : {A, B})
    {
        TestEqual(TEXT("Helm installs"), S->InstallFitting(C, TEXT("Helm")), EEWFittingResult::Installed);
        TestEqual(TEXT("Mainsail installs"), S->InstallFitting(C, TEXT("Mainsail")), EEWFittingResult::Installed);
    }
    TestTrue(TEXT("Mainsail is 2 of 3 sail capacity"), FMath::IsNearlyEqual(A->GetFittedSailFraction(), 2.f / 3.f));

    // Taking the helm through the ordinary interaction.
    Aim(PC, C, A, TEXT("Helm"));
    TestTrue(TEXT("Can take the free helm"), A->CanInteract_Implementation(C));
    TestTrue(TEXT("Interact takes the helm"), A->Interact_Implementation(C));
    TestEqual(TEXT("Helmsman recorded"), A->GetHelmsman(), C);
    TestEqual(TEXT("Survivor knows its helm"), C->GetHelmShip(), A);
    TestTrue(TEXT("Helmsman rides the ship"), C->GetAttachParentActor() == A);
    TestTrue(TEXT("Survivor movement is off at the helm"), C->GetCharacterMovement()->MovementMode == MOVE_None);
    TestEqual(TEXT("Interaction targets the helm ship from any aim"), FEWInteractionTargeting::FindTarget(C), static_cast<AActor*>(A));
    TestFalse(TEXT("A second survivor cannot take an occupied helm"), A->TakeHelm(Other));
    TestEqual(TEXT("The occupied helm cannot be removed"), A->RemoveFitting(C, TEXT("Helm")), EEWFittingResult::Occupied);

    // Only the helmsman commands, with sane values.
    TestFalse(TEXT("Others cannot set sails"), A->StepSails(Other, 1));
    TestFalse(TEXT("Others cannot steer"), A->SetRudder(Other, 1));
    TestFalse(TEXT("Rudder beyond hard over rejected"), A->SetRudder(C, 2));
    TestFalse(TEXT("NaN rudder rejected"), A->SetRudder(C, std::numeric_limits<float>::quiet_NaN()));
    TestFalse(TEXT("Sail step must be one notch"), A->StepSails(C, 2));
    PC->GetInteractionComponent()->SetMenuBlocked(true);
    TestFalse(TEXT("An open menu blocks commands"), A->StepSails(C, 1));
    PC->GetInteractionComponent()->SetMenuBlocked(false);
    TestTrue(TEXT("Quarter sail"), A->StepSails(C, 1));
    TestEqual(TEXT("Quarter setting"), A->GetSailState(), EEWSailState::Quarter);
    TestTrue(TEXT("Half sail"), A->StepSails(C, 1));
    TestEqual(TEXT("Half setting"), A->GetSailState(), EEWSailState::Half);
    TestTrue(TEXT("Three-quarter sail"), A->StepSails(C, 1));
    TestEqual(TEXT("Three-quarter setting"), A->GetSailState(), EEWSailState::ThreeQuarter);
    TestTrue(TEXT("Full sail"), A->StepSails(C, 1));
    TestTrue(TEXT("Already full stays full"), A->StepSails(C, 1) && A->GetSailState() == EEWSailState::Full);
    TestTrue(TEXT("Full sails load against the anchor chain"),
        FMath::IsNearlyEqual(A->ComputeTargetSpeed(), Def->TopSpeed * AEWShip::SailingPace * (2.f / 3.f)
            * UEWWindSubsystem::MinUpwindFactor, 1.f));
    // Trim: the sails swing with the helmsman's held direction, at a fixed rate, within their limits.
    TestFalse(TEXT("Others cannot trim"), A->SetSailTrim(Other, 1));
    TestFalse(TEXT("Trim direction must be one notch"), A->SetSailTrim(C, 2));
    auto Swing = [&](AEWShip* Ship, int32 Direction, int32 Steps)
    {
        Ship->SetSailTrim(C, Direction);
        for (int32 i = 0; i < Steps; ++i) Ship->SimulateSailing(AEWShip::SimulationStep);
        Ship->SetSailTrim(C, 0);
    };
    // Wind: well trimmed, full speed running before it; never less than 45 percent, so a ship always makes headway.
    Wind->SetWindYaw(0.f);   // Blowing toward +X, the way the ships face.
    TestEqual(TEXT("Sails start along the centreline"), A->GetSailAngle(), 0.f);
    TestTrue(TEXT("Running before the wind with the sails along the centreline gives the least"),
        FMath::IsNearlyEqual(A->GetWindFactor(), UEWWindSubsystem::MinUpwindFactor, .01f));
    Swing(A, 1, 40);
    TestEqual(TEXT("The sails swing out to starboard and stop at their limit"), A->GetSailAngle(), AEWShip::MaxSailAngle);
    TestTrue(TEXT("Squared away running before the wind, they draw fully"), FMath::IsNearlyEqual(A->GetWindFactor(), 1.f, .01f));
    Swing(A, 0, 10);
    TestEqual(TEXT("Released, the sails stay where they are"), A->GetSailAngle(), AEWShip::MaxSailAngle);
    Wind->SetWindYaw(180.f);
    TestEqual(TEXT("Into the wind the best angle is the centreline"), A->GetBestSailAngle(), 0.f);
    TestTrue(TEXT("Upwind still makes headway (45 percent)"),
        FMath::IsNearlyEqual(A->GetWindFactor(), UEWWindSubsystem::MinUpwindFactor, .01f));
    Wind->SetWindYaw(90.f);  // Across the ship, toward starboard.
    TestTrue(TEXT("On a beam reach the best angle is half way out to starboard"), FMath::IsNearlyEqual(A->GetBestSailAngle(), 45.f, .01f));
    const float BeamQuality = FMath::Cos(FMath::DegreesToRadians(67.5f));
    TestTrue(TEXT("Squared away on a beam reach draws according to its 45 degree trim error"),
        FMath::IsNearlyEqual(A->GetTrimQuality(), BeamQuality, .01f));
    TestTrue(TEXT("Partly drawing sails blend between minimum and beam-reach wind"),
        FMath::IsNearlyEqual(A->GetWindFactor(), UEWWindSubsystem::MinUpwindFactor
            + (.725f - UEWWindSubsystem::MinUpwindFactor) * BeamQuality, .01f));
    Swing(A, -1, 18);        // 85 down to 44.5 degrees.
    TestTrue(TEXT("Trimmed in to about 45 degrees, a beam reach gives 72.5 percent"), FMath::IsNearlyEqual(A->GetWindFactor(), .725f, .01f));
    Wind->SetWindYaw(0.f);
    Swing(A, 1, 40);
    for (int32 Step = 0; Step < 400 && !A->IsChainTaut(); ++Step) A->SimulateSailing(.05f);
    TestTrue(TEXT("The anchor chain becomes taut under full sail"), A->IsChainTaut());
    A->SimulateSailing(.05f);
    TestEqual(TEXT("A taut anchor chain stops the ship under full sail"), A->GetSpeed(), 0.f);
    TestTrue(TEXT("Raise anchor on A"), A->SetAnchored(C, false));
    TestTrue(TEXT("Raise anchor on B"), B->SetAnchored(C, false));
    TestFalse(TEXT("Raising a raised anchor changes nothing"), A->SetAnchored(C, false));
    TestTrue(TEXT("Downwind target includes the crossing pace and fitted sail"),
        FMath::IsNearlyEqual(A->ComputeTargetSpeed(), Def->TopSpeed * AEWShip::SailingPace * 2.f / 3.f, 1.f));

    // Leaving the helm keeps the sails set; the ship sails on.
    TestTrue(TEXT("Leave helm"), A->LeaveHelm(C));
    TestNull(TEXT("Helm is free"), A->GetHelmsman());
    TestNull(TEXT("Survivor released"), C->GetHelmShip());
    TestTrue(TEXT("Survivor collision restored"), C->GetCapsuleComponent()->GetCollisionEnabled() != ECollisionEnabled::NoCollision);
    TestEqual(TEXT("Sails stay full after leaving"), A->GetSailState(), EEWSailState::Full);

    // Set ship B the same way, then sail both for 2 seconds: A at 20 fps, B at 3 fps.
    C->SetActorLocation(B->GetActorTransform().TransformPosition(FVector(-120, 0, 186)));
    Aim(PC, C, B, TEXT("Helm"));
    TestTrue(TEXT("Take the helm of ship B"), B->Interact_Implementation(C));
    for (int32 Step = 0; Step < 4; ++Step) B->StepSails(C, 1);
    // Trimmed at anchor like A, so both start the comparison at rest.
    B->SetAnchored(C, true);
    Swing(B, 1, 40);
    for (int32 Step = 0; Step < 400 && !B->IsChainTaut(); ++Step) B->SimulateSailing(.05f);
    TestTrue(TEXT("Ship B is held at the same taut starting state"), B->IsChainTaut());
    B->SimulateSailing(.05f);
    B->SetAnchored(C, false);
    TestTrue(TEXT("Leave the helm of ship B"), B->LeaveHelm(C));
    const FVector StartA = A->GetActorLocation(), StartB = B->GetActorLocation();
    for (int32 i = 0; i < 40; ++i) A->SimulateSailing(.05f);
    for (int32 i = 0; i < 6; ++i) B->SimulateSailing(1.f / 3.f);
    const float DistA = FVector::Dist(StartA, A->GetActorLocation()), DistB = FVector::Dist(StartB, B->GetActorLocation());
    TestTrue(TEXT("The ship moves under sail"), DistA > 100.f && A->GetSpeed() > 0.f);
    // Fixed steps make frame rate irrelevant up to one step of leftover time (0.05 s).
    TestTrue(TEXT("3 fps covers the same distance as 20 fps, within one step"),
        FMath::Abs(DistA - DistB) <= Def->TopSpeed * AEWShip::SimulationStep);
    TestTrue(TEXT("3 fps reaches the same speed, within one step"),
        FMath::Abs(A->GetSpeed() - B->GetSpeed()) <= AEWShip::Acceleration * AEWShip::SimulationStep + .01f);

    // The rudder is held until changed, even across slow frames, and turns the ship.
    C->SetActorLocation(A->GetActorTransform().TransformPosition(FVector(-120, 0, 186)));
    Aim(PC, C, A, TEXT("Helm"));
    TestTrue(TEXT("Retake the helm of ship A"), A->Interact_Implementation(C));
    TestTrue(TEXT("Hard to starboard"), A->SetRudder(C, 1.f));
    const float YawBefore = A->GetActorRotation().Yaw;
    for (int32 i = 0; i < 3; ++i) A->SimulateSailing(1.f / 3.f);
    TestEqual(TEXT("Rudder is not dropped by slow frames"), A->GetRudder(), 1.f);
    TestTrue(TEXT("The ship turns to starboard"), A->GetActorRotation().Yaw > YawBefore + 5.f);
    TestTrue(TEXT("Centre the rudder"), A->SetRudder(C, 0.f));
    // The blade swings back to the middle within 0.8 s; from then the ship holds its course.
    for (int32 i = 0; i < 10; ++i) A->SimulateSailing(.1f);
    TestEqual(TEXT("The rudder blade is back in the middle"), A->GetRudderAngle(), 0.f);
    const float YawSteady = A->GetActorRotation().Yaw;
    for (int32 i = 0; i < 10; ++i) A->SimulateSailing(.1f);
    TestTrue(TEXT("Centred rudder holds course"), FMath::IsNearlyEqual(A->GetActorRotation().Yaw, YawSteady, .01f));

    // Dropping the anchor under way drags the ship to a stop, whatever the sails say.
    TestTrue(TEXT("Under way before anchoring"), A->GetSpeed() > 100.f);
    TestTrue(TEXT("Drop anchor"), A->SetAnchored(C, true));
    for (int32 Step = 0; Step < 400 && !A->IsChainTaut(); ++Step) A->SimulateSailing(.05f);
    TestTrue(TEXT("The dropped anchor chain becomes taut"), A->IsChainTaut());
    A->SimulateSailing(.05f);
    TestEqual(TEXT("The taut anchor chain stops the ship"), A->GetSpeed(), 0.f);
    const FVector Moored = A->GetActorLocation();
    for (int32 i = 0; i < 20; ++i) A->SimulateSailing(.1f);
    // It does not drift across the water; the swell only bobs it in place.
    TestTrue(TEXT("An anchored ship stays put"), FVector::Dist2D(Moored, A->GetActorLocation()) < 1.f);
    TestTrue(TEXT("The swell bobs it gently"), FMath::Abs(Moored.Z - A->GetActorLocation().Z) <= 2.f * AEWShip::SwellRise * 2.f + .1f);
    TestTrue(TEXT("Raise anchor again"), A->SetAnchored(C, false));

    // Another hull ahead stops the ship instead of passing through it.
    A->SetActorLocationAndRotation(Blocker->GetActorLocation() - FVector(1400, 0, 0), FRotator::ZeroRotator);
    bool bGotGoing = false;
    for (int32 i = 0; i < 300; ++i)
    {
        A->SimulateSailing(.1f);
        bGotGoing |= A->GetSpeed() > 100.f;
        if (bGotGoing && A->GetSpeed() == 0.f) break;
    }
    TestTrue(TEXT("The ship got under way toward the blocker"), bGotGoing);
    TestEqual(TEXT("Collision stops the ship"), A->GetSpeed(), 0.f);
    TestTrue(TEXT("Hulls do not overlap"), Blocker->GetActorLocation().X - A->GetActorLocation().X >= 2.f * Def->HullExtent.X - 5.f);
    // A pinned ship can always turn away: the rudder keeps a little bite with no way on.
    const float PinnedYaw = A->GetActorRotation().Yaw;
    TestTrue(TEXT("Rudder over while pinned"), A->SetRudder(C, -1.f));
    for (int32 i = 0; i < 20; ++i) A->SimulateSailing(.1f);
    TestTrue(TEXT("A pinned ship turns away from the obstacle"), A->GetActorRotation().Yaw < PinnedYaw - 5.f);

    // A dead helmsman is released by the ship.
    C->GetSurvivalComponent()->ApplyDamage(100000.f);
    A->Tick(.05f);
    TestNull(TEXT("Dead helmsman released"), A->GetHelmsman());
    TestNull(TEXT("Dead survivor no longer at a helm"), C->GetHelmShip());

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipWeightTest, "Elitewake.Ships.WeightAndOverload",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipWeightTest::RunTest(const FString& Parameters)
{
    using namespace EWShipTest;
    auto* Def = NewObject<UEWShipDefinition>(GetTransientPackage());
    Def->ShipId = TEXT("TestSloop");
    Def->WeightCapacity = 1000.f;
    Def->Mounts = {Mount(TEXT("Helm"), EEWShipMountType::Helm, FVector(-250, 0, 130)),
                   Mount(TEXT("Mainsail"), EEWShipMountType::Sail, FVector(0, 0, 130), EEWSailSize::Medium)};
    UEWItemDefinition* HeavyHelm = Item(TEXT("TestHeavyHelm"), EEWShipMountType::Helm);
    HeavyHelm->UnitWeight = 100.f;
    UEWItemDefinition* Sail = Item(TEXT("TestSail"), EEWShipMountType::Sail, EEWSailSize::Medium);
    UEWItemDefinition* Ballast = Item(TEXT("TestBallast"));
    Ballast->UnitWeight = 10.f; Ballast->MaxStackSize = 100;

    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    auto* CharClass = LoadClass<AEWCharacter>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    auto* PCClass = LoadClass<AEWPlayerController>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.BP_ThirdPersonPlayerController_C"));
    if (!TestNotNull(TEXT("Survivor class"), CharClass) || !TestNotNull(TEXT("Controller class"), PCClass))
    { World->DestroyWorld(false); return false; }
    auto* Ship = World->SpawnActorDeferred<AEWShip>(AEWShip::StaticClass(), FTransform::Identity);
    Ship->Definition = Def;
    Ship->FinishSpawning(FTransform::Identity);
    FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* C = World->SpawnActor<AEWCharacter>(CharClass, FVector(-120, 0, 186), FRotator::ZeroRotator, Params);
    auto* PC = World->SpawnActor<AEWPlayerController>(PCClass);
    PC->Possess(C);
    UEWInventoryComponent* Hold = Ship->GetCargo();

    // Fittings count toward the load; what a survivor carries does not.
    C->GetInventoryComponent()->AddItem(HeavyHelm, 1);
    C->GetInventoryComponent()->AddItem(Sail, 1);
    C->GetInventoryComponent()->AddItem(Ballast, 50);
    TestEqual(TEXT("Helm installs"), Ship->InstallFitting(C, TEXT("Helm")), EEWFittingResult::Installed);
    TestEqual(TEXT("Sail installs"), Ship->InstallFitting(C, TEXT("Mainsail")), EEWFittingResult::Installed);
    Ship->UpdateLoad(0.f);
    TestTrue(TEXT("Load counts fittings, not carried ballast"), FMath::IsNearlyEqual(Ship->GetLoad(), 100.f));

    // Speed falls off past half capacity.
    Hold->AddItem(Ballast, 30);                                 // 400 kg total
    TestTrue(TEXT("Under half load: full speed"), FMath::IsNearlyEqual(Ship->GetLoadSpeedFactor(), 1.f));
    Hold->AddItem(Ballast, 30);                                 // 700 kg
    TestTrue(TEXT("At 70% load the ship is slower"), FMath::IsNearlyEqual(Ship->GetLoadSpeedFactor(), .84f, .001f));

    // Overloaded: slower still, with a countdown to lighten the ship.
    Hold->AddItem(Ballast, 40);                                 // 1100 kg
    Ship->UpdateLoad(0.f);
    TestTrue(TEXT("Over capacity is overloaded"), Ship->IsOverloaded());
    TestTrue(TEXT("Overloaded speed factor"), FMath::IsNearlyEqual(Ship->GetLoadSpeedFactor(), .4f));
    TestEqual(TEXT("Countdown starts full"), Ship->GetOverloadSecondsLeft(), AEWShip::OverloadGraceSeconds);
    Ship->UpdateLoad(30.f);
    TestFalse(TEXT("Not swamped within the grace period"), Ship->IsSwamped());
    TestTrue(TEXT("Countdown runs"), FMath::IsNearlyEqual(Ship->GetOverloadSecondsLeft(), AEWShip::OverloadGraceSeconds - 30.f));
    Ship->UpdateLoad(31.f);
    TestTrue(TEXT("Swamped once the grace period runs out"), Ship->IsSwamped());

    // Lightening the ship below capacity frees it and resets the countdown.
    Hold->RemoveItem(Ballast, 20);                              // 900 kg
    Ship->UpdateLoad(0.f);
    TestFalse(TEXT("No longer overloaded"), Ship->IsOverloaded());
    TestFalse(TEXT("No longer swamped"), Ship->IsSwamped());
    TestEqual(TEXT("Countdown reset"), Ship->GetOverloadSecondsLeft(), AEWShip::OverloadGraceSeconds);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipBoardingTest, "Elitewake.Ships.BoardingAndAnchor",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipBoardingTest::RunTest(const FString& Parameters)
{
    using namespace EWShipTest;
    auto* Def = NewObject<UEWShipDefinition>(GetTransientPackage());
    Def->ShipId = TEXT("TestSloop");
    Def->Mounts = {Mount(TEXT("Helm"), EEWShipMountType::Helm, FVector(-250, 0, 130))};
    Def->BoardingPoints = {FVector(-100, -175, -10), FVector(-100, 175, -10)};

    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    auto* CharClass = LoadClass<AEWCharacter>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    auto* PCClass = LoadClass<AEWPlayerController>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.BP_ThirdPersonPlayerController_C"));
    if (!TestNotNull(TEXT("Survivor class"), CharClass) || !TestNotNull(TEXT("Controller class"), PCClass))
    { World->DestroyWorld(false); return false; }
    auto* Ship = World->SpawnActorDeferred<AEWShip>(AEWShip::StaticClass(), FTransform::Identity);
    Ship->Definition = Def;
    Ship->FinishSpawning(FTransform::Identity);
    FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    // A swimmer alongside the starboard ladder, head just above the water.
    auto* C = World->SpawnActor<AEWCharacter>(CharClass, FVector(-100, 330, -40), FRotator::ZeroRotator, Params);
    auto* PC = World->SpawnActor<AEWPlayerController>(PCClass);
    PC->Possess(C);
    auto AimAtLadder = [&](int32 Index)
    {
        FVector Eye; FRotator Unused;
        C->GetActorEyesViewPoint(Eye, Unused);
        PC->SetControlRotation((Ship->GetBoardingPointWorld(Index) - Eye).Rotation());
    };

    TestFalse(TEXT("A swimmer is not aboard"), Ship->IsAboard(C));
    AimAtLadder(1);
    TestEqual(TEXT("Aim finds the starboard ladder"), Ship->FindAimedBoardingPoint(C), 1);
    TestEqual(TEXT("Ladder aim is not a mount"), Ship->FindAimedMount(C), FName());
    TestTrue(TEXT("A swimmer can climb the ladder"), Ship->CanInteract_Implementation(C));

    // Something standing on the preferred landing spot makes the climber use a clear alternate rather than overlap it.
    auto* Other = World->SpawnActor<AEWCharacter>(CharClass,
        FVector(-100, Def->HullExtent.Y - 70.f, Def->GetDeckHeight() + C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 2.f),
        FRotator::ZeroRotator, Params);
    TestTrue(TEXT("A blocked preferred landing uses a clear alternate"), Ship->ClimbAboard(C, 1));
    C->SetActorLocation(FVector(-100, 330, -40), false, nullptr, ETeleportType::TeleportPhysics);
    C->GetCharacterMovement()->SetMovementMode(MOVE_Swimming);
    Other->Destroy();
    AimAtLadder(1);

    TestTrue(TEXT("Interact takes hold of the ladder"), Ship->Interact_Implementation(C) && C->GetLadderShip() == Ship);
    TestFalse(TEXT("Hanging on the ladder is not aboard"), Ship->IsAboard(C));
    TestFalse(TEXT("No second hold while on the ladder"), Ship->CanInteract_Implementation(C));
    // Climbing up: at the head of the ladder the survivor steps onto the deck by themselves.
    C->SetLadderArrowInput(1.f);
    C->ServerLadderClimb_Implementation(1);
    for (int32 Step = 0; Step < 50 && C->IsOnLadder(); ++Step) C->Tick(.1f);
    C->SetLadderArrowInput(0.f);
    TestFalse(TEXT("The climber has left the ladder at its head"), C->IsOnLadder());
    const FVector Local = Ship->GetActorTransform().InverseTransformPosition(C->GetActorLocation());
    TestTrue(TEXT("The survivor lands on the deck, starboard side"), Local.Z > Def->GetDeckHeight() && Local.Y > 0.f && Local.Y < Def->HullExtent.Y);
    TestTrue(TEXT("The survivor is aboard"), Ship->IsAboard(C));
    TestFalse(TEXT("No climb prompt once aboard"), Ship->ClimbAboard(C, 0));

    // The anchor capstan on deck, worked with the ordinary interaction.
    C->SetActorLocation(Ship->GetActorTransform().TransformPosition(
        FVector(Def->AnchorPoint.X - 120.f, Def->AnchorPoint.Y, Def->GetDeckHeight() + C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 2.f)));
    {
        FVector Eye; FRotator Unused;
        C->GetActorEyesViewPoint(Eye, Unused);
        PC->SetControlRotation((Ship->GetAnchorPointWorld() - Eye).Rotation());
    }
    TestTrue(TEXT("Aim finds the capstan"), Ship->IsAimingAtAnchor(C));
    TestTrue(TEXT("The capstan can be worked"), Ship->CanInteract_Implementation(C));
    TestTrue(TEXT("The ship starts anchored"), Ship->IsAnchored());
    TestTrue(TEXT("Interact raises the anchor"), Ship->Interact_Implementation(C) && !Ship->IsAnchored());
    TestTrue(TEXT("Interact drops it again"), Ship->Interact_Implementation(C) && Ship->IsAnchored());
    TestEqual(TEXT("A boat without a capstan takes the short hold"), Ship->GetHoldDurationFor_Implementation(C), AEWShip::FittingHoldSeconds);
    Def->CapstanMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT("/Engine/BasicShapes/Cylinder.Cylinder")));
    TestEqual(TEXT("Working a capstan takes the longer hold"), Ship->GetHoldDurationFor_Implementation(C), AEWShip::AnchorHoldSeconds);
    Ship->HoldChanged_Implementation(C, true);
    TestTrue(TEXT("Holding at the capstan makes the survivor its worker"), Ship->GetCapstanWorker() == C);
    Ship->HoldChanged_Implementation(nullptr, true);
    TestTrue(TEXT("Only a survivor at the capstan can take it over"), Ship->GetCapstanWorker() == C);
    Ship->HoldChanged_Implementation(C, false);
    TestNull(TEXT("Letting go leaves the capstan"), Ship->GetCapstanWorker());
    Def->CapstanMesh.Reset();

    // The cargo hold: sized by the definition, opened at the hatch, and reachable only aboard or nearby.
    TestEqual(TEXT("Hold size comes from the definition"), Ship->GetCargo()->GetMaxSlotCount(), Def->CargoSlots);
    C->SetActorLocation(Ship->GetActorTransform().TransformPosition(
        FVector(Def->CargoHatchPoint.X - 120.f, Def->CargoHatchPoint.Y, Def->GetDeckHeight() + C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 2.f)));
    {
        FVector Eye; FRotator Unused;
        C->GetActorEyesViewPoint(Eye, Unused);
        PC->SetControlRotation((Ship->GetCargoHatchWorld() - Eye).Rotation());
    }
    TestTrue(TEXT("Aim finds the cargo hatch"), Ship->IsAimingAtCargoHatch(C));
    TestTrue(TEXT("Aboard survivors can use the hold"), Ship->CanAccessCargo(C));
    TestTrue(TEXT("Interact at the hatch opens the hold"), Ship->Interact_Implementation(C));
    auto* Plank = Item(TEXT("TestPlank"));
    Plank->MaxStackSize = 50;
    C->GetInventoryComponent()->AddItem(Plank, 30);
    const int32 PlankIndex = C->GetInventoryComponent()->GetInventoryEntries().IndexOfByPredicate([&](const FEWInventoryEntry& E) { return E.ItemDefinition == Plank; });
    PC->ServerTransferContainerItem_Implementation(Ship, true, PlankIndex, 30);
    TestEqual(TEXT("The controller request stores the stack"), Ship->GetCargo()->GetItemCount(Plank), 30);
    PC->ServerTransferContainerItem_Implementation(Ship, false, 0, 30);
    TestEqual(TEXT("The controller request takes it back"), C->GetInventoryComponent()->GetItemCount(Plank), 30);
    C->SetActorLocation(FVector(3000, 3000, -40));
    TestFalse(TEXT("A survivor far from the ship cannot reach the hold"), Ship->CanAccessCargo(C));
    PC->ServerTransferContainerItem_Implementation(Ship, true, 0, 30);
    TestEqual(TEXT("Out of reach, nothing is stored"), Ship->GetCargo()->GetItemCount(Plank), 0);

    // Dead survivors cannot climb.
    C->SetActorLocation(FVector(-100, -330, -40));
    C->GetSurvivalComponent()->ApplyDamage(100000.f);
    TestFalse(TEXT("A dead survivor cannot climb"), Ship->ClimbAboard(C, 0));
    TestFalse(TEXT("A dead survivor cannot work the anchor"), Ship->SetAnchored(C, false));

    World->DestroyWorld(false);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipBuiltInFittingTest, "Elitewake.Ships.BuiltInFittings",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipBuiltInFittingTest::RunTest(const FString& Parameters)
{
    using namespace EWShipTest;

    // A paddled raft whose paddles are part of the hull: no sails at all.
    UEWItemDefinition* Oar = Item(TEXT("TestPaddles"), EEWShipMountType::Helm);
    auto* Def = NewObject<UEWShipDefinition>(GetTransientPackage());
    Def->ShipId = TEXT("TestRaft");
    Def->bPaddled = true;
    Def->Mounts = {Mount(TEXT("Helm"), EEWShipMountType::Helm, FVector(-150, 0, 130)),
                   Mount(TEXT("Sail"), EEWShipMountType::Sail, FVector(0, 0, 130), EEWSailSize::Small)};
    FEWInstalledFitting BuiltIn; BuiltIn.MountId = TEXT("Helm"); BuiltIn.Item = Oar;
    Def->BuiltInFittings = {BuiltIn};
    TestTrue(TEXT("Valid definition"), Def->Validate().IsEmpty());
    auto* Bad = DuplicateObject(Def, GetTransientPackage());
    Bad->BuiltInFittings[0].MountId = TEXT("Sail");
    TestFalse(TEXT("A built-in fitting must suit its mount"), Bad->Validate().IsEmpty());

    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    auto* CharClass = LoadClass<AEWCharacter>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    auto* PCClass = LoadClass<AEWPlayerController>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.BP_ThirdPersonPlayerController_C"));
    if (!TestNotNull(TEXT("Survivor class"), CharClass) || !TestNotNull(TEXT("Controller class"), PCClass))
    { World->DestroyWorld(false); return false; }
    auto* Ship = World->SpawnActorDeferred<AEWShip>(AEWShip::StaticClass(), FTransform::Identity);
    Ship->Definition = Def;
    Ship->FinishSpawning(FTransform::Identity);
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    TestEqual(TEXT("The paddles are fitted when the raft starts"), Ship->GetFitting(TEXT("Helm")), Oar);
    TestTrue(TEXT("A built-in helm steers"), Ship->HasFittingOfType(EEWShipMountType::Helm));

    FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* C = World->SpawnActor<AEWCharacter>(CharClass, FVector(-60, 0, 186), FRotator::ZeroRotator, Params);
    auto* PC = World->SpawnActor<AEWPlayerController>(PCClass);
    PC->Possess(C);
    TestEqual(TEXT("A built-in fitting cannot be removed"), Ship->RemoveFitting(C, TEXT("Helm")), EEWFittingResult::NotAllowed);
    TestEqual(TEXT("The paddles stay on the raft"), Ship->GetFitting(TEXT("Helm")), Oar);
    TestEqual(TEXT("Nothing went to the inventory"), C->GetInventoryComponent()->GetItemCount(Oar), 0);
    TestTrue(TEXT("The built-in helm can be taken"), Ship->TakeHelm(C));
    // Paddling: no sail fitted, yet a hard stroke reaches full speed and an easy one half, wind or no wind.
    TestTrue(TEXT("Raise the anchor"), Ship->SetAnchored(C, false));
    TestEqual(TEXT("Resting paddles do not move the raft"), Ship->ComputeTargetSpeed(), 0.f);
    TestTrue(TEXT("Easy stroke"), Ship->StepSails(C, 1));
    TestEqual(TEXT("An easy stroke is half speed without any sail"), Ship->ComputeTargetSpeed(), Def->TopSpeed * .5f);
    TestTrue(TEXT("Hard stroke"), Ship->StepSails(C, 1));
    TestEqual(TEXT("A hard stroke is full speed"), Ship->ComputeTargetSpeed(), Def->TopSpeed);
    const FVector Start = Ship->GetActorLocation();
    for (int32 i = 0; i < 20; ++i) Ship->SimulateSailing(.1f);
    TestTrue(TEXT("Paddling moves the raft"), FVector::Dist(Start, Ship->GetActorLocation()) > 50.f);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipHullDamageTest, "Elitewake.Ships.HullDamage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipHullDamageTest::RunTest(const FString& Parameters)
{
    using namespace EWShipTest;

    auto* Def = NewObject<UEWShipDefinition>(GetTransientPackage());
    Def->ShipId = TEXT("TestHull");
    Def->HullHealth = 1000.f;
    Def->Mounts = {Mount(TEXT("Helm"), EEWShipMountType::Helm, FVector(-250, 0, 130))};
    TestTrue(TEXT("Valid definition"), Def->Validate().IsEmpty());

    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    auto* Ship = World->SpawnActorDeferred<AEWShip>(AEWShip::StaticClass(), FTransform::Identity);
    Ship->Definition = Def;
    Ship->FinishSpawning(FTransform::Identity);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    TestEqual(TEXT("A whole hull starts at its definition's health"), Ship->GetHullHealth(), Def->HullHealth);
    TestEqual(TEXT("Max hull health matches the definition"), Ship->GetMaxHullHealth(), Def->HullHealth);
    TestEqual(TEXT("A whole hull has no holes"), Ship->GetHoleCount(), 0);

    const FVector Where = Ship->GetActorLocation() + FVector(0, Def->HullExtent.Y, 0);
    Ship->TakeRoundShot(Where, FVector(0, 1, 0), nullptr);
    TestEqual(TEXT("One round shot takes RoundShotDamage"), Ship->GetHullHealth(), Def->HullHealth - AEWShip::RoundShotDamage);
    TestEqual(TEXT("A hole is recorded"), Ship->GetHoleCount(), 1);
    const FEWHullHole Hole = Ship->GetHole(0);
    TestTrue(TEXT("The hole sits on the struck side"), FMath::Abs(Hole.Local.Y - Def->HullExtent.Y) < 1.f);
    TestTrue(TEXT("The hole faces the strike"), Hole.Normal.Equals(FVector(0, 1, 0), .01f));

    const float After = Ship->GetHullHealth();
    Ship->TakeRoundShot(Where, FVector(0, 1, 0), nullptr);
    TestEqual(TEXT("A second shot takes the same damage again"), Ship->GetHullHealth(), After - AEWShip::RoundShotDamage);
    TestEqual(TEXT("A second hole is recorded"), Ship->GetHoleCount(), 2);

    World->DestroyWorld(false);
    return true;
}

#endif
