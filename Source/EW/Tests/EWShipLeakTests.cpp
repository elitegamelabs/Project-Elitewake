#if WITH_DEV_AUTOMATION_TESTS

#include "Ships/EWShip.h"
#include "Ships/EWShipDefinition.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWShipLeaksTest, "Elitewake.Ships.Leaks",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWShipLeaksTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    auto* Definition = NewObject<UEWShipDefinition>(GetTransientPackage());
    Definition->ShipId = TEXT("LeakTestSloop");
    Definition->HullHealth = 10000.f;
    Definition->WeightCapacity = 1500.f;

    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(true)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
    if (!TestNotNull(TEXT("Test world"), World)) return false;

    auto* Ship = World->SpawnActorDeferred<AEWShip>(AEWShip::StaticClass(), FTransform::Identity);
    if (!TestNotNull(TEXT("Spawned ship"), Ship)) { World->DestroyWorld(false); return false; }
    Ship->Definition = Definition;
    Ship->FinishSpawning(FTransform::Identity);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();
    TestEqual(TEXT("A dry ship has no settling"), Ship->GetSettle(), 0.f);

    const FVector AboveWaterline = Ship->GetActorLocation() + FVector(0.f, Definition->HullExtent.Y, 0.f);
    Ship->TakeRoundShot(AboveWaterline, FVector(0.f, 1.f, 0.f), nullptr);
    TestEqual(TEXT("A hole above the waterline does not leak"), Ship->GetLeakCount(), 0);

    const FVector BelowWaterline = Ship->GetActorLocation() + FVector(0.f, Definition->HullExtent.Y, -100.f);
    Ship->TakeRoundShot(BelowWaterline, FVector(0.f, 1.f, 0.f), nullptr);
    TestEqual(TEXT("A hole below the waterline leaks"), Ship->GetLeakCount(), 1);

    Ship->Tick(1.f);
    TestTrue(TEXT("One leak admits LeakPerHole in one second"),
        FMath::IsNearlyEqual(Ship->GetWaterAboard(), AEWShip::LeakPerHole, .05f));
    TestTrue(TEXT("Water contributes to ship load"), FMath::IsNearlyEqual(Ship->GetLoad(), Ship->GetWaterAboard(), .05f));
    TestTrue(TEXT("A light water load settles the ship proportionally"),
        FMath::IsNearlyEqual(Ship->GetSettle(), AEWShip::MaxSettle * AEWShip::LeakPerHole / Definition->WeightCapacity, .05f));

    // Add enough holes for the 1,500 kg capacity to be reached in a single normal ship tick.
    for (int32 Index = 1; Index < 25; ++Index)
        Ship->TakeRoundShot(BelowWaterline, FVector(0.f, 1.f, 0.f), nullptr);
    TestEqual(TEXT("All submerged holes count"), Ship->GetLeakCount(), 25);
    Ship->Tick(9.96f);
    TestTrue(TEXT("Settle reaches MaxSettle at capacity"), FMath::IsNearlyEqual(Ship->GetSettle(), AEWShip::MaxSettle, .05f));
    TestTrue(TEXT("Water reaches the defined weight capacity"), FMath::IsNearlyEqual(Ship->GetWaterAboard(), Definition->WeightCapacity, .05f));

    auto* CharacterClass = LoadClass<AEWCharacter>(nullptr,
        TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    auto* ControllerClass = LoadClass<AEWPlayerController>(nullptr,
        TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.BP_ThirdPersonPlayerController_C"));
    if (!TestNotNull(TEXT("Survivor class for bailing"), CharacterClass)
        || !TestNotNull(TEXT("Controller class for bailing"), ControllerClass))
    { World->DestroyWorld(false); return false; }
    FActorSpawnParameters SpawnParams;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    const FVector BucketAimPoint = Ship->GetBucketWorld() + FVector(0.f, 0.f, 20.f);
    AEWCharacter* Character = World->SpawnActor<AEWCharacter>(CharacterClass, BucketAimPoint + FVector(-100.f, 0.f, 0.f),
        FRotator::ZeroRotator, SpawnParams);
    AEWPlayerController* Controller = World->SpawnActor<AEWPlayerController>(ControllerClass);
    if (!TestNotNull(TEXT("Bailing survivor"), Character) || !TestNotNull(TEXT("Bailing controller"), Controller))
    { World->DestroyWorld(false); return false; }
    Controller->Possess(Character);
    FVector Eye; FRotator EyeRotation;
    Character->GetActorEyesViewPoint(Eye, EyeRotation);
    Controller->SetControlRotation((BucketAimPoint - Eye).Rotation());
    TestTrue(TEXT("Survivor stands aboard beside the bucket"), Ship->IsAboard(Character));
    TestTrue(TEXT("Survivor aims at the bucket"), Ship->IsAimingAtBucket(Character));
    const float BeforeBailing = Ship->GetWaterAboard();
    TestTrue(TEXT("Bucket accepts a stroke"), Ship->Interact_Implementation(Character));
    TestTrue(TEXT("One stroke removes BailPerStroke of water"),
        FMath::IsNearlyEqual(Ship->GetWaterAboard(), BeforeBailing - AEWShip::BailPerStroke, .05f));

    Ship->Tick(5.2f);
    TestTrue(TEXT("Water stops at 1.5 times capacity"),
        FMath::IsNearlyEqual(Ship->GetWaterAboard(), Definition->WeightCapacity * 1.5f, .05f));

    World->DestroyWorld(false);
    return true;
}

#endif
