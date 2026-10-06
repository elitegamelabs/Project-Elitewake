#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "EWEditorVerificationLibrary.generated.h"

class APlayerController;
class UEnhancedInputLocalPlayerSubsystem;
class UWorld;
class AActor;

UCLASS()
class EWEDITOR_API UEWEditorVerificationLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
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
