#if WITH_DEV_AUTOMATION_TESTS
#include "EWCobweb.h"
#include "Wildlife/EWWildlifeRest.h"
#include "EWCharacter.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Misc/AutomationTest.h"

namespace
{
    UWorld* MakeTestWorld()
    {
        const auto Values=UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
            .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
        UWorld* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values);
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        return World;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWWildlifeRestTest, "Elitewake.Wildlife.RestWithoutSurvivors",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWWildlifeRestTest::RunTest(const FString& Parameters)
{
    UWorld* World=MakeTestWorld();
    UClass* PawnClass=LoadClass<AEWCharacter>(nullptr,TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    if (!TestNotNull(TEXT("Player class"),PawnClass)) { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return false; }
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Creature=World->SpawnActor<AActor>(AActor::StaticClass(),FVector::ZeroVector,FRotator::ZeroRotator,Spawn);
    Creature->SetRootComponent(NewObject<USceneComponent>(Creature)); Creature->GetRootComponent()->RegisterComponent();
    auto* Pawn=World->SpawnActor<AEWCharacter>(PawnClass,FVector(FEWWildlifeRest::RestRange*2.f,0,0),FRotator::ZeroRotator,Spawn);
    Pawn->GetCharacterMovement()->DisableMovement();
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    FEWWildlifeRest Rest; Rest.Look=FEWWildlifeRest::LookSeconds;
    TestTrue(TEXT("Awake until the first look"),Rest.IsAwake(Creature,.1f));
    TestFalse(TEXT("Rests when its look finds no survivor within range"),Rest.IsAwake(Creature,2.f));
    TestFalse(TEXT("Keeps resting between looks"),Rest.IsAwake(Creature,.1f));
    Pawn->SetActorLocation(FVector(FEWWildlifeRest::RestRange*.5f,0,0));
    TestFalse(TEXT("Does not look before the next look is due"),Rest.IsAwake(Creature,.1f));
    TestTrue(TEXT("Wakes when a survivor is within range at the next look"),Rest.IsAwake(Creature,2.f));
    Pawn->SetActorLocation(FVector(FEWWildlifeRest::RestRange*2.f,0,0));
    TestFalse(TEXT("Rests again when the survivor leaves"),Rest.IsAwake(Creature,2.f));
    Rest.Wake();
    TestTrue(TEXT("A blow wakes it at once"),Rest.bAwake);
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWCobwebTest, "Elitewake.World.CobwebTearAndRegrow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWCobwebTest::RunTest(const FString& Parameters)
{
    UWorld* World=MakeTestWorld();
    auto* Web=World->SpawnActor<AEWCobweb>(FVector::ZeroVector,FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Cobweb"),Web)) { GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return false; }
    World->InitializeActorsForPlay(FURL()); World->BeginPlay();
    TestFalse(TEXT("Starts whole"),Web->IsTorn());
    TestEqual(TEXT("No strands falling at first"),Web->GetFallingStrands(),0);
    Web->Tear();
    TestTrue(TEXT("Torn when walked through"),Web->IsTorn());
    TestEqual(TEXT("Falls apart in its strands"),Web->GetFallingStrands(),AEWCobweb::ShredCount);
    Web->Tick(AEWCobweb::FallSeconds+.1f);
    TestEqual(TEXT("The strands are gone after the fall"),Web->GetFallingStrands(),0);
    TestTrue(TEXT("Still torn after the fall"),Web->IsTorn());
    Web->Tick(AEWCobweb::RegrowSeconds);
    TestFalse(TEXT("Spun again after ten minutes"),Web->IsTorn());
    GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return true;
}
#endif
