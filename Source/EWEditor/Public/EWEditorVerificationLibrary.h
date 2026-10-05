#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "EWEditorVerificationLibrary.generated.h"

class APlayerController;
class UEnhancedInputLocalPlayerSubsystem;
class UWorld;

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
};
