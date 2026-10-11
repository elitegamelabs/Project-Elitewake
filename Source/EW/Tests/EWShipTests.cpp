#if WITH_DEV_AUTOMATION_TESTS
#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWPlayerController.h"
#include "EWSurvivalComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

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
#endif
