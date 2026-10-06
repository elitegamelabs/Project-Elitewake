#if WITH_DEV_AUTOMATION_TESTS
#include "EWInteractionComponent.h"
#include "EWInteractable.h"
#include "EWStation.h"
#include "EWResourceNode.h"
#include "EWCharacter.h"
#include "EWSurvivalComponent.h"
#include "EWInventoryComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWInteractionTest,"Elitewake.Interaction.AuthorityAndHolds",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWInteractionTest::RunTest(const FString& Parameters)
{
    const auto Values=UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    UClass* PawnClass=LoadClass<AEWCharacter>(nullptr,TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    if (!TestNotNull(TEXT("Player class"),PawnClass)) { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return false; }
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Pawn=World->SpawnActor<AEWCharacter>(PawnClass,FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    auto* PC=World->SpawnActor<APlayerController>(); PC->Possess(Pawn); PC->SetControlRotation(FRotator::ZeroRotator); Pawn->GetCharacterMovement()->DisableMovement();
    auto* Interaction=NewObject<UEWInteractionComponent>(PC); PC->AddInstanceComponent(Interaction); Interaction->RegisterComponent();
    FVector Eye; FRotator Rotation; Pawn->GetActorEyesViewPoint(Eye,Rotation);
    auto* Station=World->SpawnActor<AEWStation>(Eye+FVector(150,0,0),FRotator::ZeroRotator);
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    // TimerManager ticks once per engine frame; each synthetic world step is a new frame.
    TGuardValue<uint64> FrameGuard(GFrameCounter, GFrameCounter);
    auto Wait=[&](float Seconds) { for(float Elapsed=0;Elapsed<Seconds;Elapsed+=.05f) { ++GFrameCounter; World->Tick(LEVELTICK_All,.05f); } };
    auto StartHold=[&]() { Wait(.2f); Station->Mode=EEWInteractionMode::Hold; Station->HoldDuration=.5f; Interaction->Request(Station); };
    TestEqual(TEXT("Shared targeting finds station"),FEWInteractionTargeting::FindTarget(Pawn),static_cast<AActor*>(Station));
    Interaction->Request(Station); TestEqual(TEXT("Press acknowledges once"),Station->GetAcknowledgementCount(),1);
    Wait(.2f); Station->bAvailable=false; Interaction->Request(Station); TestEqual(TEXT("CanInteract false rejected"),Station->GetAcknowledgementCount(),1); Station->bAvailable=true;
    Wait(.2f); Interaction->SetMenuBlocked(true); Interaction->Request(Station); TestEqual(TEXT("Menu rejects forged request"),Station->GetAcknowledgementCount(),1); Interaction->SetMenuBlocked(false);
    Wait(.2f); auto* Mismatch=World->SpawnActor<AEWStation>(Eye+FVector(150,200,0),FRotator::ZeroRotator); Interaction->Request(Mismatch); TestEqual(TEXT("Mismatched target rejected"),Mismatch->GetAcknowledgementCount(),0); Mismatch->Destroy();
    Wait(.2f); Station->SetActorLocation(Eye+FVector(400,0,0)); Interaction->Request(Station); TestEqual(TEXT("Range rejected"),Station->GetAcknowledgementCount(),1); Station->SetActorLocation(Eye+FVector(150,0,0));
    auto* Wall=World->SpawnActor<AActor>(); auto* Box=NewObject<UBoxComponent>(Wall); Wall->SetRootComponent(Box); Box->SetBoxExtent(FVector(10,100,100)); Box->SetCollisionProfileName(TEXT("BlockAll")); Box->RegisterComponent(); Wall->SetActorLocation(Eye+FVector(75,0,0));
    Wait(.2f); Interaction->Request(Station); TestEqual(TEXT("Through-wall rejected"),Station->GetAcknowledgementCount(),1); Wall->Destroy();
    StartHold(); const double Start=Interaction->GetHoldState().StartTime; Wait(.15f); Interaction->Request(Station); TestEqual(TEXT("Repeated start retains timer"),Interaction->GetHoldState().StartTime,Start); TestEqual(TEXT("No early completion"),Station->GetAcknowledgementCount(),1);
    Wait(.45f); TestEqual(TEXT("Server completes once"),Station->GetAcknowledgementCount(),2); Wait(.7f); TestEqual(TEXT("Timer stops"),Station->GetAcknowledgementCount(),2);
    StartHold(); Interaction->Cancel(); Wait(.7f); TestEqual(TEXT("Release cancels"),Station->GetAcknowledgementCount(),2);
    StartHold(); PC->SetControlRotation(FRotator(0,90,0)); Wait(.7f); TestEqual(TEXT("Looking away cancels"),Station->GetAcknowledgementCount(),2); PC->SetControlRotation(FRotator::ZeroRotator);
    StartHold(); Station->SetActorLocation(Eye+FVector(400,0,0)); Wait(.7f); TestEqual(TEXT("Range loss cancels"),Station->GetAcknowledgementCount(),2); Station->SetActorLocation(Eye+FVector(150,0,0));
    StartHold(); Interaction->SetMenuBlocked(true); Wait(.7f); TestEqual(TEXT("Opening inventory cancels"),Station->GetAcknowledgementCount(),2); Interaction->SetMenuBlocked(false);
    StartHold(); PC->UnPossess(); Wait(.7f); TestEqual(TEXT("Pawn loss cancels"),Station->GetAcknowledgementCount(),2); PC->Possess(Pawn);
    StartHold(); Pawn->GetSurvivalComponent()->ApplyDamage(100); Wait(.7f); TestEqual(TEXT("Death cancels"),Station->GetAcknowledgementCount(),2); Pawn->GetSurvivalComponent()->RestoreHealth(100);
    StartHold(); Station->bAvailable=false; Wait(.7f); TestEqual(TEXT("Unavailable target cancels"),Station->GetAcknowledgementCount(),2); Station->bAvailable=true;
    StartHold(); Station->Destroy(); Wait(.7f); TestNull(TEXT("Destroyed target clears hold"),Interaction->GetHoldState().Target.Get());
    auto* Tree=World->SpawnActor<AEWResourceNode>(Eye+FVector(150,0,0),FRotator::ZeroRotator); Wait(.2f); Interaction->Request(Tree); TestEqual(TEXT("Resource fixture acknowledges"),Tree->GetAcknowledgementCount(),1); TestEqual(TEXT("Fixture grants no inventory"),Pawn->GetInventoryComponent()->GetUsedSlotCount(),0);
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return true;
}
#endif
