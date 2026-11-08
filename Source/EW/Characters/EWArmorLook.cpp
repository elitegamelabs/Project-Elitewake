#include "Characters/EWArmorLook.h"
#include "EWEquipmentComponent.h"
#include "EWItemDefinition.h"
#include "AnimationRuntime.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace EWArmorLook
{
namespace
{
enum class EShape : uint8 { Cylinder, Sphere, Cube };

/** One shape: along the segment From -> To (To none: Length cm along Along in component space), Width x Depth across it
 *  (cm, full size), Grow cm added to the segment's length, Shift moving it along the segment (0 centred, -0.5 to its start). */
struct FShape
{
    const TCHAR* From;
    const TCHAR* To;
    EShape Shape;
    float Width, Depth, Grow;
    FLinearColor Colour;
    float Shift = 0.f;
    FVector Along = FVector::UpVector;
    float Length = 0.f;
    FVector Offset = FVector::ZeroVector;   // component space, cm, after placing on the segment
};

// The category's colours (placeholders; production materials come with the real garments).
const FLinearColor Beige(.55f, .47f, .34f), BeigeDark(.42f, .35f, .25f);
const FLinearColor FurBrown(.24f, .17f, .11f), FurGrey(.36f, .32f, .28f), Leather(.16f, .1f, .06f);
const FLinearColor Steel(.22f, .23f, .25f), Navy(.05f, .07f, .16f), Brass(.55f, .42f, .16f), Boot(.07f, .05f, .04f), Sash(.32f, .05f, .06f);

/** The shapes for one worn piece. Bone names are the Unreal mannequin's, which both survivor bodies use; SIDE stands for
 *  l and r (Rebuild places a paired shape on both sides). */
void ShapesFor(EEWArmorKind Kind, EEWEquipmentSlot Slot, TArray<FShape>& Out)
{
    const float Bulk = Kind == EEWArmorKind::Fur ? 1.22f : Kind == EEWArmorKind::Metal ? 1.12f : 1.06f;
    const FLinearColor Main = Kind == EEWArmorKind::Fur ? FurBrown : Kind == EEWArmorKind::Metal ? Steel : Beige;
    {
        if (Slot == EEWEquipmentSlot::Chest)
        {
            // Sleeves (a navy coat under metal), forearms (steel guards, fur cuffs, cloth wraps) and gloves.
            const FLinearColor Sleeve = Kind == EEWArmorKind::Metal ? Navy : Kind == EEWArmorKind::Fur ? FurGrey : Beige;
            const FLinearColor Forearm = Kind == EEWArmorKind::Metal ? Steel : Kind == EEWArmorKind::Fur ? FurBrown : BeigeDark;
            const FLinearColor Glove = Kind == EEWArmorKind::Metal ? Steel : Kind == EEWArmorKind::Fur ? Leather : BeigeDark;
            Out.Add({TEXT("upperarm_SIDE"), TEXT("lowerarm_SIDE"), EShape::Cylinder, 13.f * Bulk, 13.f * Bulk, 4.f, Sleeve});
            Out.Add({TEXT("lowerarm_SIDE"), TEXT("hand_SIDE"), EShape::Cylinder, 11.f * Bulk, 11.f * Bulk, 2.f, Forearm});
            Out.Add({TEXT("hand_SIDE"), TEXT("middle_01_SIDE"), EShape::Sphere, 10.f * Bulk, 6.5f * Bulk, 9.f, Glove, .3f});
            // The shoulder: a pauldron on metal, a fur collar, a cloth layer.
            Out.Add({TEXT("clavicle_SIDE"), TEXT("upperarm_SIDE"), EShape::Sphere, 15.f * Bulk, 15.f * Bulk, 4.f, Kind == EEWArmorKind::Metal ? Steel : Main, .35f});
        }
        else if (Slot == EEWEquipmentSlot::Legs)
        {
            const FLinearColor Trouser = Kind == EEWArmorKind::Metal ? Navy : Main;
            const FLinearColor Shin = Kind == EEWArmorKind::Metal ? Boot : Kind == EEWArmorKind::Fur ? FurGrey : BeigeDark;
            const FLinearColor Shoe = Kind == EEWArmorKind::Metal ? Boot : Kind == EEWArmorKind::Fur ? FurBrown : BeigeDark;
            Out.Add({TEXT("thigh_SIDE"), TEXT("calf_SIDE"), EShape::Cylinder, 19.f * Bulk, 19.f * Bulk, 4.f, Trouser});
            Out.Add({TEXT("calf_SIDE"), TEXT("foot_SIDE"), EShape::Cylinder, 14.f * Bulk, 14.f * Bulk, 2.f, Shin});
            Out.Add({TEXT("foot_SIDE"), TEXT("ball_SIDE"), EShape::Cube, 11.f * Bulk, 9.f * Bulk, 12.f, Shoe, .15f});
            if (Kind == EEWArmorKind::Metal)   // a steel knee cop
                Out.Add({TEXT("calf_SIDE"), TEXT("foot_SIDE"), EShape::Sphere, 11.f, 11.f, -30.f, Steel, -.5f});
        }
    }
    if (Slot == EEWEquipmentSlot::Chest)
    {
        // The torso, pelvis to the base of the neck: a cuirass over a navy coat, a fur jacket, a cloth tunic.
        Out.Add({TEXT("spine_01"), TEXT("spine_04"), EShape::Cylinder, 38.f * Bulk, 26.f * Bulk, 10.f, Main});
        Out.Add({TEXT("spine_04"), TEXT("neck_01"), EShape::Cylinder, 40.f * Bulk, 25.f * Bulk, 6.f, Main});
        // The coat's skirts below the cuirass, the fur jacket's hem, the tunic's frayed hem.
        Out.Add({TEXT("pelvis"), TEXT("spine_01"), EShape::Cylinder, 40.f * Bulk, 30.f * Bulk, 16.f,
            Kind == EEWArmorKind::Metal ? Navy : Kind == EEWArmorKind::Fur ? FurGrey : BeigeDark, -.4f});
        if (Kind != EEWArmorKind::Fur)   // a sash at the waist (red on the coat, a cloth one on the tunic)
            Out.Add({TEXT("spine_01"), TEXT("spine_02"), EShape::Cylinder, 41.f * Bulk, 30.f * Bulk, -4.f, Kind == EEWArmorKind::Metal ? Sash : BeigeDark});
    }
    else if (Slot == EEWEquipmentSlot::Legs)
    {
        Out.Add({TEXT("pelvis"), TEXT("spine_01"), EShape::Cylinder, 38.f * Bulk, 28.f * Bulk, 10.f,
            Kind == EEWArmorKind::Metal ? Leather : Main, -.2f});   // the waist, with a leather belt on metal
    }
    else if (Slot == EEWEquipmentSlot::Head)
    {
        // The neck and the whole head, face included (a narrow eye slit is left to the production garment).
        Out.Add({TEXT("neck_01"), TEXT("head"), EShape::Cylinder, 15.f * Bulk, 15.f * Bulk, 6.f, Main});
        Out.Add({TEXT("head"), nullptr, EShape::Sphere, 22.f * Bulk, 25.f * Bulk, 0.f, Main, 0.f, FVector::UpVector, 28.f * Bulk, FVector(0, 1.5f, 0)});
        if (Kind == EEWArmorKind::Metal)
        {
            // The tricorn: a broad dark brim with brass edging above the enclosed steel helmet.
            Out.Add({TEXT("head"), nullptr, EShape::Cylinder, 46.f, 46.f, 0.f, Steel * .7f, 0.f, FVector::UpVector, 3.f, FVector(0, 0, 13)});
            Out.Add({TEXT("head"), nullptr, EShape::Cylinder, 48.f, 48.f, 0.f, Brass, 0.f, FVector::UpVector, 1.f, FVector(0, 0, 11.5f)});
            Out.Add({TEXT("head"), nullptr, EShape::Cylinder, 24.f, 24.f, 0.f, Steel, 0.f, FVector::UpVector, 9.f, FVector(0, 0, 18)});
        }
        else if (Kind == EEWArmorKind::Fur)
        {
            // The raccoon pelt's ears, and the fur falling to the shoulders.
            Out.Add({TEXT("head"), nullptr, EShape::Sphere, 7.f, 5.f, 0.f, FurGrey, 0.f, FVector::UpVector, 9.f, FVector(-8, 0, 16)});
            Out.Add({TEXT("head"), nullptr, EShape::Sphere, 7.f, 5.f, 0.f, FurGrey, 0.f, FVector::UpVector, 9.f, FVector(8, 0, 16)});
            Out.Add({TEXT("neck_01"), TEXT("head"), EShape::Cylinder, 30.f, 26.f, -2.f, FurGrey, -.4f});
        }
    }
}

UStaticMesh* MeshOf(EShape Shape)
{
    static const TCHAR* Paths[] = {TEXT("/Engine/BasicShapes/Cylinder.Cylinder"), TEXT("/Engine/BasicShapes/Sphere.Sphere"), TEXT("/Engine/BasicShapes/Cube.Cube")};
    return LoadObject<UStaticMesh>(nullptr, Paths[int32(Shape)]);
}

bool RefPose(const USkeletalMeshComponent* Body, const FName Bone, FTransform& Out)
{
    const USkeletalMesh* Mesh = Body ? Body->GetSkeletalMeshAsset() : nullptr;
    if (!Mesh) return false;
    const int32 Index = Mesh->GetRefSkeleton().FindBoneIndex(Bone);
    if (Index == INDEX_NONE) return false;
    Out = FAnimationRuntime::GetComponentSpaceTransformRefPose(Mesh->GetRefSkeleton(), Index);
    return true;
}
}

int32 ShapeCount(const UEWItemDefinition* Item)
{
    if (!Item || Item->ArmorKind == EEWArmorKind::None) return 0;
    TArray<FShape> Shapes;
    ShapesFor(Item->ArmorKind, Item->EquipmentSlot, Shapes);
    return Shapes.Num();
}

void Rebuild(USkeletalMeshComponent* Body, const TArray<FEWEquipmentEntry>& Worn, TArray<TObjectPtr<UStaticMeshComponent>>& InOutPieces)
{
    for (UStaticMeshComponent* Piece : InOutPieces) if (Piece) Piece->DestroyComponent();
    InOutPieces.Reset();
    if (!Body || !Body->GetOwner() || Body->GetNetMode() == NM_DedicatedServer) return;
    UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    for (const FEWEquipmentEntry& Entry : Worn)
    {
        const UEWItemDefinition* Item = Entry.ItemDefinition;
        if (!Item || Item->ArmorKind == EEWArmorKind::None) continue;
        TArray<FShape> Shapes;
        ShapesFor(Item->ArmorKind, Item->EquipmentSlot, Shapes);
        for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
            for (const FShape& Shape : Shapes)
            {
                // Paired shapes name their side with SIDE; unpaired ones are placed once (on the first pass).
                const FString From(Shape.From), To(Shape.To ? Shape.To : TEXT(""));
                const bool bPaired = From.Contains(TEXT("SIDE"));
                if (!bPaired && SideIndex == 1) continue;
                const TCHAR* Side = SideIndex == 0 ? TEXT("l") : TEXT("r");
                const FName FromBone(*From.Replace(TEXT("SIDE"), Side)), ToBone(*To.Replace(TEXT("SIDE"), Side));
                FTransform FromPose, ToPose;
                if (!RefPose(Body, FromBone, FromPose)) continue;
                // The segment in component space: to the next bone, or a set length along a set direction.
                FVector Start = FromPose.GetLocation(), Axis;
                float Length;
                if (!To.IsEmpty() && RefPose(Body, ToBone, ToPose))
                {
                    Axis = ToPose.GetLocation() - Start;
                    Length = Axis.Size();
                    Axis = Length > KINDA_SMALL_NUMBER ? Axis / Length : FVector::UpVector;
                }
                else if (!To.IsEmpty())
                {
                    // A hand without finger bones: the forearm's direction carried on.
                    FTransform Elbow;
                    const FName Forearm(*FString::Printf(TEXT("lowerarm_%s"), Side));
                    Axis = RefPose(Body, Forearm, Elbow) ? (Start - Elbow.GetLocation()).GetSafeNormal() : FVector::DownVector;
                    Length = 10.f;
                }
                else
                {
                    Axis = Shape.Along;
                    Length = Shape.Length;
                }
                const float Size = FMath::Max(1.f, Length + Shape.Grow);
                FVector Centre = Start + Axis * (Length * .5f + Length * Shape.Shift) + Shape.Offset;
                if (Shape.To == nullptr) Centre = Start + Shape.Offset + Axis * (Shape.Length * .5f - (Shape.Shape == EShape::Sphere ? 4.f : 0.f));
                // Cross axes: side to side is the body's X (the mannequin faces +Y), unless the segment runs along it.
                FVector Across = FVector::XAxisVector - Axis * FVector::DotProduct(FVector::XAxisVector, Axis);
                if (!Across.Normalize()) Across = FVector::YAxisVector;
                const FRotator Rotation = FRotationMatrix::MakeFromZX(Axis, Across).Rotator();
                // The basic shapes are 100 cm: scaled to Width (X), Depth (Y) and the segment's length (Z).
                const FVector Scale(Shape.Width / 100.f, Shape.Depth / 100.f, Size / 100.f);
                const FTransform InComponent(Rotation, Centre, Scale);
                // Fixed to the segment's first bone, so it moves with it.
                const FTransform OnBone = InComponent.GetRelativeTransform(FromPose);
                auto* Piece = NewObject<UStaticMeshComponent>(Body->GetOwner(), NAME_None, RF_Transient);
                Piece->SetStaticMesh(MeshOf(Shape.Shape));
                Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                Piece->SetCastShadow(true);
                Piece->SetupAttachment(Body, FromBone);
                Piece->SetRelativeTransform(OnBone);
                Piece->ComponentTags.Add(TEXT("ArmorPiece"));
                Piece->ComponentTags.Add(FName(*Item->ItemId.ToString()));
                if (Base)
                {
                    UMaterialInstanceDynamic* Look = UMaterialInstanceDynamic::Create(Base, Piece);
                    Look->SetVectorParameterValue(TEXT("Color"), Shape.Colour);
                    Piece->SetMaterial(0, Look);
                }
                Piece->RegisterComponent();
                InOutPieces.Add(Piece);
            }
    }
}
}
