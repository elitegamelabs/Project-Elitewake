#if WITH_DEV_AUTOMATION_TESTS
#include "Gathering/EWHandGatherable.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWHandGatheringTest, "Elitewake.Gathering.HandResources",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWHandGatheringTest::RunTest(const FString& Parameters)
{
    const auto Values=UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    UClass* PawnClass=LoadClass<AEWCharacter>(nullptr,TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    if (!TestNotNull(TEXT("Player class"),PawnClass)) { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return false; }
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Pawn=World->SpawnActor<AEWCharacter>(PawnClass,FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    auto* PC=World->SpawnActor<APlayerController>(); PC->Possess(Pawn); PC->SetControlRotation(FRotator::ZeroRotator);
    Pawn->GetCharacterMovement()->DisableMovement();
    FVector Eye; FRotator Rotation; Pawn->GetActorEyesViewPoint(Eye,Rotation);
    auto* Item=NewObject<UEWItemDefinition>(); Item->ItemId=TEXT("Test.Fiber"); Item->Category=EEWItemCategory::Resource;
    Item->MaxStackSize=250; Item->UnitWeight=.01f;
    auto* Node=World->SpawnActor<AEWHandGatherable>(Eye+FVector(150,0,0),FRotator::ZeroRotator);
    Node->ItemDefinition=Item; Node->Quantity=10;
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    auto* Inventory=Pawn->GetInventoryComponent();
    TestTrue(TEXT("Hand node uses shared pickup targeting"),FEWInteractionTargeting::FindTarget(Pawn)==Node);
    Item->Category=EEWItemCategory::Weapon;
    TestFalse(TEXT("Invalid resource category is ineligible"),IEWInteractable::Execute_CanInteract(Node,Pawn));
    TestEqual(TEXT("Invalid category cannot transfer directly"),Node->TryPickup(Pawn),0); Item->Category=EEWItemCategory::Resource;
    Pawn->GetSurvivalComponent()->ApplyDamage(100);
    TestEqual(TEXT("Dead survivor cannot gather"),Node->TryPickup(Pawn),0); Pawn->GetSurvivalComponent()->RestoreHealth(100);
    PC->SetControlRotation(FRotator(0,90,0)); TestEqual(TEXT("Un-aimed node rejected"),Node->TryPickup(Pawn),0); PC->SetControlRotation(FRotator::ZeroRotator);
    auto* Wall=World->SpawnActor<AActor>(); auto* Box=NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box);
    Box->SetBoxExtent(FVector(10,100,100)); Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent(); Wall->SetActorLocation(Eye+FVector(75,0,0));
    TestEqual(TEXT("Obstructed gather rejected"),Node->TryPickup(Pawn),0); Wall->Destroy();
    auto* Foreign=World->SpawnActor<AActor>(); Node->SetOwner(Foreign);
    TestEqual(TEXT("Foreign-owned gather rejected"),Node->TryPickup(Pawn),0); Node->SetOwner(nullptr); Foreign->Destroy();
    Node->SetActorLocation(Eye+FVector(400,0,0)); TestEqual(TEXT("Distant gather rejected"),Node->TryPickup(Pawn),0); Node->SetActorLocation(Eye+FVector(150,0,0));
    Inventory->AddItem(Item,5997);
    TestTrue(TEXT("Live resource is eligible through interface"),IEWInteractable::Execute_CanInteract(Node,Pawn));
    TestTrue(TEXT("Interface dispatch uses specialized gather path"),IEWInteractable::Execute_Interact(Node,Pawn));
    TestEqual(TEXT("Partial gather fills only available capacity"),Inventory->GetItemCount(Item),6000);
    TestEqual(TEXT("Unaccepted units remain in node"),Node->Quantity,7);
    TestEqual(TEXT("Full inventory does not consume yield"),Node->TryPickup(Pawn),0);
    Inventory->RemoveItem(Item,7);
    TestEqual(TEXT("Remainder transfers once"),Node->TryPickup(Pawn),7);
    TestTrue(TEXT("Depleted node destroyed"),Node->IsActorBeingDestroyed());
    TestEqual(TEXT("Repeated gather cannot duplicate"),Node->TryPickup(Pawn),0);
    TestEqual(TEXT("Total resource quantity conserved"),Inventory->GetItemCount(Item),6000);
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return true;
}
#endif
