#include "World/EWNightLight.h"
#include "World/EWDayNight.h"
#include "Components/LightComponent.h"

AEWNightLight::AEWNightLight()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 1.f;
    bReplicates = false;
}

void AEWNightLight::BeginPlay()
{
    Super::BeginPlay();
    Tick(0.f);
}

void AEWNightLight::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const UEWDayNightSubsystem* Time = UEWDayNightSubsystem::GetForWorld(this);
    const bool bNight = Time && !Time->IsDay();
    if (GetLightComponent() && GetLightComponent()->IsVisible() != bNight) GetLightComponent()->SetVisibility(bNight);
}
