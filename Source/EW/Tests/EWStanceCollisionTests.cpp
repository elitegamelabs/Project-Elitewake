#if WITH_DEV_AUTOMATION_TESTS

#include "EWCharacter.h"
#include "EWCharacterMovementComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWStanceCollisionTest, "Elitewake.Movement.StanceCollision",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWStanceCollisionTest::RunTest(const FString& Parameters)
{
    const UWorld::InitializationValues Values = UWorld::InitializationValues().AllowAudioPlayback(false)
        .CreatePhysicsScene(true).CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true,
        ERHIFeatureLevel::Num, &Values);
    auto Box = [World](const FVector& Position, const FVector& Extent)
    {
        AActor* Actor = World->SpawnActor<AActor>();
        UBoxComponent* Component = NewObject<UBoxComponent>(Actor);
        Actor->SetRootComponent(Component);
        Component->SetBoxExtent(Extent);
        Component->SetCollisionProfileName(TEXT("BlockAll"));
        Component->RegisterComponent();
        Actor->SetActorLocation(Position);
        return Actor;
    };
    Box(FVector(0, 0, -10), FVector(2000, 2000, 10));
    UClass* CharacterClass = LoadClass<AEWCharacter>(nullptr,
        TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.BP_ThirdPersonCharacter_C"));
    if (!TestNotNull(TEXT("Active player Blueprint loads"), CharacterClass))
    {
        World->DestroyWorld(false);
        return false;
    }
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    AEWCharacter* Character = World->SpawnActor<AEWCharacter>(CharacterClass, FVector(0, 0, 90), FRotator::ZeroRotator, Spawn);
    UEWCharacterMovementComponent* Movement = Cast<UEWCharacterMovementComponent>(Character->GetCharacterMovement());
    if (!TestNotNull(TEXT("Blueprint uses stance movement component"), Movement))
    {
        World->DestroyWorld(false);
        return false;
    }
    Movement->SetMovementMode(MOVE_Walking);
    UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const auto Bottom = [Character, Capsule]() { return Character->GetActorLocation().Z - Capsule->GetScaledCapsuleHalfHeight(); };
    const float InitialBottom = Bottom(); // CharacterMovement keeps a small floor-distance skin.
    const auto Height = [this, Capsule](float Expected) { TestEqual(TEXT("Accepted capsule half height"), Capsule->GetUnscaledCapsuleHalfHeight(), Expected); };

    Movement->bWantsToCrouch = true;
    Movement->Crouch();
    TestTrue(TEXT("Crouch accepted in open space"), Character->IsCrouched());
    Height(60.f);
    TestTrue(TEXT("Crouch preserves capsule bottom"), FMath::IsNearlyEqual(Bottom(), InitialBottom, 0.01f));
    AActor* Roof = Box(FVector(0, 0, 160), FVector(250, 250, 10));
    Movement->UnCrouch();
    TestTrue(TEXT("Low roof blocks standing"), Character->IsCrouched());
    Height(60.f);
    Roof->Destroy();
    Movement->UnCrouch();
    TestFalse(TEXT("Standing accepted after roof is removed"), Character->IsCrouched());
    Height(90.f);

    AActor* EntryWall = Box(FVector(90, 0, 45), FVector(10, 250, 45));
    Movement->bWantsToProne = true;
    Movement->Crouch();
    TestFalse(TEXT("Prone body entry rejects nearby wall beyond root capsule"), Character->IsProne());
    Height(90.f);
    EntryWall->Destroy();
    Movement->bWantsToProne = true;
    Movement->Crouch();
    TestTrue(TEXT("Prone accepted in open space"), Character->IsProne());
    Height(28.f);
    TestTrue(TEXT("Prone preserves capsule bottom"), FMath::IsNearlyEqual(Bottom(), InitialBottom, 0.01f));
    Roof = Box(FVector(0, 0, 75), FVector(250, 250, 10));
    Movement->bWantsToProne = false;
    Movement->Crouch();
    TestTrue(TEXT("Crawl-only roof blocks prone to crouch"), Character->IsProne());
    Height(28.f);
    Movement->UnCrouch();
    TestTrue(TEXT("Crawl-only roof blocks prone to stand"), Character->IsProne());
    Roof->Destroy();

    AActor* Wall = Box(FVector(200, 0, 50), FVector(10, 250, 50));
    FHitResult Hit;
    Movement->SafeMoveUpdatedComponent(FVector(400, 0, 0), FQuat::Identity, true, Hit);
    TestTrue(TEXT("Body sweep returns wall hit"), Hit.bBlockingHit);
    TestTrue(TEXT("Body stops before head clips through wall"), Character->GetActorLocation().X < 86.f);
    Wall->Destroy();
    Movement->SafeMoveUpdatedComponent(FVector(-Character->GetActorLocation().X, 0, 0), FQuat::Identity, true, Hit);
    AActor* SideWall = Box(FVector(0, 70, 50), FVector(250, 10, 50));
    Movement->SafeMoveUpdatedComponent(FVector::ZeroVector, FRotator(0, 90, 0).Quaternion(), true, Hit);
    TestTrue(TEXT("Body blocks turn into side wall"), FMath::IsNearlyZero(Character->GetActorRotation().Yaw, 0.1f));
    SideWall->Destroy();
    Movement->SafeMoveUpdatedComponent(FVector::ZeroVector, FRotator(0, 90, 0).Quaternion(), true, Hit);
    TestTrue(TEXT("Turn accepted after wall is removed"), FMath::IsNearlyEqual(Character->GetActorRotation().Yaw, 90.f, 0.1f));

    Movement->bWantsToProne = false;
    Movement->Crouch();
    TestFalse(TEXT("Prone returns to crouch in open space"), Character->IsProne());
    Height(60.f);
    Movement->UnCrouch();
    Height(90.f);
    TestTrue(TEXT("Returning to standing preserves bottom"), FMath::IsNearlyEqual(Bottom(), InitialBottom, 0.01f));
    Movement->SetMovementMode(MOVE_Falling);
    Movement->bWantsToProne = true;
    Movement->bWantsToCrouch = true;
    Movement->UpdateCharacterStateBeforeMovement(.016f);
    TestFalse(TEXT("Airborne prone entry leaves standing collider intact"), Character->IsProne());
    Height(90.f);

    FEWSavedMove Saved;
    Saved.bSavedWantsToProne = true;
    Saved.bSavedSprintInputHeld = true;
    TestTrue(TEXT("Prone intent included in movement packet"), (Saved.GetCompressedFlags() & FSavedMove_Character::FLAG_Custom_0) != 0);
    TestTrue(TEXT("Sprint exit intent included in movement packet"), (Saved.GetCompressedFlags() & FSavedMove_Character::FLAG_Custom_1) != 0);
    Saved.Clear();
    TestEqual(TEXT("Saved move reuse clears stance and sprint intent"), Saved.GetCompressedFlags(), uint8(0));

    AActor* Ramp = Box(FVector(800, 0, 60), FVector(300, 250, 20));
    Ramp->SetActorRotation(FRotator(10, 0, 0));
    Character->SetActorLocationAndRotation(FVector(800, 0, 174), FRotator::ZeroRotator);
    Movement->SetMovementMode(MOVE_Walking);
    Movement->FindFloor(Character->GetActorLocation(), Movement->CurrentFloor, false);
    TestTrue(TEXT("Inclined fixture provides a walkable floor"), Movement->CurrentFloor.IsWalkableFloor());
    Movement->bWantsToProne = true;
    Movement->bWantsToCrouch = true;
    Movement->Crouch();
    TestTrue(TEXT("Prone body fits on a ten degree slope"), Character->IsProne());
    Movement->SafeMoveUpdatedComponent(FVector(100, 0, FMath::Tan(FMath::DegreesToRadians(10.f)) * 100),
        FQuat::Identity, true, Hit);
    TestFalse(TEXT("Supporting slope does not block prone body sweep"), Hit.bBlockingHit);
    TestTrue(TEXT("Prone body advances along inclined surface"), Character->GetActorLocation().X > 899.f);
    World->DestroyWorld(false);
    return true;
}

#endif
