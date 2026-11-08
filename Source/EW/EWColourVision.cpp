#include "EWColourVision.h"
#include "Misc/ConfigCacheIni.h"

namespace EWCue
{
namespace
{
bool bLoaded = false;
EEWColourVision Mode = EEWColourVision::Standard;

void Load()
{
    if (bLoaded) return;
    bLoaded = true;
    int32 Saved = 0;
    if (GConfig) GConfig->GetInt(TEXT("Elitewake.UserControls"), TEXT("ColourVision"), Saved, GGameUserSettingsIni);
    Mode = static_cast<EEWColourVision>(FMath::Clamp(Saved, 0, 2));
}

FLinearColor Pick(const FLinearColor& Standard, const FLinearColor& RedGreen, const FLinearColor& BlueYellow)
{
    Load();
    return Mode == EEWColourVision::RedGreen ? RedGreen : Mode == EEWColourVision::BlueYellow ? BlueYellow : Standard;
}
}

EEWColourVision GetMode()
{
    Load();
    return Mode;
}

void SetMode(EEWColourVision NewMode)
{
    bLoaded = true;
    Mode = NewMode;
    if (GConfig)
    {
        GConfig->SetInt(TEXT("Elitewake.UserControls"), TEXT("ColourVision"), int32(Mode), GGameUserSettingsIni);
        GConfig->Flush(false, GGameUserSettingsIni);
    }
}

FText ModeName(EEWColourVision Of)
{
    switch (Of)
    {
    case EEWColourVision::RedGreen: return NSLOCTEXT("Elitewake", "ColourVisionRedGreen", "Red-green");
    case EEWColourVision::BlueYellow: return NSLOCTEXT("Elitewake", "ColourVisionBlueYellow", "Blue-yellow");
    default: return NSLOCTEXT("Elitewake", "ColourVisionStandard", "Standard");
    }
}

// Okabe-Ito: sky blue (.34,.71,.91), orange (.90,.62,0), bluish green (0,.62,.45), vermilion (.84,.37,0), reddish purple (.80,.47,.65).
FLinearColor Good() { return Pick(FLinearColor(.45f, 1.f, .45f), FLinearColor(.34f, .71f, .91f), FLinearColor(0.f, .62f, .45f)); }
FLinearColor Warning() { return Pick(FLinearColor(1.f, .72f, .25f), FLinearColor(.9f, .62f, 0.f), FLinearColor(.84f, .37f, 0.f)); }
FLinearColor Cold() { return Pick(FLinearColor(.45f, .75f, 1.f), FLinearColor(.34f, .71f, .91f), FLinearColor(0.f, .62f, .45f)); }
FLinearColor Hot() { return Pick(FLinearColor(1.f, .55f, .2f), FLinearColor(.9f, .62f, 0.f), FLinearColor(.80f, .47f, .65f)); }
}
