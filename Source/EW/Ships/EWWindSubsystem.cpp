#include "EWWindSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"

AEWWindState::AEWWindState()
{
    bReplicates = true;
    bAlwaysRelevant = true;
    SetNetUpdateFrequency(1.f);
    PrimaryActorTick.bCanEverTick = false;
}

void AEWWindState::BeginPlay()
{
    Super::BeginPlay();
    if (UEWWindSubsystem* Wind = GetWorld()->GetSubsystem<UEWWindSubsystem>()) Wind->SetState(this);
}

void AEWWindState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWWindState, WindYaw);
}

UEWWindSubsystem* UEWWindSubsystem::GetForWorld(const UObject* WorldContext)
{
    const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
    return World ? World->GetSubsystem<UEWWindSubsystem>() : nullptr;
}

void UEWWindSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
    Super::OnWorldBeginPlay(InWorld);
    if (!InWorld.IsGameWorld() || InWorld.GetNetMode() == NM_Client) return;
    FActorSpawnParameters Params;
    Params.ObjectFlags |= RF_Transient;
    State = InWorld.SpawnActor<AEWWindState>(Params);
    if (State) State->WindYaw = WindYaw;
}

void UEWWindSubsystem::SetWindYaw(float NewYaw)
{
    if (!FMath::IsFinite(NewYaw) || (GetWorld() && GetWorld()->GetNetMode() == NM_Client)) return;
    WindYaw = FRotator::NormalizeAxis(NewYaw);
    if (State) State->WindYaw = WindYaw;
}

float UEWWindSubsystem::GetHeadingFactor(const FVector& ShipForward) const
{
    const FVector Heading = FVector(ShipForward.X, ShipForward.Y, 0).GetSafeNormal();
    if (Heading.IsNearlyZero()) return MinUpwindFactor;
    // Cosine is 1 when the ship runs with the wind and -1 when it heads into it.
    const float Alignment = FVector::DotProduct(Heading, GetWindDirection());
    return MinUpwindFactor + (1.f - MinUpwindFactor) * (Alignment + 1.f) * .5f;
}
