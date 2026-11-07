#include "Characters/EWAppearance.h"
#include "Components/SkinnedMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkinnedAsset.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Math/RandomStream.h"

namespace
{
TArray<FName> Both(std::initializer_list<const TCHAR*> Stems)
{
    TArray<FName> Out;
    for (const TCHAR* Stem : Stems)
    {
        Out.Add(FName(FString(Stem) + TEXT("_l")));
        Out.Add(FName(FString(Stem) + TEXT("_r")));
    }
    return Out;
}

FEWLookSlider Shape(const TCHAR* Id, EEWLookGroup Group, const TCHAR* Label, TArray<FName> Bones, const FVector& Low, const FVector& High, bool bWholeLimb = false)
{
    FEWLookSlider S{Id, Group, Label, MoveTemp(Bones), Low, High, bWholeLimb};
    return S;
}

FEWLookSlider Kept(const TCHAR* Id, EEWLookGroup Group, const TCHAR* Label)
{
    return FEWLookSlider{Id, Group, Label, {}};
}

/** Thickness: the bone's two cross axes (the mannequin's bones run along X). */
FVector Thick(float S) { return FVector(1.f, S, S); }
FVector Long(float S) { return FVector(S, 1.f, 1.f); }

/** A preset: a starting body, colouring and hair; its face is varied from its own seed. All tuning. */
struct FPreset
{
    const TCHAR* Name;
    float Height, Build, Shoulders, Belly, SkinTone, Undertone, Weathering;
    uint8 HairMan, HairWoman, HairColour, FacialHair, EyeColour;
};
const FPreset Presets[] = {
    {TEXT("Deckhand"),      .50f, .45f, .55f, .40f, .30f, .60f, .55f, 2, 6, 2, 1, 0},
    {TEXT("Navigator"),     .60f, .40f, .45f, .45f, .15f, .40f, .30f, 3, 5, 7, 5, 4},
    {TEXT("Quartermaster"), .45f, .70f, .60f, .70f, .45f, .55f, .45f, 1, 9, 1, 6, 1},
    {TEXT("Gunner"),        .55f, .75f, .75f, .50f, .65f, .50f, .65f, 0, 1, 0, 2, 0},
    {TEXT("Shipwright"),    .65f, .60f, .70f, .55f, .55f, .65f, .70f, 4, 4, 3, 7, 2},
    {TEXT("Islander"),      .50f, .50f, .50f, .40f, .85f, .55f, .50f, 8, 10, 0, 4, 1},
};
}

const TArray<FEWLookSlider>& FEWAppearance::Sliders()
{
    using G = EEWLookGroup;
    static const TArray<FEWLookSlider> List = {
        Kept(TEXT("Height"), G::Body, TEXT("Height")),
        Kept(TEXT("Build"), G::Body, TEXT("Build (slight to broad)")),
        Shape(TEXT("Shoulders"), G::Body, TEXT("Shoulder width"), Both({TEXT("clavicle")}), Long(.8f), Long(1.2f)),
        Shape(TEXT("Chest"), G::Body, TEXT("Chest"), {TEXT("spine_04"), TEXT("spine_05")}, Thick(.86f), Thick(1.16f)),
        Shape(TEXT("Belly"), G::Body, TEXT("Belly"), {TEXT("spine_01"), TEXT("spine_02")}, Thick(.86f), Thick(1.25f)),
        Shape(TEXT("Hips"), G::Body, TEXT("Hips"), {TEXT("pelvis")}, Thick(.88f), Thick(1.16f)),
        Shape(TEXT("NeckLength"), G::Body, TEXT("Neck length"), {TEXT("neck_01"), TEXT("neck_02")}, Long(.8f), Long(1.25f)),
        Shape(TEXT("NeckThickness"), G::Body, TEXT("Neck thickness"), {TEXT("neck_01"), TEXT("neck_02")}, Thick(.85f), Thick(1.2f)),
        Shape(TEXT("HeadSize"), G::Body, TEXT("Head size"), {TEXT("head")}, FVector(.9f), FVector(1.1f), true),
        Shape(TEXT("ArmLength"), G::Body, TEXT("Arm length"), Both({TEXT("upperarm"), TEXT("upperarm_twist_01"), TEXT("upperarm_twist_02"),
            TEXT("lowerarm"), TEXT("lowerarm_twist_01"), TEXT("lowerarm_twist_02")}), Long(.92f), Long(1.08f)),
        Shape(TEXT("UpperArms"), G::Body, TEXT("Upper arms"), Both({TEXT("upperarm"), TEXT("upperarm_twist_01"), TEXT("upperarm_twist_02")}), Thick(.82f), Thick(1.25f)),
        Shape(TEXT("Forearms"), G::Body, TEXT("Forearms"), Both({TEXT("lowerarm"), TEXT("lowerarm_twist_01"), TEXT("lowerarm_twist_02")}), Thick(.85f), Thick(1.2f)),
        Shape(TEXT("Hands"), G::Body, TEXT("Hands"), Both({TEXT("hand")}), FVector(.88f), FVector(1.12f), true),
        Shape(TEXT("LegLength"), G::Body, TEXT("Leg length"), Both({TEXT("thigh"), TEXT("thigh_twist_01"), TEXT("thigh_twist_02"),
            TEXT("calf"), TEXT("calf_twist_01"), TEXT("calf_twist_02")}), Long(.92f), Long(1.08f)),
        Shape(TEXT("Thighs"), G::Body, TEXT("Thighs"), Both({TEXT("thigh"), TEXT("thigh_twist_01"), TEXT("thigh_twist_02")}), Thick(.85f), Thick(1.2f)),
        Shape(TEXT("Calves"), G::Body, TEXT("Calves"), Both({TEXT("calf"), TEXT("calf_twist_01"), TEXT("calf_twist_02")}), Thick(.85f), Thick(1.2f)),
        Shape(TEXT("Feet"), G::Body, TEXT("Feet"), Both({TEXT("foot")}), FVector(.9f), FVector(1.1f), true),

        Kept(TEXT("HeadWidth"), G::Head, TEXT("Head width")),
        Kept(TEXT("HeadLength"), G::Head, TEXT("Head length")),
        Kept(TEXT("Crown"), G::Head, TEXT("Crown height")),
        Kept(TEXT("ForeheadHeight"), G::Head, TEXT("Forehead height")),
        Kept(TEXT("ForeheadSlope"), G::Head, TEXT("Forehead slope")),
        Kept(TEXT("Temples"), G::Head, TEXT("Temples")),

        Kept(TEXT("BrowHeight"), G::Brows, TEXT("Brow height")),
        Kept(TEXT("BrowDepth"), G::Brows, TEXT("Brow ridge")),
        Kept(TEXT("BrowAngle"), G::Brows, TEXT("Brow angle")),
        Kept(TEXT("BrowThickness"), G::Brows, TEXT("Brow thickness")),

        Kept(TEXT("EyeSize"), G::Eyes, TEXT("Eye size")),
        Kept(TEXT("EyeSpacing"), G::Eyes, TEXT("Eye spacing")),
        Kept(TEXT("EyeHeight"), G::Eyes, TEXT("Eye height")),
        Kept(TEXT("EyeDepth"), G::Eyes, TEXT("Eye depth")),
        Kept(TEXT("EyeTilt"), G::Eyes, TEXT("Eye tilt")),
        Kept(TEXT("Eyelids"), G::Eyes, TEXT("Eyelids")),

        Kept(TEXT("NoseLength"), G::Nose, TEXT("Nose length")),
        Kept(TEXT("NoseWidth"), G::Nose, TEXT("Nose width")),
        Kept(TEXT("BridgeHeight"), G::Nose, TEXT("Bridge height")),
        Kept(TEXT("BridgeWidth"), G::Nose, TEXT("Bridge width")),
        Kept(TEXT("NoseCurve"), G::Nose, TEXT("Bridge curve")),
        Kept(TEXT("TipHeight"), G::Nose, TEXT("Tip height")),
        Kept(TEXT("TipSize"), G::Nose, TEXT("Tip size")),
        Kept(TEXT("Nostrils"), G::Nose, TEXT("Nostril flare")),

        Kept(TEXT("CheekboneHeight"), G::Cheeks, TEXT("Cheekbone height")),
        Kept(TEXT("CheekboneWidth"), G::Cheeks, TEXT("Cheekbone width")),
        Kept(TEXT("CheekFullness"), G::Cheeks, TEXT("Cheek fullness")),
        Kept(TEXT("CheekHollow"), G::Cheeks, TEXT("Cheek hollows")),

        Kept(TEXT("MouthWidth"), G::Mouth, TEXT("Mouth width")),
        Kept(TEXT("MouthHeight"), G::Mouth, TEXT("Mouth height")),
        Kept(TEXT("UpperLip"), G::Mouth, TEXT("Upper lip")),
        Kept(TEXT("LowerLip"), G::Mouth, TEXT("Lower lip")),
        Kept(TEXT("LipCorners"), G::Mouth, TEXT("Lip corners")),
        Kept(TEXT("MouthDepth"), G::Mouth, TEXT("Mouth depth")),

        Kept(TEXT("JawWidth"), G::Jaw, TEXT("Jaw width")),
        Kept(TEXT("JawAngle"), G::Jaw, TEXT("Jaw angle")),
        Kept(TEXT("JawLength"), G::Jaw, TEXT("Jaw length")),
        Kept(TEXT("ChinLength"), G::Jaw, TEXT("Chin length")),
        Kept(TEXT("ChinWidth"), G::Jaw, TEXT("Chin width")),
        Kept(TEXT("ChinDepth"), G::Jaw, TEXT("Chin depth")),
        Kept(TEXT("ChinCleft"), G::Jaw, TEXT("Chin cleft")),

        Kept(TEXT("EarSize"), G::Ears, TEXT("Ear size")),
        Kept(TEXT("EarAngle"), G::Ears, TEXT("Ear angle")),
        Kept(TEXT("EarHeight"), G::Ears, TEXT("Ear height")),
        Kept(TEXT("EarLobes"), G::Ears, TEXT("Ear lobes")),

        Kept(TEXT("SkinTone"), G::Skin, TEXT("Skin tone (fair to deep)")),
        Kept(TEXT("Undertone"), G::Skin, TEXT("Undertone (cool to warm)")),
        Kept(TEXT("Weathering"), G::Skin, TEXT("Sun and salt weathering")),
        Kept(TEXT("Freckles"), G::Skin, TEXT("Freckles")),
        Kept(TEXT("BodyHair"), G::Skin, TEXT("Body hair")),

        Kept(TEXT("MakeupStrength"), G::Makeup, TEXT("Makeup strength")),
    };
    return List;
}

const TArray<FEWLookChoice>& FEWAppearance::Choices()
{
    static const TArray<FEWLookChoice> List = {
        {TEXT("HairStyle"), TEXT("Hair style"), {TEXT("Shaved"), TEXT("Cropped"), TEXT("Short and tousled"), TEXT("Tied queue"), TEXT("Long queue"),
            TEXT("Braided queue"), TEXT("Loose to the shoulder"), TEXT("Long and loose"), TEXT("Curls"), TEXT("Bun"), TEXT("Two braids"),
            TEXT("Headscarf"), TEXT("Bald")}},
        {TEXT("HairColour"), TEXT("Hair colour"), {TEXT("Black"), TEXT("Dark brown"), TEXT("Chestnut"), TEXT("Auburn"), TEXT("Copper red"),
            TEXT("Dark blond"), TEXT("Golden blond"), TEXT("Ash"), TEXT("Grey"), TEXT("White")}},
        {TEXT("FacialHair"), TEXT("Facial hair"), {TEXT("None"), TEXT("Stubble"), TEXT("Moustache"), TEXT("Mutton chops"), TEXT("Goatee"),
            TEXT("Short beard"), TEXT("Full beard"), TEXT("Long beard"), TEXT("Braided beard")}},
        {TEXT("BrowStyle"), TEXT("Brow style"), {TEXT("Natural"), TEXT("Thin"), TEXT("Thick"), TEXT("Straight"), TEXT("Arched"), TEXT("Split by a scar")}},
        {TEXT("EyeColour"), TEXT("Eye colour"), {TEXT("Brown"), TEXT("Dark brown"), TEXT("Hazel"), TEXT("Green"), TEXT("Blue"), TEXT("Grey"), TEXT("Amber")}},
        {TEXT("Makeup"), TEXT("Makeup"), {TEXT("None"), TEXT("Kohl-lined eyes"), TEXT("Rouged cheeks"), TEXT("Tinted lips"), TEXT("Kohl and rouge"),
            TEXT("Sun-bronzed"), TEXT("Painted stripe")}},
        {TEXT("MakeupColour"), TEXT("Makeup colour"), {TEXT("Soot black"), TEXT("Crimson"), TEXT("Rose"), TEXT("Ochre"), TEXT("Indigo")}},
        {TEXT("Scars"), TEXT("Scars"), {TEXT("None"), TEXT("Brow cut"), TEXT("Cheek slash"), TEXT("Lip scar"), TEXT("Jaw scar"), TEXT("Pox marks"), TEXT("Old burn")}},
    };
    return List;
}

const TArray<const TCHAR*>& FEWAppearance::TattooDesigns()
{
    static const TArray<const TCHAR*> List = {TEXT("None"), TEXT("Anchor"), TEXT("Swallow"), TEXT("Compass rose"), TEXT("Nautical star"),
        TEXT("Ship under sail"), TEXT("Rope band"), TEXT("Sea serpent"), TEXT("Mermaid"), TEXT("Heart and banner"), TEXT("Crossed cannons"),
        TEXT("Turtle"), TEXT("Whale"), TEXT("Wave band")};
    return List;
}

const TArray<const TCHAR*>& FEWAppearance::TattooPlaces()
{
    static const TArray<const TCHAR*> List = {TEXT("Left forearm"), TEXT("Right forearm"), TEXT("Left upper arm"), TEXT("Right upper arm"),
        TEXT("Chest"), TEXT("Back"), TEXT("Neck"), TEXT("Left hand"), TEXT("Right hand"), TEXT("Left calf"), TEXT("Right calf")};
    return List;
}

const TArray<const TCHAR*>& FEWAppearance::TattooInks()
{
    static const TArray<const TCHAR*> List = {TEXT("Black"), TEXT("Blue-black"), TEXT("Faded green"), TEXT("Red and black")};
    return List;
}

const TArray<const TCHAR*>& FEWAppearance::PresetNames()
{
    static const TArray<const TCHAR*> List = [] { TArray<const TCHAR*> Names; for (const FPreset& P : Presets) Names.Add(P.Name); return Names; }();
    return List;
}

int32 FEWAppearance::SliderIndex(const TCHAR* Id)
{
    return Sliders().IndexOfByPredicate([Id](const FEWLookSlider& S) { return FCString::Strcmp(S.Id, Id) == 0; });
}

int32 FEWAppearance::ChoiceIndex(const TCHAR* Id)
{
    return Choices().IndexOfByPredicate([Id](const FEWLookChoice& C) { return FCString::Strcmp(C.Id, Id) == 0; });
}

float FEWAppearance::GetSlider(int32 Index) const
{
    if (Index == 0) return (Height - MinHeight) / (MaxHeight - MinHeight);
    return Features.IsValidIndex(Index - 1) ? Features[Index - 1] / 255.f : 128.f / 255.f;
}

void FEWAppearance::SetSlider(int32 Index, float Value)
{
    Value = FMath::IsFinite(Value) ? FMath::Clamp(Value, 0.f, 1.f) : .5f;
    if (Index == 0) { Height = FMath::Lerp(MinHeight, MaxHeight, Value); return; }
    if (Index < 1 || Index >= Sliders().Num()) return;
    if (Features.Num() < Sliders().Num() - 1) Features.Init(128, Sliders().Num() - 1);
    Features[Index - 1] = static_cast<uint8>(FMath::RoundToInt(Value * 255.f));
}

void FEWAppearance::SetPick(int32 Index, int32 Value)
{
    if (!Choices().IsValidIndex(Index)) return;
    if (Picks.Num() < Choices().Num()) Picks.SetNumZeroed(Choices().Num());
    const int32 Count = Choices()[Index].Options.Num();
    Picks[Index] = static_cast<uint8>(((Value % Count) + Count) % Count);
}

FLinearColor FEWAppearance::SkinColour(const UEWBodyRoster* Roster) const
{
    if (!Roster || Roster->Tones.Num() == 0) return FLinearColor(.6f, .45f, .35f);
    const float T = GetSlider(SliderIndex(TEXT("SkinTone"))) * (Roster->Tones.Num() - 1);
    const int32 A = FMath::FloorToInt(T), B = FMath::Min(A + 1, Roster->Tones.Num() - 1);
    FLinearColor Colour = FMath::Lerp(Roster->Tones[A], Roster->Tones[B], T - A);
    // Undertone: cooler toward pink-olive, warmer toward gold.
    const float U = GetSlider(SliderIndex(TEXT("Undertone"))) * 2.f - 1.f;
    Colour *= FLinearColor(1.f + .07f * U, 1.f, 1.f - .09f * U);
    Colour.A = 1.f;
    return Colour;
}

void FEWAppearance::ApplyPreset(int32 PresetIndex)
{
    const int32 Index = FMath::Clamp(PresetIndex, 0, UE_ARRAY_COUNT(Presets) - 1);
    const FPreset& P = Presets[Index];
    Preset = static_cast<uint8>(Index);
    Features.Init(128, Sliders().Num() - 1);
    Picks.Init(0, Choices().Num());
    Tattoos.Reset();
    const bool bMan = Body == 0;
    // The face varies a little from the preset's own seed, and between the two bodies.
    FRandomStream Stream(1700 + Index * 7 + Body);
    for (int32 S = 1; S < Sliders().Num(); ++S)
        if (Sliders()[S].Group != EEWLookGroup::Body && Sliders()[S].Group != EEWLookGroup::Skin && Sliders()[S].Group != EEWLookGroup::Makeup)
            SetSlider(S, .5f + (Stream.FRand() + Stream.FRand() - 1.f) * .22f);
    SetSlider(0, P.Height);
    SetSlider(SliderIndex(TEXT("Build")), P.Build);
    SetSlider(SliderIndex(TEXT("Shoulders")), bMan ? P.Shoulders : P.Shoulders * .8f);
    SetSlider(SliderIndex(TEXT("Hips")), bMan ? .45f : .62f);
    SetSlider(SliderIndex(TEXT("Belly")), P.Belly);
    SetSlider(SliderIndex(TEXT("SkinTone")), P.SkinTone);
    SetSlider(SliderIndex(TEXT("Undertone")), P.Undertone);
    SetSlider(SliderIndex(TEXT("Weathering")), P.Weathering);
    SetSlider(SliderIndex(TEXT("Freckles")), Stream.FRand() * .4f);
    SetSlider(SliderIndex(TEXT("BodyHair")), bMan ? .5f : .15f);
    SetSlider(SliderIndex(TEXT("MakeupStrength")), .5f);
    SetPick(ChoiceIndex(TEXT("HairStyle")), bMan ? P.HairMan : P.HairWoman);
    SetPick(ChoiceIndex(TEXT("HairColour")), P.HairColour);
    SetPick(ChoiceIndex(TEXT("FacialHair")), bMan ? P.FacialHair : 0);
    SetPick(ChoiceIndex(TEXT("EyeColour")), P.EyeColour);
    SetPick(ChoiceIndex(TEXT("Makeup")), bMan ? 0 : (Index % 3 == 1 ? 1 : 0));
    // A sailor's mark on some.
    if (Index == 0 || Index == 3) Tattoos.Add(FEWTattoo{static_cast<uint8>(Index == 0 ? 1 : 10), static_cast<uint8>(Index == 0 ? 0 : 2), 128, 128, 0});
    Tone = 0;
}

void FEWAppearance::Randomise(int32 Seed)
{
    FRandomStream Stream(Seed);
    ApplyPreset(Stream.RandHelper(UE_ARRAY_COUNT(Presets)));
    const bool bMan = Body == 0;
    for (int32 S = 0; S < Sliders().Num(); ++S)
    {
        const EEWLookGroup Group = Sliders()[S].Group;
        const float Spread = Group == EEWLookGroup::Skin ? .5f : Group == EEWLookGroup::Body ? .3f : .25f;
        SetSlider(S, Group == EEWLookGroup::Skin && S == SliderIndex(TEXT("SkinTone")) ? Stream.FRand()
            : .5f + (Stream.FRand() + Stream.FRand() - 1.f) * Spread * 2.f);
    }
    for (int32 C = 0; C < Choices().Num(); ++C) SetPick(C, Stream.RandHelper(Choices()[C].Options.Num()));
    if (!bMan && Stream.FRand() < .9f) SetPick(ChoiceIndex(TEXT("FacialHair")), 0);
    if (bMan && Stream.FRand() < .7f) SetPick(ChoiceIndex(TEXT("Makeup")), 0);
    if (Stream.FRand() < .7f) SetPick(ChoiceIndex(TEXT("Scars")), 0);
    Tattoos.Reset();
    for (int32 T = Stream.RandHelper(4); T > 0; --T)
        Tattoos.Add(FEWTattoo{static_cast<uint8>(1 + Stream.RandHelper(TattooDesigns().Num() - 1)), static_cast<uint8>(Stream.RandHelper(TattooPlaces().Num())),
            static_cast<uint8>(80 + Stream.RandHelper(140)), static_cast<uint8>(Stream.RandHelper(256)), static_cast<uint8>(Stream.RandHelper(TattooInks().Num()))});
}

FEWAppearance FEWAppearance::Clamped(const UEWBodyRoster* Roster) const
{
    FEWAppearance Out = *this;
    Out.Body = Roster && Roster->Bodies.Num() ? FMath::Min<int32>(Body, Roster->Bodies.Num() - 1) : 0;
    Out.Tone = Roster && Roster->Tones.Num() ? FMath::Min<int32>(Tone, Roster->Tones.Num() - 1) : 0;
    Out.Height = FMath::IsFinite(Height) ? FMath::Clamp(Height, MinHeight, MaxHeight) : 1.f;
    Out.Preset = FMath::Min<int32>(Preset, PresetNames().Num() - 1);
    const int32 FeatureCount = Sliders().Num() - 1;
    if (Out.Features.Num() == 0)
    {
        // A look saved before the sliders: as made, in the colouring it chose.
        Out.Features.Init(128, FeatureCount);
        if (Roster && Roster->Tones.Num() > 1) Out.SetSlider(SliderIndex(TEXT("SkinTone")), static_cast<float>(Out.Tone) / (Roster->Tones.Num() - 1));
    }
    else if (Out.Features.Num() != FeatureCount)
    {
        const int32 Had = Out.Features.Num();
        Out.Features.SetNum(FeatureCount);
        for (int32 I = Had; I < FeatureCount; ++I) Out.Features[I] = 128;
    }
    Out.Picks.SetNumZeroed(Choices().Num());
    for (int32 C = 0; C < Choices().Num(); ++C) Out.Picks[C] = FMath::Min<int32>(Out.Picks[C], Choices()[C].Options.Num() - 1);
    Out.Tattoos.RemoveAll([](const FEWTattoo& T) { return T.Design == 0 || T.Design >= TattooDesigns().Num(); });
    if (Out.Tattoos.Num() > MaxTattoos) Out.Tattoos.SetNum(MaxTattoos);
    for (FEWTattoo& T : Out.Tattoos)
    {
        T.Place = FMath::Min<int32>(T.Place, TattooPlaces().Num() - 1);
        T.Ink = FMath::Min<int32>(T.Ink, TattooInks().Num() - 1);
    }
    return Out;
}

bool FEWAppearance::ApplyTo(USkinnedMeshComponent* Mesh, const UEWBodyRoster* Roster) const
{
    if (!Mesh || !Roster || !Roster->Bodies.IsValidIndex(Body)) return false;
    const FEWBodyOption& Option = Roster->Bodies[Body];
    USkeletalMesh* BodyMesh = Option.Mesh.LoadSynchronous();
    if (!BodyMesh) return false;
    if (Mesh->GetSkinnedAsset() != BodyMesh)
    {
        Mesh->SetSkinnedAssetAndUpdate(BodyMesh, false);
        Mesh->EmptyOverrideMaterials();
    }
    if (UMaterialInterface* Dress = Option.ToneMaterial.LoadSynchronous())
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot) Mesh->SetMaterial(Slot, Dress);
    if (Option.ToneParameters.Num())
    {
        const FLinearColor Skin = SkinColour(Roster);
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
            if (UMaterialInstanceDynamic* Dynamic = Mesh->CreateDynamicMaterialInstance(Slot))
                for (const FName& Parameter : Option.ToneParameters)
                    Dynamic->SetVectorParameterValue(Parameter, Skin);
    }
    // The mesh stands on its own origin at the feet, so scaling it keeps the feet on the ground. Build widens it.
    const float Width = FMath::Lerp(.88f, 1.14f, GetSlider(SliderIndex(TEXT("Build"))));
    Mesh->SetRelativeScale3D(FVector(Height * Width, Height * Width, Height));
    return true;
}

void FEWAppearance::BoneScales(const USkinnedMeshComponent* Mesh, TArray<FVector>& OutScales) const
{
    OutScales.Reset();
    const USkinnedAsset* Asset = Mesh ? Mesh->GetSkinnedAsset() : nullptr;
    if (!Asset) return;
    const FReferenceSkeleton& Skeleton = Asset->GetRefSkeleton();
    const int32 Count = Skeleton.GetNum();
    TArray<FVector> Own, Limb;
    Own.Init(FVector::OneVector, Count);
    Limb.Init(FVector::OneVector, Count);
    for (int32 S = 1; S < Sliders().Num(); ++S)
    {
        const FEWLookSlider& Slider = Sliders()[S];
        if (Slider.Bones.Num() == 0) continue;
        const FVector Scale = FMath::Lerp(Slider.Low, Slider.High, GetSlider(S));
        for (const FName& Bone : Slider.Bones)
        {
            const int32 Index = Skeleton.FindBoneIndex(Bone);
            if (Index == INDEX_NONE) continue;
            (Slider.bWholeLimb ? Limb : Own)[Index] *= Scale;
        }
    }
    OutScales.SetNum(Count);
    TArray<FVector> Carried;
    Carried.Init(FVector::OneVector, Count);
    for (int32 Index = 0; Index < Count; ++Index)
    {
        const int32 Parent = Skeleton.GetParentIndex(Index);
        Carried[Index] = Limb[Index] * (Parent == INDEX_NONE ? FVector::OneVector : Carried[Parent]);
        OutScales[Index] = Own[Index] * Carried[Index];
    }
}
