#if WITH_DEV_AUTOMATION_TESTS
#include "Gathering/EWMineable.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWEquipmentComponent.h"
#include "EWItemDefinition.h"
#include "EWSurvivalComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWMiningTest,"Elitewake.Gathering.PickaxeMining",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWMiningTest::RunTest(const FString& Parameters)
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
    auto* Stone=NewObject<UEWItemDefinition>(); Stone->ItemId=TEXT("Test.Stone"); Stone->Category=EEWItemCategory::Resource; Stone->MaxStackSize=250;
    auto* Ore=NewObject<UEWItemDefinition>(); Ore->ItemId=TEXT("Test.Ore"); Ore->Category=EEWItemCategory::Resource; Ore->MaxStackSize=250;
    auto* Tool=NewObject<UEWItemDefinition>(); Tool->ItemId=TEXT("Test.Pickaxe"); Tool->Category=EEWItemCategory::Tool; Tool->EquipmentSlot=EEWEquipmentSlot::MainHand; Tool->GatheringTool=EEWGatheringTool::Pickaxe; Tool->MaxStackSize=1;
    auto* Node=World->SpawnActor<AEWMineable>(Eye+FVector(150,0,0),FRotator::ZeroRotator); Node->Resource=Stone;
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    auto* Inventory=Pawn->GetInventoryComponent(); auto* Equipment=Pawn->GetEquipmentComponent();
    TestEqual(TEXT("Bare hands cannot mine"),Node->TryMine(Pawn),0);
    Inventory->AddItem(Tool,1); TestEqual(TEXT("Merely carrying a pickaxe cannot mine"),Node->TryMine(Pawn),0);
    TestTrue(TEXT("Owned tool equips"),Equipment->EquipItem(Tool,EEWEquipmentSlot::MainHand)==EEWEquipmentResult::Success);
    TestFalse(TEXT("Interact does not mine"),IEWInteractable::Execute_Interact(Node,Pawn));
    Node->MinimumPickaxeTier=EEWPickaxeTier::Metal;
    Tool->PickaxeTier=EEWPickaxeTier::Wooden;
    TestFalse(TEXT("Wooden pickaxe is below a metal node requirement"),Node->CanMine(Pawn));
    Tool->PickaxeTier=EEWPickaxeTier::Metal;
    TestTrue(TEXT("Metal pickaxe meets its node requirement"),Node->CanMine(Pawn));
    Tool->PickaxeTier=EEWPickaxeTier::Tungsten;
    TestTrue(TEXT("Higher-tier pickaxe meets a metal node requirement"),Node->CanMine(Pawn));
    Node->MinimumPickaxeTier=EEWPickaxeTier::None; Tool->PickaxeTier=EEWPickaxeTier::None;
    Tool->GatheringTool=EEWGatheringTool::Hatchet; TestEqual(TEXT("Hatchet cannot mine"),Node->TryMine(Pawn),0); Tool->GatheringTool=EEWGatheringTool::Pickaxe;
    TestEqual(TEXT("Pickaxe accepts stone"),Node->TryMine(Pawn),3);
    Node->Resource=Ore; TestEqual(TEXT("Authored ore is accepted"),Node->TryMine(Pawn),3); TestEqual(TEXT("Ore identity preserved"),Inventory->GetItemCount(Ore),3); Node->Resource=Stone;
    PC->SetControlRotation(FRotator(0,90,0)); TestEqual(TEXT("Aim rejected"),Node->TryMine(Pawn),0); PC->SetControlRotation(FRotator::ZeroRotator);
    Node->SetActorLocation(Eye+FVector(400,0,0)); TestEqual(TEXT("Range rejected"),Node->TryMine(Pawn),0); Node->SetActorLocation(Eye+FVector(150,0,0));
    Node->SetOwner(PC); TestEqual(TEXT("Own source accessible"),Node->TryMine(Pawn),3); Node->SetOwner(World->SpawnActor<AActor>()); TestEqual(TEXT("Foreign owner rejected"),Node->TryMine(Pawn),0); Node->SetOwner(nullptr);
    Pawn->GetSurvivalComponent()->ApplyDamage(100); TestEqual(TEXT("Dead survivor rejected"),Node->TryMine(Pawn),0); Pawn->GetSurvivalComponent()->RestoreHealth(100);
    Stone->Category=EEWItemCategory::Tool; TestEqual(TEXT("Invalid resource category rejected"),Node->TryMine(Pawn),0); Stone->Category=EEWItemCategory::Resource;
    Inventory->RemoveItem(Ore,100); Inventory->AddItem(Stone,5993);
    TestEqual(TEXT("Partial strike transfers only capacity"),Node->TryMine(Pawn),1); TestEqual(TEXT("Rejected stock preserved"),Node->Remaining,2);
    TestEqual(TEXT("Full inventory preserves pool"),Node->TryMine(Pawn),0);
    Inventory->RemoveItem(Stone,100000);
    TestEqual(TEXT("Freed capacity receives last stock"),Node->TryMine(Pawn),2); TestTrue(TEXT("Depleted source destroyed"),Node->IsActorBeingDestroyed());
    TestEqual(TEXT("No replay after depletion"),Node->TryMine(Pawn),0); TestEqual(TEXT("Final conserved inventory"),Inventory->GetItemCount(Stone),2);
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return true;
}
#endif
