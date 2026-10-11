#pragma once

#include "CoreMinimal.h"
#include "EWShipTypes.generated.h"

class UEWItemDefinition;

/** What a ship mount accepts. None marks an item that is not a ship fitting. */
UENUM(BlueprintType)
enum class EEWShipMountType : uint8 { None, Helm, Sail, Cannon, Utility };

/** Sail mounts accept only their own size. */
UENUM(BlueprintType)
enum class EEWSailSize : uint8 { None, Small, Medium, Large };

/** A fixed place on a hull where one fitting can be installed. */
USTRUCT(BlueprintType)
struct FEWShipMount
{
    GENERATED_BODY()

    /** Unique within its ship definition; installed fittings refer to it. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    FName MountId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    EEWShipMountType Type = EEWShipMountType::None;
    /** Only used by sail mounts. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    EEWSailSize SailSize = EEWSailSize::None;
    /** Relative to the ship. Players aim here to install, and the fitting mesh attaches here. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    FTransform Transform;
};

/** One installed fitting. Replicated as part of the ship's fitting list. */
USTRUCT(BlueprintType)
struct FEWInstalledFitting
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Ship")
    FName MountId;
    UPROPERTY(BlueprintReadOnly, Category="Ship")
    TObjectPtr<UEWItemDefinition> Item;
};
