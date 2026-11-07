#include "EWControllerIcons.h"
#include "Components/RichTextBlock.h"
#include "Engine/Texture2D.h"
#include "Framework/Text/ITextDecorator.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "HAL/PlatformTime.h"

#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
#include <windows.h>
#include "Windows/HideWindowsPlatformTypes.h"
#endif

namespace
{
    constexpr uint32 SonyVendor = 0x054C;
    constexpr uint32 MicrosoftVendor = 0x045E;
    const TCHAR* IconFolder = TEXT("/Game/Elitewake/UI/Icons/Controller");

    /** One gamepad key: its Xbox and PlayStation names, a plain word, and each family's icon (the Home buttons are left out:
     *  both are platform logos, and the game never asks for them). */
    struct FButton { const TCHAR* Key; const TCHAR* Xbox; const TCHAR* PlayStation; const TCHAR* Word; const TCHAR* XboxIcon; const TCHAR* PlayStationIcon; };
    const FButton GamepadButtons[] = {
        {TEXT("Gamepad_FaceButton_Bottom"), TEXT("A"), TEXT("Cross"), TEXT("Bottom button"), TEXT("A"), TEXT("Cross")},
        {TEXT("Gamepad_FaceButton_Right"), TEXT("B"), TEXT("Circle"), TEXT("Right button"), TEXT("B"), TEXT("Circle")},
        {TEXT("Gamepad_FaceButton_Left"), TEXT("X"), TEXT("Square"), TEXT("Left button"), TEXT("X"), TEXT("Square")},
        {TEXT("Gamepad_FaceButton_Top"), TEXT("Y"), TEXT("Triangle"), TEXT("Top button"), TEXT("Y"), TEXT("Triangle")},
        {TEXT("Gamepad_DPad_Up"), TEXT("D-pad Up"), TEXT("D-pad Up"), TEXT("D-pad Up"), TEXT("DPad_Up"), TEXT("DPad_Up")},
        {TEXT("Gamepad_DPad_Down"), TEXT("D-pad Down"), TEXT("D-pad Down"), TEXT("D-pad Down"), TEXT("DPad_Down"), TEXT("DPad_Down")},
        {TEXT("Gamepad_DPad_Left"), TEXT("D-pad Left"), TEXT("D-pad Left"), TEXT("D-pad Left"), TEXT("DPad_Left"), TEXT("DPad_Left")},
        {TEXT("Gamepad_DPad_Right"), TEXT("D-pad Right"), TEXT("D-pad Right"), TEXT("D-pad Right"), TEXT("DPad_Right"), TEXT("DPad_Right")},
        {TEXT("Gamepad_LeftShoulder"), TEXT("LB"), TEXT("L1"), TEXT("Left bumper"), TEXT("LB"), TEXT("L1")},
        {TEXT("Gamepad_RightShoulder"), TEXT("RB"), TEXT("R1"), TEXT("Right bumper"), TEXT("RB"), TEXT("R1")},
        {TEXT("Gamepad_LeftTrigger"), TEXT("LT"), TEXT("L2"), TEXT("Left trigger"), TEXT("LT"), TEXT("L2")},
        {TEXT("Gamepad_LeftTriggerAxis"), TEXT("LT"), TEXT("L2"), TEXT("Left trigger"), TEXT("LT"), TEXT("L2")},
        {TEXT("Gamepad_RightTrigger"), TEXT("RT"), TEXT("R2"), TEXT("Right trigger"), TEXT("RT"), TEXT("R2")},
        {TEXT("Gamepad_RightTriggerAxis"), TEXT("RT"), TEXT("R2"), TEXT("Right trigger"), TEXT("RT"), TEXT("R2")},
        {TEXT("Gamepad_LeftThumbstick"), TEXT("LS"), TEXT("L3"), TEXT("Left stick press"), TEXT("LeftStickPress"), TEXT("L3")},
        {TEXT("Gamepad_RightThumbstick"), TEXT("RS"), TEXT("R3"), TEXT("Right stick press"), TEXT("RightStickPress"), TEXT("R3")},
        {TEXT("Gamepad_Left2D"), TEXT("Left stick"), TEXT("Left stick"), TEXT("Left stick"), TEXT("LeftStick"), TEXT("LeftStick")},
        {TEXT("Gamepad_LeftX"), TEXT("Left stick"), TEXT("Left stick"), TEXT("Left stick"), TEXT("LeftStick"), TEXT("LeftStick")},
        {TEXT("Gamepad_LeftY"), TEXT("Left stick"), TEXT("Left stick"), TEXT("Left stick"), TEXT("LeftStick"), TEXT("LeftStick")},
        {TEXT("Gamepad_Right2D"), TEXT("Right stick"), TEXT("Right stick"), TEXT("Right stick"), TEXT("RightStick"), TEXT("RightStick")},
        {TEXT("Gamepad_RightX"), TEXT("Right stick"), TEXT("Right stick"), TEXT("Right stick"), TEXT("RightStick"), TEXT("RightStick")},
        {TEXT("Gamepad_RightY"), TEXT("Right stick"), TEXT("Right stick"), TEXT("Right stick"), TEXT("RightStick"), TEXT("RightStick")},
        {TEXT("Gamepad_Special_Left"), TEXT("View"), TEXT("Create"), TEXT("Back button"), TEXT("View"), TEXT("Create")},
        {TEXT("Gamepad_Special_Right"), TEXT("Menu"), TEXT("Options"), TEXT("Start button"), TEXT("Menu"), TEXT("Options")},
    };

    const FButton* Find(const FKey& Key)
    {
        const FName Name = Key.GetFName();
        for (const FButton& Button : GamepadButtons) if (Name == FName(Button.Key)) return &Button;
        return nullptr;
    }

    /** Every connected gamepad or joystick's family (Raw Input: HID usage page 1, usage 4 joystick or 5 gamepad). */
    TArray<EEWGamepadFamily> ConnectedPads()
    {
        TArray<EEWGamepadFamily> Pads;
#if PLATFORM_WINDOWS
        UINT Count = 0;
        if (GetRawInputDeviceList(nullptr, &Count, sizeof(RAWINPUTDEVICELIST)) != 0 || Count == 0) return Pads;
        TArray<RAWINPUTDEVICELIST> Devices;
        Devices.SetNumZeroed(Count);
        const UINT Listed = GetRawInputDeviceList(Devices.GetData(), &Count, sizeof(RAWINPUTDEVICELIST));
        if (Listed == UINT(-1)) return Pads;
        for (UINT Index = 0; Index < Listed; ++Index)
        {
            if (Devices[Index].dwType != RIM_TYPEHID) continue;
            RID_DEVICE_INFO Info = {};
            Info.cbSize = sizeof(Info);
            UINT Size = sizeof(Info);
            if (GetRawInputDeviceInfoW(Devices[Index].hDevice, RIDI_DEVICEINFO, &Info, &Size) == UINT(-1)) continue;
            if (Info.hid.usUsagePage != 1 || (Info.hid.usUsage != 4 && Info.hid.usUsage != 5)) continue;
            // An XInput pad's device path carries "IG_" (any maker's Xbox-layout pad).
            bool bXInput = false;
            UINT NameLength = 0;
            GetRawInputDeviceInfoW(Devices[Index].hDevice, RIDI_DEVICENAME, nullptr, &NameLength);
            if (NameLength > 0)
            {
                TArray<TCHAR> Name;
                Name.SetNumZeroed(NameLength + 1);
                if (GetRawInputDeviceInfoW(Devices[Index].hDevice, RIDI_DEVICENAME, Name.GetData(), &NameLength) != UINT(-1))
                    bXInput = FCString::Stristr(Name.GetData(), TEXT("IG_")) != nullptr;
            }
            Pads.Add(FEWControllerIcons::FamilyForVendor(Info.hid.dwVendorId, bXInput));
        }
#endif
        return Pads;
    }
}

EEWGamepadFamily FEWControllerIcons::FamilyForVendor(uint32 VendorId, bool bXInput)
{
    if (VendorId == SonyVendor) return EEWGamepadFamily::PlayStation;
    if (VendorId == MicrosoftVendor || bXInput) return EEWGamepadFamily::Xbox;
    return EEWGamepadFamily::Unknown;
}

EEWGamepadFamily FEWControllerIcons::FamilyOfPads(const TArray<EEWGamepadFamily>& Pads)
{
    if (Pads.Contains(EEWGamepadFamily::PlayStation)) return EEWGamepadFamily::PlayStation;
    if (Pads.Contains(EEWGamepadFamily::Xbox)) return EEWGamepadFamily::Xbox;
    return EEWGamepadFamily::Unknown;
}

EEWGamepadFamily FEWControllerIcons::DetectConnected()
{
    static double CheckedAt = -1.0e9;
    static EEWGamepadFamily Detected = EEWGamepadFamily::Unknown;
    const double Now = FPlatformTime::Seconds();
    if (Now - CheckedAt >= RefreshSeconds)
    {
        CheckedAt = Now;
        Detected = FamilyOfPads(ConnectedPads());
    }
    return Detected;
}

EEWGamepadFamily FEWControllerIcons::Resolve(EEWButtonIconsChoice Choice, EEWGamepadFamily Detected)
{
    switch (Choice)
    {
    case EEWButtonIconsChoice::Xbox: return EEWGamepadFamily::Xbox;
    case EEWButtonIconsChoice::PlayStation: return EEWGamepadFamily::PlayStation;
    default: return Detected;
    }
}

const TCHAR* FEWControllerIcons::FamilyName(EEWGamepadFamily Family)
{
    switch (Family)
    {
    case EEWGamepadFamily::Xbox: return TEXT("Xbox");
    case EEWGamepadFamily::PlayStation: return TEXT("PlayStation");
    default: return TEXT("Unknown");
    }
}

FString FEWControllerIcons::IconName(const FKey& Key, EEWGamepadFamily Family)
{
    const FButton* Button = Find(Key);
    if (!Button || Family == EEWGamepadFamily::Unknown) return FString();
    return FString::Printf(TEXT("T_Icon_%s_%s"), FamilyName(Family), Family == EEWGamepadFamily::Xbox ? Button->XboxIcon : Button->PlayStationIcon);
}

UTexture2D* FEWControllerIcons::IconFor(const FKey& Key, EEWGamepadFamily Family)
{
    const FString Name = IconName(Key, Family);
    if (Name.IsEmpty()) return nullptr;
    // Loaded once and kept for the session: 36 small UI textures.
    static TMap<FString, UTexture2D*> Loaded;
    if (UTexture2D** Found = Loaded.Find(Name)) return *Found;
    const FString Path = FString::Printf(TEXT("%s/%s/%s.%s"), IconFolder, FamilyName(Family), *Name, *Name);
    UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *Path, nullptr, LOAD_Quiet | LOAD_NoWarn);
    if (Texture) Texture->AddToRoot();
    Loaded.Add(Name, Texture);
    return Texture;
}

FString FEWControllerIcons::ButtonName(const FKey& Key, EEWGamepadFamily Family)
{
    const FButton* Button = Find(Key);
    if (!Button) return Key.GetDisplayName().ToString();
    switch (Family)
    {
    case EEWGamepadFamily::Xbox: return Button->Xbox;
    case EEWGamepadFamily::PlayStation: return Button->PlayStation;
    default: return Button->Word;
    }
}

FString FEWControllerIcons::Expand(const FString& Text, EEWGamepadFamily Family, bool bRich)
{
    FString Out;
    Out.Reserve(Text.Len() + 32);
    int32 At = 0;
    while (At < Text.Len())
    {
        const int32 Open = Text.Find(TEXT("[Gamepad_"), ESearchCase::CaseSensitive, ESearchDir::FromStart, At);
        const int32 Close = Open == INDEX_NONE ? INDEX_NONE : Text.Find(TEXT("]"), ESearchCase::CaseSensitive, ESearchDir::FromStart, Open);
        if (Open == INDEX_NONE || Close == INDEX_NONE) { Out += Text.Mid(At); break; }
        Out += Text.Mid(At, Open - At);
        const FKey Key(FName(*Text.Mid(Open + 1, Close - Open - 1)));
        if (bRich && IconFor(Key, Family))
            Out += FString::Printf(TEXT("<btn id=\"%s\" f=\"%s\"/>"), *Key.GetFName().ToString(), FamilyName(Family));
        else
            Out += ButtonName(Key, Family);
        At = Close + 1;
    }
    return Out;
}

namespace
{
    class FEWButtonIconRun : public FRichTextDecorator
    {
    public:
        FEWButtonIconRun(URichTextBlock* InOwner) : FRichTextDecorator(InOwner) {}
        virtual bool Supports(const FTextRunParseResults& RunParseResult, const FString& Text) const override
        {
            return RunParseResult.Name == TEXT("btn") && RunParseResult.MetaData.Contains(TEXT("id"));
        }
    protected:
        virtual TSharedPtr<SWidget> CreateDecoratorWidget(const FTextRunInfo& RunInfo, const FTextBlockStyle& Style) const override
        {
            const FKey Key(FName(*RunInfo.MetaData[TEXT("id")]));
            const FString* Named = RunInfo.MetaData.Find(TEXT("f"));
            const EEWGamepadFamily Family = !Named ? EEWGamepadFamily::Unknown
                : *Named == TEXT("PlayStation") ? EEWGamepadFamily::PlayStation
                : *Named == TEXT("Xbox") ? EEWGamepadFamily::Xbox : EEWGamepadFamily::Unknown;
            UTexture2D* Texture = FEWControllerIcons::IconFor(Key, Family);
            if (!Texture)
                return SNew(STextBlock).TextStyle(&Style).Text(FText::FromString(FEWControllerIcons::ButtonName(Key, Family)));
            // A little taller than the letters (font size is in points; a line is about 4/3 of it in Slate units).
            const float Height = FMath::RoundToFloat(Style.Font.Size * (Texture->GetSurfaceWidth() > 1.4f * Texture->GetSurfaceHeight() ? 2.2f : 1.7f));   // wide shoulder buttons a little taller to read
            const float Width = FMath::RoundToFloat(Height * Texture->GetSurfaceWidth() / FMath::Max(1.f, Texture->GetSurfaceHeight()));
            const FString Id = FString::Printf(TEXT("%s@%.0f"), *Texture->GetName(), Height);
            TSharedRef<FSlateBrush>* Brush = Brushes.Find(Id);
            if (!Brush)
            {
                TSharedRef<FSlateBrush> Made = MakeShared<FSlateBrush>();
                Made->SetResourceObject(Texture);
                Made->ImageSize = FVector2D(Width, Height);
                Brush = &Brushes.Add(Id, Made);
            }
            return SNew(SBox).WidthOverride(Width).HeightOverride(Height).VAlign(VAlign_Center).Padding(FMargin(2.f, 0.f))
            [
                SNew(SImage).Image(&Brush->Get())
            ];
        }
    private:
        mutable TMap<FString, TSharedRef<FSlateBrush>> Brushes;
    };
}

TSharedPtr<ITextDecorator> UEWButtonIconDecorator::CreateDecorator(URichTextBlock* InOwner)
{
    return MakeShared<FEWButtonIconRun>(InOwner);
}
