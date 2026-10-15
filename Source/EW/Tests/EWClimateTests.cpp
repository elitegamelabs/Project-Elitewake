// Copyright Elite Game Labs. All Rights Reserved.

#if WITH_DEV_AUTOMATION_TESTS
#include "EWSurvivalComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "World/EWClimateRegion.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWClimateModelTest, "Elitewake.Survival.ClimateModel",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWClimateModelTest::RunTest(const FString& Parameters)
{
    const auto Values = UWorld::InitializationValues().AllowAudioPlayback(false).CreatePhysicsScene(false)
        .CreateNavigation(false).CreateAISystem(false).ShouldSimulatePhysics(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true,
        ERHIFeatureLevel::Num, &Values);
    if (!TestNotNull(TEXT("Test world"), World)) return false;
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);

    auto MakeSurvival = [World]()
    {
        AActor* Owner = World->SpawnActor<AActor>();
        UEWSurvivalComponent* Component = NewObject<UEWSurvivalComponent>(Owner);
        Owner->AddInstanceComponent(Component);
        Component->RegisterComponent();
        return Component;
    };
    FEWClimate Cold;
    Cold.Region = EEWRegion::Winter;
    Cold.AirTemperature = -12.f;
    // Hold felt temperature constant so this compares WaterChill instead of air-versus-water temperatures.
    Cold.WaterTemperature = Cold.AirTemperature;
    Cold.Humidity = 40.f;

    UEWSurvivalComponent* Comfortable = MakeSurvival();
    FEWClimate Mild;
    Mild.Region = EEWRegion::Plains;
    Mild.AirTemperature = 20.f;
    Mild.WaterTemperature = 18.f;
    Mild.Humidity = 45.f;
    Comfortable->UpdateClimate(Mild, false, 0.f, 1.f);
    TestEqual(TEXT("Comfortable air holds the target at normal body temperature"),
        Comfortable->GetTargetBodyTemperature(), UEWSurvivalComponent::NormalBody);

    UEWSurvivalComponent* ColdAir = MakeSurvival();
    ColdAir->UpdateClimate(Cold, false, 0.f, 1.f);
    const float AirTarget = ColdAir->GetTargetBodyTemperature();
    TestTrue(TEXT("Unclothed winter air targets below the freezing threshold"),
        AirTarget < UEWSurvivalComponent::FreezingBelow);
    TestTrue(TEXT("Body temperature moves toward the target by BodyRate per second"),
        FMath::IsNearlyEqual(ColdAir->GetBodyTemperature(),
            UEWSurvivalComponent::NormalBody - UEWSurvivalComponent::BodyRate, KINDA_SMALL_NUMBER));

    UEWSurvivalComponent* ColdWater = MakeSurvival();
    ColdWater->UpdateClimate(Cold, true, 0.f, 1.f);
    TestTrue(TEXT("Cold water target is lower than the same climate's air target"),
        ColdWater->GetTargetBodyTemperature() < AirTarget);
    TestTrue(TEXT("Cold water records water temperature as felt temperature"),
        FMath::IsNearlyEqual(ColdWater->GetFeltTemperature(), Cold.WaterTemperature));

    UEWSurvivalComponent* InsulatedCold = MakeSurvival();
    InsulatedCold->UpdateClimate(Cold, false, 1.f, 1.f);
    TestTrue(TEXT("Full insulation holds the winter target near normal"),
        FMath::IsNearlyEqual(InsulatedCold->GetTargetBodyTemperature(), UEWSurvivalComponent::NormalBody, .5f));

    FEWClimate Hot;
    Hot.Region = EEWRegion::Desert;
    Hot.AirTemperature = 34.f;
    Hot.WaterTemperature = 27.f;
    Hot.Humidity = 75.f;
    UEWSurvivalComponent* BareHeat = MakeSurvival();
    BareHeat->UpdateClimate(Hot, false, 0.f, 1.f);
    TestEqual(TEXT("Bare skin remains comfortable in hot humid air"),
        BareHeat->GetTargetBodyTemperature(), UEWSurvivalComponent::NormalBody);
    UEWSurvivalComponent* ClothedHeat = MakeSurvival();
    ClothedHeat->UpdateClimate(Hot, false, 1.f, 1.f);
    TestTrue(TEXT("Insulation traps heat in hot humid air"),
        ClothedHeat->GetTargetBodyTemperature() > UEWSurvivalComponent::NormalBody);

    UEWSurvivalComponent* Freezing = MakeSurvival();
    Freezing->SetBodyTemperature(UEWSurvivalComponent::FreezingBelow - 1.f);
    Freezing->UpdateClimate(Cold, false, 0.f, 1.f);
    TestTrue(TEXT("Freezing damage applies at FreezeDamage per second"),
        FMath::IsNearlyEqual(Freezing->GetHealth(), 100.f - UEWSurvivalComponent::FreezeDamage, KINDA_SMALL_NUMBER));
    TestTrue(TEXT("Freezing condition appears as a persistent notice"),
        Freezing->GetDebuffNotices().ContainsByPredicate([](const FEWDebuffNotice& Notice)
        { return Notice.Id == TEXT("Freezing"); }));
    FEWClimate Warm;
    Warm.Region = EEWRegion::Plains;
    Warm.AirTemperature = 20.f;
    Warm.WaterTemperature = 18.f;
    Warm.Humidity = 45.f;
    Freezing->SetBodyTemperature(UEWSurvivalComponent::NormalBody);
    Freezing->UpdateClimate(Warm, false, 0.f, 1.f);
    TestFalse(TEXT("Freezing notice clears after warming"),
        Freezing->GetDebuffNotices().ContainsByPredicate([](const FEWDebuffNotice& Notice)
        { return Notice.Id == TEXT("Freezing"); }));

    AEWClimateRegion* Region = World->SpawnActor<AEWClimateRegion>(FVector::ZeroVector, FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Climate region"), Region))
    {
        GEngine->DestroyWorldContext(World);
        World->DestroyWorld(false);
        return false;
    }
    Region->Region = EEWRegion::Desert;
    Region->Radii = FVector2D(5000.f, 5000.f);
    Region->OffshoreReach = 100.f;
    Region->Climate = Hot;
    const FEWClimate Inside = AEWClimateRegion::SampleClimate(World, FVector::ZeroVector);
    TestEqual(TEXT("Inside oval retains its region"), Inside.Region, EEWRegion::Desert);
    TestEqual(TEXT("Inside oval retains its climate"), Inside.AirTemperature, Hot.AirTemperature);
    const FEWClimate Halfway = AEWClimateRegion::SampleClimate(World, FVector(5050.f, 0.f, 0.f));
    const FEWClimate Sea = AEWClimateRegion::OpenSea();
    TestTrue(TEXT("Fifty metres offshore blends halfway to open sea"),
        FMath::IsNearlyEqual(Halfway.AirTemperature, FMath::Lerp(Hot.AirTemperature, Sea.AirTemperature, .5f), .01f));
    TestTrue(TEXT("Offshore humidity blends halfway to open sea"),
        FMath::IsNearlyEqual(Halfway.Humidity, FMath::Lerp(Hot.Humidity, Sea.Humidity, .5f), .01f));
    const FEWClimate Beyond = AEWClimateRegion::SampleClimate(World, FVector(5101.f, 0.f, 0.f));
    TestEqual(TEXT("Beyond offshore reach returns open-sea air"), Beyond.AirTemperature, Sea.AirTemperature);
    TestEqual(TEXT("Beyond offshore reach returns open-sea humidity"), Beyond.Humidity, Sea.Humidity);

    GEngine->DestroyWorldContext(World);
    World->DestroyWorld(false);
    return true;
}
#endif
