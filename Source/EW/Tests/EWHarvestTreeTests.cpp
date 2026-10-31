#if WITH_DEV_AUTOMATION_TESTS
#include "Gathering/EWHarvestTree.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWHarvestTreeTest,"Elitewake.Gathering.HatchetTree",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWHarvestTreeTest::RunTest(const FString& Parameters)
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
    auto Resource=[](const TCHAR* Id){ auto* Item=NewObject<UEWItemDefinition>(); Item->ItemId=Id; Item->Category=EEWItemCategory::Resource; Item->MaxStackSize=250; return Item; };
    auto* Wood=Resource(TEXT("Test.Wood")); auto* Thatch=Resource(TEXT("Test.Thatch"));
    auto* Tool=Resource(TEXT("Test.Hatchet")); Tool->Category=EEWItemCategory::Tool; Tool->EquipmentSlot=EEWEquipmentSlot::MainHand; Tool->GatheringTool=EEWGatheringTool::Hatchet; Tool->MaxStackSize=1;
    auto* Tree=World->SpawnActor<AEWHarvestTree>(Eye+FVector(150,0,0),FRotator::ZeroRotator); Tree->Wood=Wood; Tree->Thatch=Thatch;
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    auto* Inventory=Pawn->GetInventoryComponent(); auto* Equipment=Pawn->GetEquipmentComponent();
    TestEqual(TEXT("Bare hands gated until injuries exist"),Tree->TryHarvest(Pawn),0);
    Inventory->AddItem(Tool,1); TestEqual(TEXT("Inventory-only tool is insufficient"),Tree->TryHarvest(Pawn),0);
    TestTrue(TEXT("Owned tool equips"),Equipment->EquipItem(Tool,EEWEquipmentSlot::MainHand)==EEWEquipmentResult::Success);
    TestFalse(TEXT("Interact cannot harvest"),IEWInteractable::Execute_Interact(Tree,Pawn));
    TestEqual(TEXT("Equipped hatchet strike yields both resources"),Tree->TryHarvest(Pawn),4);
    TestEqual(TEXT("Wood stock decreases only accepted units"),Tree->WoodRemaining,9); TestEqual(TEXT("Thatch stock decreases"),Tree->ThatchRemaining,3);
    Tool->GatheringTool=EEWGatheringTool::None; TestEqual(TEXT("Wrong equipped tool rejected"),Tree->TryHarvest(Pawn),0); Tool->GatheringTool=EEWGatheringTool::Hatchet;
    PC->SetControlRotation(FRotator(0,90,0)); TestEqual(TEXT("Aim rejected"),Tree->TryHarvest(Pawn),0); PC->SetControlRotation(FRotator::ZeroRotator);
    Tree->SetActorLocation(Eye+FVector(400,0,0)); TestEqual(TEXT("Range rejected"),Tree->TryHarvest(Pawn),0); Tree->SetActorLocation(Eye+FVector(150,0,0));
    Pawn->GetSurvivalComponent()->ApplyDamage(100); TestEqual(TEXT("Dead survivor rejected"),Tree->TryHarvest(Pawn),0); Pawn->GetSurvivalComponent()->RestoreHealth(100);
    Inventory->RemoveItem(Thatch,1); Inventory->AddItem(Wood,5996); // 24 wood stacks; one unit free, no free slot for thatch.
    TestEqual(TEXT("Partial dual-resource strike accepts only wood that fits"),Tree->TryHarvest(Pawn),1);
    TestEqual(TEXT("Partial stock conserves rejected wood"),Tree->WoodRemaining,8); TestEqual(TEXT("Rejected thatch remains"),Tree->ThatchRemaining,3);
    TestEqual(TEXT("Full inventory rejects without stock loss"),Tree->TryHarvest(Pawn),0);
    Inventory->RemoveItem(Wood,100000);
    while(!Tree->IsFelled() && !Tree->IsActorBeingDestroyed()) Tree->TryHarvest(Pawn);
    TestTrue(TEXT("Cutting the last wood tips the tree over instead of removing it at once"),Tree->IsFelled() && !Tree->IsActorBeingDestroyed());
    Tree->Tick(Tree->FallDuration);
    TestTrue(TEXT("A tree that just landed lies still and solid"),!Tree->IsFading() && !Tree->IsActorBeingDestroyed());
    Tree->Tick(Tree->RemoveDelay);
    TestTrue(TEXT("After lying a while the felled tree starts to fade instead of vanishing"),Tree->IsFading() && !Tree->IsActorBeingDestroyed());
    Tree->Tick(Tree->FadeSeconds+.1f);
    TestEqual(TEXT("All remaining wood conserved"),Inventory->GetItemCount(Wood),8); TestEqual(TEXT("All remaining thatch conserved"),Inventory->GetItemCount(Thatch),3);
    TestEqual(TEXT("Destroyed tree cannot replay"),Tree->TryHarvest(Pawn),0);

    auto* FelledTree=World->SpawnActor<AEWHarvestTree>(FVector(1000,0,0),FRotator::ZeroRotator,Spawn);
    FelledTree->Wood=Wood; FelledTree->Thatch=Thatch; FelledTree->WoodRemaining=7; FelledTree->ThatchRemaining=2;
    FelledTree->BlockerRadius=52.f; FelledTree->BlockerHalfHeight=220.f;
    FelledTree->OnConstruction(FTransform(FRotator::ZeroRotator,FelledTree->GetActorLocation()));
    TestTrue(TEXT("Configured standing tree blocks movement"),FelledTree->Blocker->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics);
    TestTrue(TEXT("Authority can fell toward a horizontal direction"),FelledTree->Fell(FVector::ForwardVector));
    TestTrue(TEXT("Felled state is exposed for replication"),FelledTree->IsFelled());
    TestTrue(TEXT("Actor movement replication enabled on fall"),FelledTree->IsReplicatingMovement());
    TestEqual(TEXT("Felling preserves remaining wood"),FelledTree->WoodRemaining,7);
    TestEqual(TEXT("Felling preserves remaining thatch"),FelledTree->ThatchRemaining,2);
    TestFalse(TEXT("Second fall cannot restart the fall"),FelledTree->Fell(FVector::RightVector));
    FelledTree->Tick(FelledTree->FallDuration*.5f);
    TestTrue(TEXT("Tree rotates progressively while falling"),FelledTree->GetActorUpVector().X>.2f && FelledTree->GetActorUpVector().X<.99f);
    FelledTree->Tick(FelledTree->FallDuration);
    TestTrue(TEXT("Tree settles horizontally in the requested direction"),FVector::DotProduct(FelledTree->GetActorUpVector(),FVector::ForwardVector)>.99f);
    TestTrue(TEXT("Blocker turns with the fallen trunk"),FVector::DotProduct(FelledTree->Blocker->GetUpVector(),FVector::ForwardVector)>.99f);
    TestTrue(TEXT("Fallen trunk remains solid"),FelledTree->Blocker->GetCollisionEnabled()==ECollisionEnabled::QueryAndPhysics);
    TestEqual(TEXT("Repeated fall leaves wood unchanged"),FelledTree->WoodRemaining,7);
    TestEqual(TEXT("Repeated fall leaves thatch unchanged"),FelledTree->ThatchRemaining,2);
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return true;
}
#endif
