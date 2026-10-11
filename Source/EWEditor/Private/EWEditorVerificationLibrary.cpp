#include "EWEditorVerificationLibrary.h"
#include "Editor.h"
#include "Settings/LevelEditorPlaySettings.h"
#include "EWCompanyComponent.h"
#include "EWPlayerController.h"
#include "Engine/World.h"

bool UEWEditorVerificationLibrary::SendVerificationCompanyCommand(AEWPlayerController* Controller, EEWCompanyAction Action, const FString& Text, int32 TargetPlayerId)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType!=EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor,false);
    Controller->GetCompanyComponent()->ServerCommand(Action,Text,TargetPlayerId); return true;
}
bool UEWEditorVerificationLibrary::SendVerificationCompanyPolicy(AEWPlayerController* Controller,int32 Kind,EEWCompanyOwnership Policy)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType!=EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor,false);
    Controller->GetCompanyComponent()->ServerSetPolicy(Kind,Policy); return true;
}
#include "InputKeyEventArgs.h"
#include "EWCharacter.h"
#include "EWCraftingRecipe.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "Engine/NetDriver.h"
#include "EWPickup.h"
#include "EWInnTorchPickup.h"
#include "EWPlayerController.h"
#include "EWInventoryComponent.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
#include "EWStation.h"
#include "EWResourceNode.h"
#include "Survival/EWWaterSource.h"
#include "Gathering/EWHandGatherable.h"
#include "Gathering/EWHarvestTree.h"
#include "Gathering/EWMineable.h"

bool UEWEditorVerificationLibrary::AdvanceVerificationFoodClock(AActor* Owner, float RealSeconds)
{
    if (!Owner || !Owner->HasAuthority() || Owner->GetWorld()->WorldType != EWorldType::PIE
        || !FMath::IsFinite(RealSeconds) || RealSeconds < 0.f) return false;
    auto* Inventory = Owner->FindComponentByClass<UEWInventoryComponent>();
    if (!Inventory) return false;
    Inventory->LastFoodClockSeconds -= RealSeconds;
    Inventory->RefreshFoodAge();
    return true;
}
bool UEWEditorVerificationLibrary::SendVerificationFoodRequest(AEWPlayerController* Controller, UEWItemDefinition* Item)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType != EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor, false);
    Controller->RequestConsumeFood(Item);
    return true;
}

AEWMineable* UEWEditorVerificationLibrary::SpawnVerificationMineable(UWorld* World, FVector Location, UEWItemDefinition* Resource, int32 Quantity)
{
    if (!World || World->WorldType != EWorldType::PIE || World->GetNetMode() == NM_Client || !IsValid(Resource) || Quantity <= 0) return nullptr;
    auto* Node = World->SpawnActor<AEWMineable>(Location, FRotator::ZeroRotator);
    if (Node) { Node->Resource = Resource; Node->Remaining = Quantity; Node->ForceNetUpdate(); }
    return Node;
}

AEWHarvestTree* UEWEditorVerificationLibrary::SpawnVerificationHarvestTree(UWorld* World, FVector Location, UEWItemDefinition* Wood, UEWItemDefinition* Thatch)
{
    if (!World || World->WorldType != EWorldType::PIE || World->GetNetMode() == NM_Client) return nullptr;
    auto* Tree = World->SpawnActor<AEWHarvestTree>(Location, FRotator::ZeroRotator);
    if (Tree) { Tree->Wood = Wood; Tree->Thatch = Thatch; Tree->ForceNetUpdate(); }
    return Tree;
}
bool UEWEditorVerificationLibrary::SendVerificationAttack(AEWPlayerController* Controller, AActor* Target)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType != EWorldType::PIE) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor, false);
    Controller->ServerAttack(Target); return true;
}

AEWHandGatherable* UEWEditorVerificationLibrary::SpawnVerificationHandGatherable(UWorld* World, FVector Location, UEWItemDefinition* Item, int32 Quantity, bool bSticks)
{
    if (!World || World->WorldType != EWorldType::PIE || World->GetNetMode() == NM_Client || !IsValid(Item) || Quantity <= 0) return nullptr;
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Node = World->SpawnActor<AEWHandGatherable>(Location, FRotator::ZeroRotator, Spawn);
    if (Node)
    {
        Node->ItemDefinition = Item; Node->Quantity = Quantity;
        Node->GatheringKind = bSticks ? EEWHandGatheringKind::LooseSticks : EEWHandGatheringKind::PlantFiber;
        Node->ForceNetUpdate();
    }
    return Node;
}

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

AEWInnTorchPickup* UEWEditorVerificationLibrary::SpawnVerificationInnTorch(UWorld* World, FVector Location, UEWItemDefinition* Item)
{
    if (!World || !World->IsGameWorld() || World->GetNetMode()==NM_Client || !Item) return nullptr;
    auto* Torch = World->SpawnActor<AEWInnTorchPickup>(Location, FRotator::ZeroRotator);
    if (Torch) Torch->ItemDefinition=Item;
    return Torch;
}

AEWCharacter* UEWEditorVerificationLibrary::SpawnVerificationRecipeCharacter(UWorld* World,
    TSubclassOf<AEWCharacter> CharacterClass, FVector Location, const TArray<UEWCraftingRecipe*>& Recipes)
{
    if (!World || World->WorldType!=EWorldType::PIE || World->GetNetMode()==NM_Client || !CharacterClass) return nullptr;
    const FTransform Transform(FRotator::ZeroRotator, Location);
    auto* Pawn = World->SpawnActorDeferred<AEWCharacter>(CharacterClass, Transform, nullptr, nullptr,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!Pawn) return nullptr;
    auto* Inventory = Pawn->GetInventoryComponent();
    Inventory->StartingRecipes.Reset();
    for (auto* Recipe : Recipes) Inventory->StartingRecipes.Add(Recipe);
    Pawn->FinishSpawning(Transform);
    return Pawn;
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
bool UEWEditorVerificationLibrary::SendVerificationGameplayKey(AEWPlayerController* Controller, FName KeyName)
{
    if (!Controller || !Controller->IsLocalPlayerController() || Controller->GetWorld()->WorldType != EWorldType::PIE) return false;
    const FKey Key(KeyName); if (!Key.IsValid()) return false;
    TGuardValue<bool> ScriptGuard(GAllowActorScriptExecutionInEditor,false);
    FInputKeyEventArgs Args; Args.Key=Key; Args.Event=IE_Pressed; Args.AmountDepressed=1.f;
    const bool Handled=Controller->InputKey(Args);
    Args.Event=IE_Released; Args.AmountDepressed=0.f; Controller->InputKey(Args);
    return Handled;
}

bool UEWEditorVerificationLibrary::StartVerificationPlaySession(int32 NumPlayers)
{
    if (!GEditor || GEditor->PlayWorld || GEditor->IsPlaySessionInProgress()) return false;
    ULevelEditorPlaySettings* Settings = DuplicateObject(GetDefault<ULevelEditorPlaySettings>(), GetTransientPackage());
    Settings->SetPlayNetMode(EPlayNetMode::PIE_ListenServer);
    Settings->SetPlayNumberOfClients(FMath::Clamp(NumPlayers, 1, 4));
    Settings->SetRunUnderOneProcess(true);
    FRequestPlaySessionParams Params;
    Params.WorldType = EPlaySessionWorldType::PlayInEditor;
    Params.SessionDestination = EPlaySessionDestinationType::InProcess;
    Params.EditorPlaySettings = Settings;
    GEditor->RequestPlaySession(Params);
    return true;
}

bool UEWEditorVerificationLibrary::StopVerificationPlaySession()
{
    if (!GEditor || !GEditor->IsPlaySessionInProgress()) return false;
    GEditor->RequestEndPlayMap();
    return true;
}
