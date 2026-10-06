#include "EWEditorVerificationLibrary.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "Engine/NetDriver.h"

UEnhancedInputLocalPlayerSubsystem* UEWEditorVerificationLibrary::GetPlayerInputSubsystem(APlayerController* Controller)
{
    ULocalPlayer* Player = Controller ? Controller->GetLocalPlayer() : nullptr;
    return Player ? Player->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr;
}

TArray<UWorld*> UEWEditorVerificationLibrary::GetPlayWorlds()
{
    TArray<UWorld*> Worlds;
    if (GEngine)
    {
        for (const FWorldContext& Context : GEngine->GetWorldContexts())
        {
            if (Context.WorldType == EWorldType::PIE && Context.World())
            {
                Worlds.Add(Context.World());
            }
        }
    }
    return Worlds;
}

AActor* UEWEditorVerificationLibrary::SpawnVerificationBox(UWorld* World, FVector Location, FVector Extent, FRotator Rotation)
{
    if (!World || World->WorldType != EWorldType::PIE) return nullptr;
    AActor* Actor = World->SpawnActor<AActor>();
    UBoxComponent* Box = NewObject<UBoxComponent>(Actor);
    Actor->SetRootComponent(Box);
    Box->SetBoxExtent(Extent);
    Box->SetCollisionProfileName(TEXT("BlockAll"));
    Box->SetHiddenInGame(false);
    Box->RegisterComponent();
    Actor->SetActorLocationAndRotation(Location, Rotation);
    return Actor;
}

FIntPoint UEWEditorVerificationLibrary::GetVerificationNetworkSettings(UWorld* World)
{
#if DO_ENABLE_NET_TEST
    UNetDriver* Driver = World && World->WorldType == EWorldType::PIE ? World->GetNetDriver() : nullptr;
    if (Driver) return FIntPoint(Driver->PacketSimulationSettings.PktLag, Driver->PacketSimulationSettings.PktLoss);
#endif
    return FIntPoint(-1, -1);
}

bool UEWEditorVerificationLibrary::SetVerificationNetworkSettings(UWorld* World, int32 LagMilliseconds, int32 LossPercent)
{
#if DO_ENABLE_NET_TEST
    UNetDriver* Driver = World && World->WorldType == EWorldType::PIE ? World->GetNetDriver() : nullptr;
    if (Driver)
    {
        FPacketSimulationSettings Settings = Driver->PacketSimulationSettings;
        Settings.PktLag = FMath::Clamp(LagMilliseconds, 0, 1000);
        Settings.PktLoss = FMath::Clamp(LossPercent, 0, 100);
        Driver->SetPacketSimulationSettings(Settings);
        return true;
    }
#endif
    return false;
}
