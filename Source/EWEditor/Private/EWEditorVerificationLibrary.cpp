#include "EWEditorVerificationLibrary.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "Engine/NetDriver.h"
#include "EWPickup.h"
#include "EWPlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "EWStation.h"
#include "EWResourceNode.h"
#include "Survival/EWWaterSource.h"

AEWWaterSource* UEWEditorVerificationLibrary::SpawnVerificationWaterSource(UWorld* World, FVector Location, bool bFresh)
{
    if (!World || World->WorldType != EWorldType::PIE || World->GetNetMode() == NM_Client) return nullptr;
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Source = World->SpawnActor<AEWWaterSource>(Location, FRotator::ZeroRotator, Spawn);
    if (Source) { Source->WaterQuality = bFresh ? EEWWaterQuality::Fresh : EEWWaterQuality::Salt; Source->ForceNetUpdate(); }
    return Source;
}

AEWStation* UEWEditorVerificationLibrary::SpawnVerificationInteractable(UWorld* World, FVector Location, bool bResource, bool bHold, bool bSingleUse, float Duration)
{
    if (!World || World->WorldType != EWorldType::PIE || World->GetNetMode() == NM_Client) return nullptr;
    FActorSpawnParameters Spawn; Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Target = World->SpawnActor<AEWStation>(bResource ? AEWResourceNode::StaticClass() : AEWStation::StaticClass(), Location, FRotator::ZeroRotator, Spawn);
    if (Target) { Target->Mode = bHold ? EEWInteractionMode::Hold : EEWInteractionMode::Press; Target->bSingleUse = bSingleUse; Target->HoldDuration = Duration; Target->ForceNetUpdate(); }
    return Target;
}
bool UEWEditorVerificationLibrary::SetVerificationInteractionAvailable(AEWStation* Target, bool bAvailable)
{
    if (!Target || !Target->HasAuthority() || Target->GetWorld()->WorldType != EWorldType::PIE) return false;
    Target->bAvailable = bAvailable; Target->ForceNetUpdate(); return true;
}

bool UEWEditorVerificationLibrary::SendVerificationInteractionRequest(AEWPlayerController* Controller, AActor* Target, bool bCancel)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType != EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor,false);
    if (bCancel) Controller->ServerCancelInteraction();
    else Controller->ServerInteract(Target);
    return true;
}

bool UEWEditorVerificationLibrary::FlushVerificationInput(AEWPlayerController* Controller)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType!=EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor,false);
    Controller->FlushPressedKeys();
    return !Controller->IsHotbarModifierHeld();
}

bool UEWEditorVerificationLibrary::SendVerificationUIKey(APlayerController* Controller, FName KeyName)
{
    return SendVerificationUIKeyEvent(Controller,KeyName,true) && SendVerificationUIKeyEvent(Controller,KeyName,false);
}

bool UEWEditorVerificationLibrary::SendVerificationUIKeyEvent(APlayerController* Controller, FName KeyName, bool bPressed)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType != EWorldType::PIE || !FSlateApplication::IsInitialized()) return false;
    const FKey Key(KeyName);
    if (!Key.IsValid()) return false;
    const int32 User = FSlateApplication::Get().GetUserIndexForController(Controller->GetLocalPlayer()->GetControllerId());
    const FKeyEvent Event(Key, FModifierKeysState(), User, false, 0, 0);
    // Python's editor execution guard forces actor RPCs local. Exercise normal game input.
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor, false);
    if (bPressed) FSlateApplication::Get().ProcessKeyDownEvent(Event);
    else FSlateApplication::Get().ProcessKeyUpEvent(Event);
    return true;
}

bool UEWEditorVerificationLibrary::SendVerificationHotbarRequest(AEWPlayerController* Controller, int32 Slot, UEWItemDefinition* Item, bool bActivate)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType!=EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor,false);
    if (bActivate) Controller->RequestHotbarActivation(Slot);
    else Controller->RequestHotbarBinding(Slot,Item);
    return true;
}

bool UEWEditorVerificationLibrary::SendVerificationEquipmentRequest(AEWPlayerController* Controller, UEWItemDefinition* Item, EEWEquipmentSlot Slot, bool bUnequip)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType != EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor, false);
    if (bUnequip) Controller->RequestUnequipItem(Slot);
    else Controller->RequestEquipItem(Item, Slot);
    return true;
}

bool UEWEditorVerificationLibrary::SendVerificationUIAnalog(APlayerController* Controller, float Value)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType != EWorldType::PIE || !FSlateApplication::IsInitialized()) return false;
    const int32 User = FSlateApplication::Get().GetUserIndexForController(Controller->GetLocalPlayer()->GetControllerId());
    const FAnalogInputEvent Event(EKeys::Gamepad_LeftY, FModifierKeysState(), User, false, 0, 0, Value);
    FSlateApplication::Get().ProcessAnalogInputEvent(Event);
    return true;
}

AEWPickup* UEWEditorVerificationLibrary::SpawnVerificationPickup(UWorld* World, FVector Location, UEWItemDefinition* Item, int32 Quantity)
{
    if (!World || World->WorldType != EWorldType::PIE || World->GetNetMode() == NM_Client) return nullptr;
    AEWPickup* Pickup = World->SpawnActor<AEWPickup>(Location, FRotator::ZeroRotator);
    Pickup->ItemDefinition = Item;
    Pickup->Quantity = Quantity;
    return Pickup;
}

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
