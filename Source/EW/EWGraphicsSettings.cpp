#include "EWGraphicsSettings.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"

namespace
{
    UGameUserSettings* Settings() { return GEngine ? GEngine->GetGameUserSettings() : nullptr; }

    void ApplyAndSave(UGameUserSettings* S)
    {
        S->ApplyNonResolutionSettings();
        S->SaveSettings();
    }
}

int32 FEWGraphicsSettings::Get(EGroup Group)
{
    const UGameUserSettings* S = Settings();
    if (!S) return Levels - 1;
    switch (Group)
    {
    case EGroup::Textures: return S->GetTextureQuality();
    case EGroup::Shadows: return S->GetShadowQuality();
    case EGroup::Foliage: return S->GetFoliageQuality();
    case EGroup::Reflections: return S->GetReflectionQuality();
    case EGroup::Effects: return S->GetVisualEffectQuality();
    default: return Levels - 1;
    }
}

void FEWGraphicsSettings::Set(EGroup Group, int32 Level)
{
    UGameUserSettings* S = Settings();
    if (!S) return;
    Level = FMath::Clamp(Level, 0, Levels - 1);
    switch (Group)
    {
    case EGroup::Textures: S->SetTextureQuality(Level); break;
    case EGroup::Shadows: S->SetShadowQuality(Level); break;
    case EGroup::Foliage: S->SetFoliageQuality(Level); break;
    case EGroup::Reflections: S->SetReflectionQuality(Level); S->SetShadingQuality(Level); break;
    case EGroup::Effects: S->SetVisualEffectQuality(Level); S->SetPostProcessingQuality(Level); break;
    default: return;
    }
    ApplyAndSave(S);
}

void FEWGraphicsSettings::SetOverall(int32 Level)
{
    UGameUserSettings* S = Settings();
    if (!S) return;
    // Every engine group, global illumination and view distance included; view distance and plant density read the same at
    // every level (Config/DefaultScalability.ini), so it changes nothing a survivor can see.
    S->SetOverallScalabilityLevel(FMath::Clamp(Level, 0, Levels - 1));
    ApplyAndSave(S);
}

int32 FEWGraphicsSettings::GetOverall()
{
    const int32 First = Get(EGroup::Textures);
    for (int32 Index = 1; Index < GroupCount; ++Index)
        if (Get(static_cast<EGroup>(Index)) != First) return INDEX_NONE;
    return First;
}

FText FEWGraphicsSettings::LevelName(int32 Level)
{
    switch (Level)
    {
    case 0: return NSLOCTEXT("Elitewake", "QualityLow", "Low");
    case 1: return NSLOCTEXT("Elitewake", "QualityMedium", "Medium");
    case 2: return NSLOCTEXT("Elitewake", "QualityHigh", "High");
    case 3: return NSLOCTEXT("Elitewake", "QualityEpic", "Epic");
    default: return NSLOCTEXT("Elitewake", "QualityCustom", "Custom");
    }
}

FText FEWGraphicsSettings::GroupName(EGroup Group)
{
    switch (Group)
    {
    case EGroup::Textures: return NSLOCTEXT("Elitewake", "GraphicsTextures", "Textures");
    case EGroup::Shadows: return NSLOCTEXT("Elitewake", "GraphicsShadows", "Shadows");
    case EGroup::Foliage: return NSLOCTEXT("Elitewake", "GraphicsFoliage", "Foliage detail");
    case EGroup::Reflections: return NSLOCTEXT("Elitewake", "GraphicsReflections", "Water and reflections");
    case EGroup::Effects: return NSLOCTEXT("Elitewake", "GraphicsEffects", "Effects");
    default: return FText::GetEmpty();
    }
}
