#include "EWEditorVerificationLibrary.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"

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
