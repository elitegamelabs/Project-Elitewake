#include "EWSurvivorSave.h"
#include "EWCharacter.h"
#include "EWHotbarComponent.h"
#include "EWStarterKit.h"
#include "EWSurvivalComponent.h"
#include "EWProgressionComponent.h"
#include "EWExplorationComponent.h"
#include "EWGameMode.h"
#include "EWPlayerController.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "Kismet/GameplayStatics.h"

namespace
{
    /** The map's package, without the PIE prefix, so a save made in Play matches the packaged map. */
    FString MapOf(const AActor* Actor)
    {
        const UWorld* World = Actor ? Actor->GetWorld() : nullptr;
        return World ? UWorld::RemovePIEPrefix(World->GetOutermost()->GetName()) : FString();
    }
}

bool UEWSurvivorSave::SaveSurvivor(AEWCharacter* Survivor, const FString& SlotName)
{
    if (!Survivor || !Survivor->HasAuthority()) return false;
    auto* Save = Cast<UEWSurvivorSave>(UGameplayStatics::CreateSaveGameObject(StaticClass()));
    if (!Save) return false;
    Save->MapPath = MapOf(Survivor);
    Save->SavedAt = FDateTime::Now();
    Save->Location = Survivor->GetActorLocation();
    Save->Facing = Survivor->GetController() ? Survivor->GetController()->GetControlRotation() : Survivor->GetActorRotation();
    if (const auto* Needs = Survivor->GetSurvivalComponent())
    {
        Save->Health = Needs->GetHealth();
        Save->Hunger = Needs->GetHunger();
        Save->Hydration = Needs->GetHydration();
    }
    if (const auto* Pack = Survivor->GetInventoryComponent()) Save->Inventory = Pack->Entries;
    if (const auto* Worn = Survivor->GetEquipmentComponent()) Save->Equipment = Worn->GetEquipmentEntries();
    if (const auto* Bar = Survivor->GetHotbarComponent())
        for (int32 i = 0; i < UEWHotbarComponent::SlotCount; ++i) Save->Hotbar.Add(Bar->GetBoundItem(i));
    if (const auto* Progress = Survivor->GetProgressionComponent())
    {
        Save->Level = Progress->GetLevel(); Save->Experience = Progress->GetExperience(); Save->UnspentStatPoints = Progress->GetUnspentPoints();
        Save->StatPoints = Progress->GetAllStatPoints(); Save->SkillPoints = Progress->GetSkillPoints(); Save->UnlockedSkills = Progress->GetUnlockedSkills();
    }
    if (const auto* Controller = Cast<AEWPlayerController>(Survivor->GetController()))
        if (const UEWExplorationComponent* Explored = Controller->GetExploration())
            if (Explored->GetBoundsSize() > 0.f)
            {
                const TArray<uint8>& Cells = Explored->GetCells();
                Save->ExploredBits.Init(0, (Cells.Num() + 7) / 8);
                for (int32 i = 0; i < Cells.Num(); ++i) if (Cells[i]) Save->ExploredBits[i >> 3] |= uint8(1 << (i & 7));
                Save->ExploredMin = Explored->GetBoundsMin(); Save->ExploredSize = Explored->GetBoundsSize();
            }
    AEWBuildPiece::CaptureAll(Survivor->GetWorld(), Save->BuiltPieces);
    return UGameplayStatics::SaveGameToSlot(Save, SlotName, 0);
}

bool UEWSurvivorSave::HasSave(const FString& SlotName)
{
    return UGameplayStatics::DoesSaveGameExist(SlotName, 0);
}

UEWSurvivorSave* UEWSurvivorSave::LoadSave(const FString& SlotName)
{
    return Cast<UEWSurvivorSave>(UGameplayStatics::LoadGameFromSlot(SlotName, 0));
}

bool UEWSurvivorSave::ApplyTo(AEWCharacter* Survivor) const
{
    if (!Survivor || !Survivor->HasAuthority() || MapPath != MapOf(Survivor)) return false;
    auto* Pack = Survivor->GetInventoryComponent();
    auto* Worn = Survivor->GetEquipmentComponent();
    if (!Pack || !Worn) return false;
    // The starter supplies are part of what was saved: hand them over now so they cannot arrive again on top.
    for (TActorIterator<AEWStarterKit> It(Survivor->GetWorld()); It; ++It) It->GiveKit(Survivor);
    Survivor->CancelRestrictedActions();
    for (const FEWEquipmentEntry& Entry : Worn->GetEquipmentEntries())
        if (Entry.ItemDefinition) Worn->UnequipItem(Entry.Slot);
    // An item that no longer exists in the game is left out. Equipped items go back through the inventory so
    // they are equipped the ordinary way.
    TArray<FEWInventoryEntry> Entries = Inventory.FilterByPredicate([](const FEWInventoryEntry& E) { return E.ItemDefinition && E.Quantity > 0; });
    for (const FEWEquipmentEntry& Entry : Equipment)
        if (Entry.ItemDefinition) UEWInventoryComponent::AddToEntries(Entries, Pack->MaxSlots, Entry.ItemDefinition, 1);
    Pack->Entries = MoveTemp(Entries);
    Pack->HandleInventoryChanged();
    for (const FEWEquipmentEntry& Entry : Equipment)
        if (Entry.ItemDefinition) Worn->EquipItem(Entry.ItemDefinition, Entry.Slot);
    if (auto* Bar = Survivor->GetHotbarComponent())
        for (int32 i = 0; i < UEWHotbarComponent::SlotCount; ++i) Bar->BindItem(i, Hotbar.IsValidIndex(i) ? Hotbar[i].Get() : nullptr);
    // Levels first: their health bonus raises the maximum before the saved health is put back.
    if (Level > 0)
        if (auto* Progress = Survivor->GetProgressionComponent())
            Progress->Restore(Level, Experience, UnspentStatPoints, StatPoints, SkillPoints, UnlockedSkills);
    if (auto* Needs = Survivor->GetSurvivalComponent())
    {
        const float Change = Health - Needs->GetHealth();
        if (Change < 0.f) Needs->ApplyDamage(-Change);
        else if (Change > 0.f) Needs->RestoreHealth(Change);
        Needs->SetHunger(Hunger);
        Needs->SetHydration(Hydration);
    }
    if (ExploredSize > 0.f)
        if (auto* Controller = Cast<AEWPlayerController>(Survivor->GetController()))
            if (UEWExplorationComponent* Explored = Controller->GetExploration())
            {
                TArray<uint8> Cells; Cells.Init(0, UEWExplorationComponent::GridSize * UEWExplorationComponent::GridSize);
                for (int32 i = 0; i < Cells.Num() && (i >> 3) < ExploredBits.Num(); ++i) if (ExploredBits[i >> 3] & (1 << (i & 7))) Cells[i] = 255;
                Explored->LoadCells(Cells, ExploredMin, ExploredSize);
                // The server's own edge grows to where this survivor has been, so teleports do not fire inside their explored map.
                if (const AEWGameMode* Mode = Survivor->GetWorld() ? Survivor->GetWorld()->GetAuthGameMode<AEWGameMode>() : nullptr)
                    if (Mode->WorldEdge) Mode->WorldEdge->GrowToCover(ExploredSize);
            }
    // What was built comes back (a map loaded fresh has none; pieces already standing are left alone).
    if (BuiltPieces.Num() > 0 && Survivor->GetWorld())
    {
        bool bAny = false;
        for (TActorIterator<AEWBuildPiece> It(Survivor->GetWorld()); It; ++It) { bAny = true; break; }
        if (!bAny) AEWBuildPiece::RestoreAll(Survivor->GetWorld(), BuiltPieces);
    }
    Survivor->TeleportTo(Location, FRotator(0.f, Facing.Yaw, 0.f), false, true);
    if (AController* Controller = Survivor->GetController()) Controller->SetControlRotation(Facing);
    return true;
}
