#if WITH_DEV_AUTOMATION_TESTS
#include "EWCobweb.h"
#include "EWExplorationComponent.h"
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWWorldEdgeGrowthTest, "Elitewake.World.EdgeGrowsAndWraps",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWWorldEdgeGrowthTest::RunTest(const FString& Parameters)
{
    auto* Edge=NewObject<UEWExplorationComponent>(GetTransientPackage());
    Edge->SetBounds(FVector2D(-1000.f,-1000.f),2000.f);
    TestEqual(TEXT("Starts at its set size"),Edge->GetBoundsSize(),2000.f);
    Edge->GrowToCover(1000.f);
    TestEqual(TEXT("Already wide enough: unchanged"),Edge->GetBoundsSize(),2000.f);
    Edge->GrowToCover(5000.f);
    TestTrue(TEXT("Grows to cover a wider explored square"),Edge->GetBoundsSize()>=5000.f*.999f);
    const float Size=Edge->GetBoundsSize(); const FVector2D Min=Edge->GetBoundsMin();
    TestTrue(TEXT("Grows by steps, centred, not past what it needs by a whole step"),Size<5000.f*Edge->ExpandFactor*1.01f);
    TestTrue(TEXT("Centred: the old square stays inside"),Min.X<=-1000.f && Min.X+Size>=1000.f);
    const FVector Past(Min.X+Size+10.f,0.f,50.f);
    const FVector Wrapped=Edge->WrapLocation(Past);
    TestTrue(TEXT("Past the west (+X) edge comes out on the east"),FMath::IsNearlyEqual(Wrapped.X,Min.X+10.f,.01f));
    TestTrue(TEXT("Height is kept"),FMath::IsNearlyEqual(Wrapped.Z,50.0));
    const FVector Inside(0.f,0.f,0.f);
    TestTrue(TEXT("Inside is unchanged"),Edge->WrapLocation(Inside).Equals(Inside));
    return true;
}
#endif
