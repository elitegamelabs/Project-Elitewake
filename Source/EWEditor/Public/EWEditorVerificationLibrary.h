#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "EWItemDefinition.h"
#include "EWEditorVerificationLibrary.generated.h"

class AEWPickup;
class AEWPlayerController;
class UEWItemDefinition;

class APlayerController;
class UEnhancedInputLocalPlayerSubsystem;
class UWorld;
class AActor;

UCLASS()
class EWEDITOR_API UEWEditorVerificationLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static bool FlushVerificationInput(AEWPlayerController* Controller);
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static bool SendVerificationHotbarRequest(AEWPlayerController* Controller, int32 Slot, UEWItemDefinition* Item, bool bActivate = false);
    /** Separate press/release permits real held-LB and release-order regression checks. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static bool SendVerificationUIKeyEvent(APlayerController* Controller, FName KeyName, bool bPressed);
    /** Normal owned-controller equipment intent with editor script RPC bypass disabled in this scope. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static bool SendVerificationEquipmentRequest(AEWPlayerController* Controller, UEWItemDefinition* Item, EEWEquipmentSlot Slot, bool bUnequip = false);
    /** Route normal Slate input to the focused local PIE UI, including gamepad keys/axes. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static bool SendVerificationUIKey(APlayerController* Controller, FName KeyName);
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static bool SendVerificationUIAnalog(APlayerController* Controller, float Value);
    /** PIE authority-only pickup fixture; not part of game targets. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor Verification")
    static AEWPickup* SpawnVerificationPickup(UWorld* World, FVector Location, UEWItemDefinition* Item, int32 Quantity);
    /** Access normal Enhanced Input injection for scripted editor Play verification. */
    UFUNCTION(BlueprintPure, Category="Elitewake|Editor|Verification")
    static UEnhancedInputLocalPlayerSubsystem* GetPlayerInputSubsystem(APlayerController* Controller);

    /** Enumerate in-process PIE worlds for host/client verification. */
    UFUNCTION(BlueprintPure, Category="Elitewake|Editor|Verification")
    static TArray<UWorld*> GetPlayWorlds();

    /** Temporary blocking geometry in a Play world; never saves or edits a map. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static AActor* SpawnVerificationBox(UWorld* World, FVector Location, FVector Extent, FRotator Rotation);

    UFUNCTION(BlueprintPure, Category="Elitewake|Editor|Verification")
    static FIntPoint GetVerificationNetworkSettings(UWorld* World);

    /** Apply bounded packet emulation to an existing PIE driver only. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Verification")
    static bool SetVerificationNetworkSettings(UWorld* World, int32 LagMilliseconds, int32 LossPercent);
};
