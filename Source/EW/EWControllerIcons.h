#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Components/RichTextBlockDecorator.h"
#include "EWControllerIcons.generated.h"

class UTexture2D;

/** Which buttons the connected gamepad has printed on it (owner, November 1). Unknown shows plain words, never a guessed symbol. */
UENUM(BlueprintType)
enum class EEWGamepadFamily : uint8 { Unknown, Xbox, PlayStation };

/** The Options choice (Options, "Button icons"): follow the connected pad, or always one family. */
UENUM(BlueprintType)
enum class EEWButtonIconsChoice : uint8 { Automatic, Xbox, PlayStation };

/**
 * Gamepad buttons drawn as the player's own controller shows them (owner, November 1: "whenever they are connected use the
 * appropriate buttons"). The engine names gamepad keys by position (Gamepad_FaceButton_Left is X on an Xbox pad and Square on a
 * PlayStation pad), so bindings never change; only the picture and the word do. The family comes from the USB/Bluetooth vendor of
 * the connected pads (Windows Raw Input): Sony is PlayStation; Microsoft, or any XInput pad (the Xbox layout), is Xbox; anything
 * else is Unknown and gets words ("Left button"). A connected Sony pad wins over an XInput one, because tools such as DS4Windows
 * or Steam present a PlayStation pad to the game as a virtual Xbox pad while the real pad stays visible.
 *
 * Prompt text names a button with a token, [Gamepad_FaceButton_Left]; Expand turns each token into an icon (rich text) or a word.
 */
struct EW_API FEWControllerIcons
{
    /** The family of the pads connected now (cached, looked at again every RefreshSeconds). */
    static EEWGamepadFamily DetectConnected();
    static constexpr double RefreshSeconds = 3.0;
    /** The family a pad's vendor and kind point to. */
    static EEWGamepadFamily FamilyForVendor(uint32 VendorId, bool bXInput);
    /** The family of a set of connected pads: PlayStation if any is Sony, else Xbox if any is Xbox-like, else Unknown. */
    static EEWGamepadFamily FamilyOfPads(const TArray<EEWGamepadFamily>& Pads);
    /** What to show, given the player's choice and what is connected. */
    static EEWGamepadFamily Resolve(EEWButtonIconsChoice Choice, EEWGamepadFamily Detected);

    /** The icon's asset name (T_Icon_Xbox_X, T_Icon_PlayStation_Square), or empty when the family or key has none. */
    static FString IconName(const FKey& Key, EEWGamepadFamily Family);
    /** The icon texture, loaded and kept; null when there is none. */
    static UTexture2D* IconFor(const FKey& Key, EEWGamepadFamily Family);
    /** The button's printed name for the family (X, Square, LB, L1), or a plain word for Unknown (Left button). */
    static FString ButtonName(const FKey& Key, EEWGamepadFamily Family);

    /** Replace each [Gamepad_...] token: with an icon tag (bRich, a family with icons) or the button's name. */
    static FString Expand(const FString& Text, EEWGamepadFamily Family, bool bRich);
    static FText Expand(const FText& Text, EEWGamepadFamily Family, bool bRich) { return FText::FromString(Expand(Text.ToString(), Family, bRich)); }
    /** The token for a key, for building prompt text. */
    static FString Token(const FKey& Key) { return FString::Printf(TEXT("[%s]"), *Key.GetFName().ToString()); }

    static const TCHAR* FamilyName(EEWGamepadFamily Family);
};

/** Draws <btn id="Gamepad_..." f="Xbox"/> in rich text as the button's icon, sized to the text around it. */
UCLASS()
class EW_API UEWButtonIconDecorator : public URichTextBlockDecorator
{
    GENERATED_BODY()
public:
    UEWButtonIconDecorator(const FObjectInitializer& ObjectInitializer) : Super(ObjectInitializer) {}
    virtual TSharedPtr<ITextDecorator> CreateDecorator(URichTextBlock* InOwner) override;
};
