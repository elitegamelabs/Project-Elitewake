#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Characters/EWAppearance.h"
#include "EWAppearanceSave.generated.h"

/** The look last made in the character creator, so the next run starts with it. */
UCLASS()
class EW_API UEWAppearanceSave : public USaveGame
{
    GENERATED_BODY()
public:
    static inline const TCHAR* Slot = TEXT("Appearance");
    UPROPERTY()
    FEWAppearance Appearance;
};
