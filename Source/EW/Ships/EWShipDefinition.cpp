#include "EWShipDefinition.h"
#include "EWItemDefinition.h"

const FEWShipMount* UEWShipDefinition::FindMount(FName MountId) const
{
    return MountId.IsNone() ? nullptr : Mounts.FindByPredicate([MountId](const FEWShipMount& M) { return M.MountId == MountId; });
}

bool UEWShipDefinition::Accepts(const FEWShipMount& Mount, const UEWItemDefinition* Item)
{
    if (!Item || Mount.Type == EEWShipMountType::None || Item->FittingMountType != Mount.Type) return false;
    return Mount.Type != EEWShipMountType::Sail
        || (Mount.SailSize != EEWSailSize::None && Item->FittingSailSize == Mount.SailSize);
}

FString UEWShipDefinition::Validate() const
{
    if (ShipId.IsNone()) return TEXT("ShipId is empty");
    if (HullExtent.GetMin() <= 0) return TEXT("HullExtent must be positive");
    TSet<FName> Seen;
    for (const FEWShipMount& Mount : Mounts)
    {
        if (Mount.MountId.IsNone()) return TEXT("a mount has no MountId");
        if (Seen.Contains(Mount.MountId)) return FString::Printf(TEXT("duplicate mount %s"), *Mount.MountId.ToString());
        Seen.Add(Mount.MountId);
        if (Mount.Type == EEWShipMountType::None) return FString::Printf(TEXT("mount %s has no type"), *Mount.MountId.ToString());
        if ((Mount.Type == EEWShipMountType::Sail) != (Mount.SailSize != EEWSailSize::None))
            return FString::Printf(TEXT("mount %s: only sail mounts have a sail size, and every sail mount needs one"), *Mount.MountId.ToString());
    }
    return FString();
}

FPrimaryAssetId UEWShipDefinition::GetPrimaryAssetId() const
{
    return FPrimaryAssetId(TEXT("EWShip"), ShipId.IsNone() ? GetFName() : ShipId);
}
