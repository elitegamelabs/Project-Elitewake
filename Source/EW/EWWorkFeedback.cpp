#include "EWWorkFeedback.h"
#include "EWItemDefinition.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
    constexpr float BurstLife = 1.4f;     // seconds a chip lives (tuning)
    constexpr float MarkerLife = .42f;
    constexpr float PopupLife = 1.7f;
    const FLinearColor Gave(1.f, 1.f, 1.f);
    const FLinearColor Refused(1.f, .62f, .18f);
}

AEWImpactBurst::AEWImpactBurst()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = false;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Shape(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    CubeMesh = Cube.Object;
    ShapeMaterial = Shape.Object;
}

AEWImpactBurst* AEWImpactBurst::Spawn(UWorld* World, const FVector& Point, const FVector& Normal, EEWWorkSurface Surface)
{
    if (!World || World->GetNetMode() == NM_DedicatedServer) return nullptr;
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Burst = World->SpawnActor<AEWImpactBurst>(Point, FRotator::ZeroRotator, Params);
    if (Burst) Burst->Fill(Normal.GetSafeNormal(), Surface);
    return Burst;
}

void AEWImpactBurst::Fill(const FVector& Normal, EEWWorkSurface Surface)
{
    if (!CubeMesh || !ShapeMaterial) return;
    const bool bWood = Surface == EEWWorkSurface::Wood;
    const int32 Count = bWood ? 11 : 14;
    for (int32 i = 0; i < Count; ++i)
    {
        auto* Part = NewObject<UStaticMeshComponent>(this);
        Part->SetStaticMesh(CubeMesh);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetCastShadow(false);
        Part->SetupAttachment(GetRootComponent());
        Part->RegisterComponent();
        auto* Paint = UMaterialInstanceDynamic::Create(ShapeMaterial, Part);
        FLinearColor Colour;
        FVector Scale;
        if (bWood)
        {
            // Pale fresh wood mostly, a few dark flakes of bark; long thin splinters.
            const bool bBark = FMath::FRand() < .3f;
            Colour = bBark ? FLinearColor(.07f, .05f, .03f) : FLinearColor(.62f, .45f, .24f) * FMath::FRandRange(.8f, 1.1f);
            Scale = FVector(FMath::FRandRange(.05f, .11f), FMath::FRandRange(.012f, .025f), FMath::FRandRange(.008f, .015f));
        }
        else
        {
            const float Grey = FMath::FRandRange(.18f, .42f);
            Colour = FLinearColor(Grey, Grey * .97f, Grey * .92f);
            const float Size = FMath::FRandRange(.015f, .045f);
            Scale = FVector(Size, Size * FMath::FRandRange(.6f, 1.f), Size * FMath::FRandRange(.4f, .8f));
        }
        Paint->SetVectorParameterValue(TEXT("Color"), Colour);
        Part->SetMaterial(0, Paint);
        Part->SetRelativeScale3D(Scale);
        Part->SetRelativeRotation(FRotator(FMath::FRandRange(-180.f, 180.f), FMath::FRandRange(-180.f, 180.f), FMath::FRandRange(-180.f, 180.f)));
        // Out from the face in a wide cone, with some lift.
        const FVector Out = FMath::VRandCone(Normal, FMath::DegreesToRadians(55.f));
        FChip Chip;
        Chip.Part = Part;
        Chip.Velocity = Out * FMath::FRandRange(180.f, bWood ? 420.f : 480.f) + FVector(0, 0, FMath::FRandRange(80.f, 220.f));
        Chip.Spin = FRotator(FMath::FRandRange(-720.f, 720.f), FMath::FRandRange(-720.f, 720.f), FMath::FRandRange(-720.f, 720.f));
        Chip.Scale = Scale;
        Chips.Add(Chip);
    }
}

void AEWImpactBurst::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    Age += DeltaSeconds;
    if (Age >= BurstLife) { Destroy(); return; }
    const float Shrink = FMath::Clamp((BurstLife - Age) / (BurstLife * .4f), 0.f, 1.f);
    for (FChip& Chip : Chips)
    {
        if (!Chip.Part) continue;
        Chip.Velocity += FVector(0, 0, -980.f) * DeltaSeconds;
        Chip.Velocity *= FMath::Pow(.35f, DeltaSeconds);   // air drag
        Chip.Part->AddRelativeLocation(Chip.Velocity * DeltaSeconds);
        Chip.Part->AddRelativeRotation(Chip.Spin * DeltaSeconds);
        Chip.Part->SetRelativeScale3D(Chip.Scale * Shrink);
    }
}

// ---- Hit marker -----------------------------------------------------------------------------------------------

TSharedRef<SWidget> UEWHitMarkerWidget::RebuildWidget()
{
    SetVisibility(ESlateVisibility::HitTestInvisible);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Root = WidgetTree->ConstructWidget<UBorder>();
        Root->SetBrushColor(FLinearColor::Transparent);
        WidgetTree->RootWidget = Root;
    }
    return Super::RebuildWidget();
}

void UEWHitMarkerWidget::AddLine(const FString& Text, const FLinearColor& Colour, bool bBelow)
{
    // A newer line pushes the older ones on up.
    FPopup Popup;
    Popup.Text = Text;
    Popup.Colour = Colour;
    Popup.bBelow = bBelow;
    Popups.Add(Popup);
    if (Popups.Num() > 6) Popups.RemoveAt(0);
    LastLine = Text;
}

void UEWHitMarkerWidget::ShowHit(bool bGave, const TArray<FEWGatherGain>& Gains, EEWWorkRefusal Refusal)
{
    MarkerAge = 0.f;
    bMarkerGave = bGave;
    ++MarkerCount;
    ShowGains(Gains);
    switch (Refusal)
    {
    case EEWWorkRefusal::NeedsHatchet: AddLine(TEXT("Needs a hatchet"), Refused, true); break;
    case EEWWorkRefusal::NeedsPickaxe: AddLine(TEXT("Needs a pickaxe"), Refused, true); break;
    case EEWWorkRefusal::PackFull: AddLine(TEXT("Your pack is full"), Refused, true); break;
    default: break;
    }
}

void UEWHitMarkerWidget::ShowGains(const TArray<FEWGatherGain>& Gains)
{
    for (const FEWGatherGain& Gain : Gains)
        if (Gain.Item && Gain.Count > 0)
            AddLine(FString::Printf(TEXT("+%d %s"), Gain.Count, *Gain.Item->DisplayName.ToString()), Gave, false);
}

void UEWHitMarkerWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    if (MarkerAge >= 0.f) { MarkerAge += Delta; if (MarkerAge > MarkerLife) MarkerAge = -1.f; }
    for (FPopup& Popup : Popups) Popup.Age += Delta;
    Popups.RemoveAll([](const FPopup& P) { return P.Age > PopupLife; });
}

int32 UEWHitMarkerWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    const FVector2f Centre = FVector2f(AllottedGeometry.GetLocalSize()) * .5f;
    if (MarkerAge >= 0.f)
    {
        // Four ticks pointing in at the centre, popping out a little then settling as they fade.
        const float T = MarkerAge / MarkerLife;
        const float Pop = 1.f + .45f * FMath::Exp(-T * 9.f);
        const FLinearColor Colour = (bMarkerGave ? Gave : Refused).CopyWithNewOpacity(1.f - T * T);
        for (const FVector2f Dir : {FVector2f(1, 1), FVector2f(-1, 1), FVector2f(1, -1), FVector2f(-1, -1)})
        {
            const FVector2f D = Dir.GetSafeNormal();
            TArray<FVector2f> Points = {Centre + D * 9.f * Pop, Centre + D * 21.f * Pop};
            FSlateDrawElement::MakeLines(OutDrawElements, Layer + 1, AllottedGeometry.ToPaintGeometry(), Points,
                ESlateDrawEffect::None, Colour, true, 2.5f);
        }
    }
    if (Popups.Num())
    {
        const TSharedRef<FSlateFontMeasure> Measure = FSlateApplication::Get().GetRenderer()->GetFontMeasureService();
        const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", 16);
        int32 Above = 0, Below = 0;
        for (int32 i = Popups.Num() - 1; i >= 0; --i)
        {
            const FPopup& P = Popups[i];
            const float T = P.Age / PopupLife;
            const float Alpha = FMath::Clamp((1.f - T) * 2.5f, 0.f, 1.f);
            const FVector2D Size = Measure->Measure(P.Text, Font);
            FVector2f At = P.bBelow ? Centre + FVector2f(-Size.X * .5f, 38.f + 22.f * Below++)
                                    : Centre + FVector2f(34.f, -30.f - 24.f * Above++ - P.Age * 26.f);
            // A soft shadow keeps the text readable over sand and sky.
            FSlateDrawElement::MakeText(OutDrawElements, Layer + 2, AllottedGeometry.ToPaintGeometry(FVector2f(Size), FSlateLayoutTransform(At + FVector2f(1.5f, 1.5f))),
                P.Text, Font, ESlateDrawEffect::None, FLinearColor(0, 0, 0, .6f * Alpha));
            FSlateDrawElement::MakeText(OutDrawElements, Layer + 3, AllottedGeometry.ToPaintGeometry(FVector2f(Size), FSlateLayoutTransform(At)),
                P.Text, Font, ESlateDrawEffect::None, P.Colour.CopyWithNewOpacity(Alpha));
        }
    }
    return Layer + 3;
}
