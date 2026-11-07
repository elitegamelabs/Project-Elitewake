// Copyright Elite Game Labs. All Rights Reserved.

#include "EWItemDefinition.h"

FPrimaryAssetId UEWItemDefinition::GetPrimaryAssetId() const
{
	const FName AssetName = ItemId.IsNone() ? GetFName() : ItemId;
	return FPrimaryAssetId(TEXT("EWItem"), AssetName);
}
