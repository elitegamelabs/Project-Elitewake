#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "EWAnimationEditorLibrary.generated.h"

class UBlendSpace;

/** Editor asset preparation that is not exposed by Unreal's stock Python bindings. */
UCLASS()
class EWEDITOR_API UEWAnimationEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Validate samples and build the runtime triangulation after editing a blend space. */
    UFUNCTION(BlueprintCallable, Category="Elitewake|Editor|Animation")
    static bool CompileBlendSpace(UBlendSpace* BlendSpace);
};
