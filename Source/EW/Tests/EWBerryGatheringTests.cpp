#if WITH_DEV_AUTOMATION_TESTS
#include "Gathering/EWHandGatherable.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWBerryTest,"Elitewake.Gathering.Berries",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWBerryTest::RunTest(const FString& Parameters)
{
    const auto Values=UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    UClass* PawnClass=LoadClass<AEWCharacter>(nullptr,TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    if (!TestNotNull(TEXT("Pawn class"),PawnClass)) { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return false; }
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Pawn=World->SpawnActor<AEWCharacter>(PawnClass,FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    auto* PC=World->SpawnActor<APlayerController>(); PC->Possess(Pawn); PC->SetControlRotation(FRotator::ZeroRotator); Pawn->GetCharacterMovement()->DisableMovement();
    FVector Eye; FRotator Rotation; Pawn->GetActorEyesViewPoint(Eye,Rotation);
    auto* Berry=NewObject<UEWItemDefinition>(); Berry->ItemId=TEXT("Test.Berry"); Berry->Category=EEWItemCategory::Consumable; Berry->FoodKind=EEWFoodKind::Berry; Berry->MaxStackSize=500;
    auto* Node=World->SpawnActor<AEWHandGatherable>(Eye+FVector(150,0,0),FRotator::ZeroRotator); Node->ItemDefinition=Berry; Node->Quantity=10;
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    auto* Inventory=Pawn->GetInventoryComponent();
    TestEqual(TEXT("Resource node cannot gather consumables"),Node->TryPickup(Pawn),0);
    Node->GatheringKind=EEWHandGatheringKind::Berries;
    Berry->FoodKind=EEWFoodKind::None; TestEqual(TEXT("Nonberry consumable rejected"),Node->TryPickup(Pawn),0); Berry->FoodKind=EEWFoodKind::Berry;
    Berry->Category=EEWItemCategory::Resource; TestEqual(TEXT("Berry must be food consumable"),Node->TryPickup(Pawn),0); Berry->Category=EEWItemCategory::Consumable;
    Inventory->AddItem(Berry,11997);
    TestTrue(TEXT("Interface dispatch gathers berries"),IEWInteractable::Execute_Interact(Node,Pawn));
    TestEqual(TEXT("24 food stacks accept 12000"),Inventory->GetItemCount(Berry),12000); TestEqual(TEXT("Partial capacity conserves stock"),Node->Quantity,7);
    TestEqual(TEXT("Full inventory preserves bush"),Node->TryPickup(Pawn),0);
    Inventory->RemoveItem(Berry,7);
    Pawn->GetSurvivalComponent()->ApplyDamage(100); TestEqual(TEXT("Dead survivor cannot gather"),Node->TryPickup(Pawn),0); Pawn->GetSurvivalComponent()->RestoreHealth(100);
    PC->SetControlRotation(FRotator(0,90,0)); TestEqual(TEXT("Unaimed gather rejected"),Node->TryPickup(Pawn),0); PC->SetControlRotation(FRotator::ZeroRotator);
    TestEqual(TEXT("Freed capacity takes exact remainder"),Node->TryPickup(Pawn),7); TestTrue(TEXT("Depletion removes bush"),Node->IsActorBeingDestroyed());
    TestEqual(TEXT("No repeated depleted grant"),Node->TryPickup(Pawn),0);
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return true;
}
#endif
