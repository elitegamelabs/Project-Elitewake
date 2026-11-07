#pragma once

#include "CoreMinimal.h"

/**
 * The player's graphics quality (CLAUDE.md 9.6; owner, November 1): an overall Low / Medium / High / Epic preset and five
 * groups, kept by the engine's UGameUserSettings (GameUserSettings.ini). Stronger graphics cards show higher-resolution textures,
 * better shadows, foliage detail, water and reflections, and effects; gameplay is identical on every tier: what hides a
 * survivor (grass and plant density, view distance) is held the same at every level by Config/DefaultScalability.ini.
 */
struct EW_API FEWGraphicsSettings
{
    enum class EGroup : uint8 { Textures, Shadows, Foliage, Reflections, Effects, Count };
    static constexpr int32 GroupCount = static_cast<int32>(EGroup::Count);
    static constexpr int32 Levels = 4;     // 0 Low, 1 Medium, 2 High, 3 Epic

    /** A group's level, 0 to 3. */
    static int32 Get(EGroup Group);
    /** Set one group (Effects also sets post-processing; Reflections also shading, for the water), apply and save. */
    static void Set(EGroup Group, int32 Level);
    /** Set every group (and global illumination) to one level, apply and save. */
    static void SetOverall(int32 Level);
    /** The level every group shares, or INDEX_NONE when they differ (a custom mix). */
    static int32 GetOverall();
    /** "Low", "Medium", "High", "Epic" (or "Custom" for INDEX_NONE). */
    static FText LevelName(int32 Level);
    static FText GroupName(EGroup Group);
};
