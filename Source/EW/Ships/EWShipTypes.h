#pragma once

#include "CoreMinimal.h"
#include "EWShipTypes.generated.h"

class UEWItemDefinition;
class UStaticMesh;

/** What a ship mount accepts. None marks an item that is not a ship fitting. */
UENUM(BlueprintType)
enum class EEWShipMountType : uint8 { None, Helm, Sail, Cannon, Utility, Railing };

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
    /** Optional: how whatever is fitted here looks, instead of the item's own mesh. A ship's rig shapes its sails,
     *  so the same Small sail is a jib on one hull and sets on a short mast on another. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship|Look")
    TSoftObjectPtr<UStaticMesh> FittedMesh;
    /** Sails only: shown while furled, replacing the item's furled mesh. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship|Look")
    TSoftObjectPtr<UStaticMesh> FittedFurledMesh;
    /** Relative to the mount; used with FittedMesh. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship|Look")
    FTransform FittedMeshTransform;
    /** A place that only exists with a module on another mount (owner, October 17: a two-cannon railing module opens
     *  two cannon places behind it): that railing mount, and which of its module's cannon places this is (1-based).
     *  None: always open. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    FName ParentMount;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    int32 ParentSlot = 0;
    /** Shown, and solid, while nothing is fitted here (owner, October 17: a railing hardpoint carries a plain railing
     *  until another module replaces it; taking that module off brings the plain railing back). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship|Look")
    TSoftObjectPtr<UStaticMesh> EmptyMesh;
};

/** One installed fitting. Replicated as part of the ship's fitting list. */
USTRUCT(BlueprintType)
struct FEWInstalledFitting
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    FName MountId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship")
    TObjectPtr<UEWItemDefinition> Item;
};
