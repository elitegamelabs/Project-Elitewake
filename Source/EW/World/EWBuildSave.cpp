#include "World/EWBuildSave.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

namespace
{
    FString MapOf(const UWorld* World) { return UWorld::RemovePIEPrefix(World->GetOutermost()->GetName()); }
}

bool UEWBuildSave::SaveWorld(UWorld* World, const FString& SlotName)
{
    if (!World || World->GetNetMode() == NM_Client) return false;
    auto* Save = Cast<UEWBuildSave>(UGameplayStatics::CreateSaveGameObject(StaticClass()));
    if (!Save) return false;
    Save->MapPath = MapOf(World);
    Save->SavedAt = FDateTime::Now();
    AEWBuildPiece::CaptureAll(World, Save->Pieces);
    return UGameplayStatics::SaveGameToSlot(Save, SlotName, 0);
}

int32 UEWBuildSave::RestoreWorld(UWorld* World, const FString& SlotName)
{
    if (!World || World->GetNetMode() == NM_Client || !UGameplayStatics::DoesSaveGameExist(SlotName, 0)) return 0;
    const auto* Save = Cast<UEWBuildSave>(UGameplayStatics::LoadGameFromSlot(SlotName, 0));
    if (!Save || Save->MapPath != MapOf(World)) return 0;
    for (TActorIterator<AEWBuildPiece> It(World); It; ++It) return 0;      // something already stands: leave it be
    return AEWBuildPiece::RestoreAll(World, Save->Pieces);
}
