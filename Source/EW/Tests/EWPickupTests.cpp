#if WITH_DEV_AUTOMATION_TESTS
#include "EWPickup.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWPickupTest, "Elitewake.Inventory.PickupValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWPickupTest::RunTest(const FString& Parameters)
{
    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    UClass* Class = LoadClass<AEWCharacter>(nullptr, TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    if (!TestNotNull(TEXT("Player class"), Class)) { World->DestroyWorld(false); return false; }
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AEWCharacter* Character = World->SpawnActor<AEWCharacter>(Class, FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    APlayerController* Controller = World->SpawnActor<APlayerController>();
    Controller->Possess(Character); Controller->SetControlRotation(FRotator::ZeroRotator);
    FVector Eye; FRotator Rotation; Character->GetActorEyesViewPoint(Eye, Rotation);
    UEWItemDefinition* Item = NewObject<UEWItemDefinition>(); Item->MaxStackSize = 250; Item->UnitWeight = .1f;
    UEWInventoryComponent* Inventory = Character->GetInventoryComponent();
    auto Pickup = [&]() { AEWPickup* P = World->SpawnActor<AEWPickup>(Eye + FVector(150,0,0), FRotator::ZeroRotator); P->ItemDefinition = Item; P->Quantity = 10; return P; };
    AEWPickup* P = Pickup();
    TestEqual(TEXT("Aim finds world stack"), AEWPickup::FindTarget(Character), P);
    P->SetActorLocation(Eye + FVector(400,0,0));
    TestEqual(TEXT("Out of range rejected"), P->TryPickup(Character), 0);
    P->SetActorLocation(Eye + FVector(150,0,0));
    Controller->SetControlRotation(FRotator(0,90,0));
    TestEqual(TEXT("Looking away rejected"), P->TryPickup(Character), 0);
    Controller->SetControlRotation(FRotator::ZeroRotator);
    AActor* Wall = World->SpawnActor<AActor>();
    UBoxComponent* Box = NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(10,100,100)); Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent();
    Wall->SetActorLocation(Eye + FVector(75,0,0));
    TestEqual(TEXT("Wall blocks remote pickup"), P->TryPickup(Character), 0); Wall->Destroy();
    AActor* OtherOwner = World->SpawnActor<AActor>(); P->SetOwner(OtherOwner);
    TestEqual(TEXT("Foreign ownership rejected"), P->TryPickup(Character), 0); P->SetOwner(nullptr);
    Controller->UnPossess(); TestEqual(TEXT("Unpossessed character rejected"), P->TryPickup(Character), 0);
    Controller->Possess(Character);
    Inventory->AddItem(Item, 5997);
    TestEqual(TEXT("Partial pickup only fills available capacity"), P->TryPickup(Character), 3);
    TestEqual(TEXT("Remainder stays in world"), P->Quantity, 7);
    TestEqual(TEXT("Full inventory rejects remainder"), P->TryPickup(Character), 0);
    Inventory->RemoveItem(Item, 7);
    TestEqual(TEXT("Remaining units accepted"), P->TryPickup(Character), 7);
    TestTrue(TEXT("Exhausted stack destroyed"), P->IsActorBeingDestroyed());
    TestEqual(TEXT("Repeated transfer cannot duplicate"), P->TryPickup(Character), 0);
    TestEqual(TEXT("Final count conserved"), Inventory->GetItemCount(Item), 6000);
    World->DestroyWorld(false); return true;
}
#endif
