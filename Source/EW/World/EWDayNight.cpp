#include "World/EWDayNight.h"
#include "World/EWNorth.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/GameStateBase.h"
#include "Net/UnrealNetwork.h"

float FEWSkyClock::HourAfter(float Hour, double Seconds)
{
    return static_cast<float>(FMath::Fmod(FMath::Fmod(static_cast<double>(Hour) + Seconds / SecondsPerHour, 24.0) + 24.0, 24.0));
}

int32 FEWSkyClock::DayAfter(int32 Day, float Hour, double Seconds)
{
    const double Hours = static_cast<double>(Hour) + FMath::Max(0.0, Seconds) / SecondsPerHour;
    return FMath::Max(1, Day) + static_cast<int32>(FMath::FloorToDouble(Hours / 24.0));
}

float FEWSkyClock::SunElevation(float Hour)
{
    // A sine over the day, and its mirror under the horizon through the night.
    return HighestSun * FMath::Sin(PI * (Hour - DayStarts) / 12.f);
}

float FEWSkyClock::SunAzimuth(float Hour)
{
    // East (bearing 90) at 06:00, a quarter of the compass every six hours, as world yaw (World/EWNorth.h).
    return EWNorth::YawOfBearing(90.f + 90.f * (Hour - DayStarts) / 6.f);
}

AEWSkyClock::AEWSkyClock()
{
    bReplicates = true;
    bAlwaysRelevant = true;
    SetNetUpdateFrequency(1.f);
    PrimaryActorTick.bCanEverTick = true;
    // The sun moves a quarter of a degree a minute; a few updates a second are plenty.
    PrimaryActorTick.TickInterval = .25f;
}

void AEWSkyClock::BeginPlay()
{
    Super::BeginPlay();
    if (UEWDayNightSubsystem* Time = GetWorld()->GetSubsystem<UEWDayNightSubsystem>()) Time->SetClock(this);
    FindLights();
    ApplyLight(GetHour());
}

void AEWSkyClock::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWSkyClock, AnchorHour);
    DOREPLIFETIME(AEWSkyClock, AnchorServerTime);
    DOREPLIFETIME(AEWSkyClock, AnchorDay);
}

int32 AEWSkyClock::GetDay() const
{
    const AGameStateBase* State = GetWorld() ? GetWorld()->GetGameState() : nullptr;
    const double Now = State ? State->GetServerWorldTimeSeconds() : (GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0);
    return FEWSkyClock::DayAfter(AnchorDay, AnchorHour, Now - AnchorServerTime);
}

float AEWSkyClock::GetHour() const
{
    const AGameStateBase* State = GetWorld() ? GetWorld()->GetGameState() : nullptr;
    const double Now = State ? State->GetServerWorldTimeSeconds() : (GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0);
    return FEWSkyClock::HourAfter(AnchorHour, FMath::Max(0.0, Now - AnchorServerTime));
}

void AEWSkyClock::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ApplyLight(GetHour());
}

void AEWSkyClock::FindLights()
{
    for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("EWSun"))) { Sun = *It; break; }
    }
    if (!Sun) return;
    if (UDirectionalLightComponent* Light = Cast<UDirectionalLightComponent>(Sun->GetLightComponent()))
    {
        SunIntensity = Light->Intensity;
    }
    // A moving light has to be movable before it is registered, so the moon is spawned deferred.
    Moon = GetWorld()->SpawnActorDeferred<ADirectionalLight>(ADirectionalLight::StaticClass(), FTransform::Identity);
    if (Moon)
    {
        Moon->SetFlags(RF_Transient);
        Moon->Tags.Add(TEXT("EWMoon"));
        Moon->GetLightComponent()->SetMobility(EComponentMobility::Movable);
        Moon->FinishSpawning(FTransform::Identity);
    }
    if (UDirectionalLightComponent* Light = Moon ? Cast<UDirectionalLightComponent>(Moon->GetLightComponent()) : nullptr)
    {
        // Moonlight (tuning): about a twentieth of the sun, cool, the atmosphere's second light.
        Light->SetIntensity(SunIntensity * .05f);
        Light->SetLightColor(FLinearColor(.55f, .65f, 1.f));
        // Not an atmosphere light: the sky is dark at night, not a dim day.
        Light->SetAtmosphereSunLight(false);
        Light->SetCastShadows(true);
    }
    FActorSpawnParameters Params;
    Params.ObjectFlags |= RF_Transient;
    NightGrade = GetWorld()->SpawnActor<APostProcessVolume>(Params);
    if (NightGrade)
    {
        NightGrade->bUnbound = true;
        NightGrade->Priority = -1.f;          // under any volume the map places itself
        NightGrade->Settings.bOverride_AutoExposureBias = true;
    }
}

void AEWSkyClock::ApplyLight(float Hour)
{
    if (!Sun) return;
    const float Elevation = FEWSkyClock::SunElevation(Hour);
    const float Azimuth = FEWSkyClock::SunAzimuth(Hour);
    Sun->SetActorRotation(FEWSkyClock::LightRotation(Elevation, Azimuth));
    // Twilight (tuning): the sun keeps lighting the sky until it is 10 degrees under the horizon, fading as it goes;
    // the moon and the night's darker exposure come in as it does.
    const float SunUp = FMath::Clamp((Elevation + 10.f) / 12.f, 0.f, 1.f);
    if (UDirectionalLightComponent* Light = Cast<UDirectionalLightComponent>(Sun->GetLightComponent()))
    {
        Light->SetIntensity(SunIntensity * SunUp);
    }
    if (Moon)
    {
        Moon->SetActorRotation(FEWSkyClock::LightRotation(-Elevation, Azimuth + 180.f));
        Moon->GetLightComponent()->SetVisibility(SunUp < 1.f);
    }
    if (NightGrade) NightGrade->Settings.AutoExposureBias = -FEWSkyClock::NightExposure * (1.f - SunUp);
}

UEWDayNightSubsystem* UEWDayNightSubsystem::GetForWorld(const UObject* WorldContext)
{
    const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    return World ? World->GetSubsystem<UEWDayNightSubsystem>() : nullptr;
}

void UEWDayNightSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
    Super::OnWorldBeginPlay(InWorld);
    if (!InWorld.IsGameWorld() || InWorld.GetNetMode() == NM_Client) return;
    FActorSpawnParameters Params;
    Params.ObjectFlags |= RF_Transient;
    Clock = InWorld.SpawnActor<AEWSkyClock>(Params);
    if (Clock) Clock->AnchorServerTime = InWorld.GetTimeSeconds();
}

float UEWDayNightSubsystem::GetHour() const
{
    return Clock ? Clock->GetHour() : FEWSkyClock::StartHour;
}

int32 UEWDayNightSubsystem::GetDay() const
{
    return Clock ? Clock->GetDay() : 1;
}

void UEWDayNightSubsystem::SetDayAndHour(int32 Day, float Hour)
{
    if (!Clock || !FMath::IsFinite(Hour) || (GetWorld() && GetWorld()->GetNetMode() == NM_Client)) return;
    SetHour(Hour);
    Clock->AnchorDay = FMath::Max(1, Day);
    Clock->ForceNetUpdate();
}

void UEWDayNightSubsystem::SetHour(float Hour)
{
    if (!Clock || !FMath::IsFinite(Hour) || (GetWorld() && GetWorld()->GetNetMode() == NM_Client)) return;
    const AGameStateBase* State = GetWorld()->GetGameState();
    // The day carries on: setting the hour does not change which day it is.
    Clock->AnchorDay = Clock->GetDay();
    Clock->AnchorHour = FEWSkyClock::HourAfter(Hour, 0.0);
    Clock->AnchorServerTime = State ? State->GetServerWorldTimeSeconds() : GetWorld()->GetTimeSeconds();
    Clock->ForceNetUpdate();
}
