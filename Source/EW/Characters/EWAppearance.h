#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EWAppearance.generated.h"

class USkeletalMesh;
class USkinnedMeshComponent;
class UMaterialInterface;

/** One body a survivor can be made from, and how its colouring is chosen. */
USTRUCT(BlueprintType)
struct FEWBodyOption
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    FText DisplayName;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TSoftObjectPtr<USkeletalMesh> Mesh;
    /** If set, the body is dressed in this material (every slot) before it is toned. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TSoftObjectPtr<UMaterialInterface> ToneMaterial;
    /** Vector material parameters on the body that take the chosen tone. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TArray<FName> ToneParameters;
};

/** The bodies and tones offered when a survivor is made. Bodies can be added without code. */
UCLASS(BlueprintType)
class EW_API UEWBodyRoster : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TArray<FEWBodyOption> Bodies;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TArray<FLinearColor> Tones;
};

/** Where a slider belongs in the character creator. */
UENUM(BlueprintType)
enum class EEWLookGroup : uint8 { Body, Head, Brows, Eyes, Nose, Cheeks, Mouth, Jaw, Ears, Skin, Makeup };

/**
 * One slider of the character creator (owner, November 7: every face and body feature). 0 to 1, a half is as made.
 * Sliders on the mannequin's bones reshape the preview now; the face's are kept for the real character model (Phase 5),
 * which has a face to shape.
 */
struct FEWLookSlider
{
    const TCHAR* Id;
    EEWLookGroup Group;
    const TCHAR* Label;
    /** Bones it scales on the preview (none: kept for the real model), each by Low at 0 and High at 1, in the bone's own axes. */
    TArray<FName> Bones;
    FVector Low = FVector::OneVector;
    FVector High = FVector::OneVector;
    /** Carried down to every bone below (a hand with its fingers), not just the bones named. */
    bool bWholeLimb = false;
};

/** One list of choices (hair styles, beard, eye colour...), shown by name. */
struct FEWLookChoice
{
    const TCHAR* Id;
    const TCHAR* Label;
    TArray<const TCHAR*> Options;
};

/** A tattoo the player composes: a design, where it sits, its size and turn, and its ink. */
USTRUCT(BlueprintType)
struct FEWTattoo
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") uint8 Design = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") uint8 Place = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") uint8 Size = 128;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") uint8 Angle = 128;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") uint8 Ink = 0;
    bool operator==(const FEWTattoo& O) const { return Design == O.Design && Place == O.Place && Size == O.Size && Angle == O.Angle && Ink == O.Ink; }
};

/** How a survivor looks. Small and replicated; every machine builds the look from it. */
USTRUCT(BlueprintType)
struct FEWAppearance
{
    GENERATED_BODY()
    /** The body from the roster: 0 the man, 1 the woman. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    uint8 Body = 0;
    /** The roster colouring the creator last offered as a swatch (kept for older saves; the Skin tone slider is the colour). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    uint8 Tone = 0;
    /** Height relative to the body's own, 1 = as made (tuning range MinHeight-MaxHeight). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    float Height = 1.f;
    /** The preset the look started from. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    uint8 Preset = 0;
    /** Every slider but height, in the order of Sliders(), 0-255 (128 as made). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    TArray<uint8> Features;
    /** Every list choice, in the order of Choices(). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    TArray<uint8> Picks;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    TArray<FEWTattoo> Tattoos;

    static constexpr float MinHeight = .88f;
    static constexpr float MaxHeight = 1.12f;
    static constexpr int32 MaxTattoos = 6;

    /** Every slider, height first (stored in Height, not Features). */
    static const TArray<FEWLookSlider>& Sliders();
    static const TArray<FEWLookChoice>& Choices();
    static int32 SliderIndex(const TCHAR* Id);
    static int32 ChoiceIndex(const TCHAR* Id);
    /** Tattoo designs, places and inks offered. */
    static const TArray<const TCHAR*>& TattooDesigns();
    static const TArray<const TCHAR*>& TattooPlaces();
    static const TArray<const TCHAR*>& TattooInks();
    /** The presets each body starts from. */
    static const TArray<const TCHAR*>& PresetNames();

    float GetSlider(int32 Index) const;
    void SetSlider(int32 Index, float Value);
    int32 GetPick(int32 Index) const { return Picks.IsValidIndex(Index) ? Picks[Index] : 0; }
    void SetPick(int32 Index, int32 Value);
    /** The skin's colour: the Skin tone slider across the roster's colourings, warmed or cooled by Undertone. */
    FLinearColor SkinColour(const UEWBodyRoster* Roster) const;
    /** Starts over from a preset of this body (keeps the body). */
    void ApplyPreset(int32 PresetIndex);
    /** A believable look at random, for the body chosen. */
    void Randomise(int32 Seed);

    bool operator==(const FEWAppearance& Other) const
    {
        return Body == Other.Body && Tone == Other.Tone && Height == Other.Height && Preset == Other.Preset
            && Features == Other.Features && Picks == Other.Picks && Tattoos == Other.Tattoos;
    }
    /** Brought within what the roster and the creator offer, so a bad request can never break a survivor. */
    FEWAppearance Clamped(const UEWBodyRoster* Roster) const;
    /** Dresses a mesh in this look: its body, skin, height and build. Returns false if the roster lacks the body. */
    bool ApplyTo(USkinnedMeshComponent* Mesh, const UEWBodyRoster* Roster) const;
    /** Each bone's scale in its own axes from the sliders on bones (the preview's shaping), by bone index. */
    void BoneScales(const USkinnedMeshComponent* Mesh, TArray<FVector>& OutScales) const;
};
