#include "Characters/EWAppearance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInstanceDynamic.h"

FEWAppearance FEWAppearance::Clamped(const UEWBodyRoster* Roster) const
{
    FEWAppearance Out = *this;
    Out.Body = Roster && Roster->Bodies.Num() ? FMath::Min<int32>(Body, Roster->Bodies.Num() - 1) : 0;
    Out.Tone = Roster && Roster->Tones.Num() ? FMath::Min<int32>(Tone, Roster->Tones.Num() - 1) : 0;
    Out.Height = FMath::IsFinite(Height) ? FMath::Clamp(Height, MinHeight, MaxHeight) : 1.f;
    return Out;
}

bool FEWAppearance::ApplyTo(USkeletalMeshComponent* Mesh, const UEWBodyRoster* Roster) const
{
    if (!Mesh || !Roster || !Roster->Bodies.IsValidIndex(Body)) return false;
    const FEWBodyOption& Option = Roster->Bodies[Body];
    USkeletalMesh* BodyMesh = Option.Mesh.LoadSynchronous();
    if (!BodyMesh) return false;
    if (Mesh->GetSkeletalMeshAsset() != BodyMesh)
    {
        Mesh->SetSkeletalMesh(BodyMesh, false);
        Mesh->EmptyOverrideMaterials();
    }
    if (UMaterialInterface* Dress = Option.ToneMaterial.LoadSynchronous())
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot) Mesh->SetMaterial(Slot, Dress);
    if (Roster->Tones.IsValidIndex(Tone) && Option.ToneParameters.Num())
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
            if (UMaterialInstanceDynamic* Dynamic = Mesh->CreateDynamicMaterialInstance(Slot))
                for (const FName& Parameter : Option.ToneParameters)
                    Dynamic->SetVectorParameterValue(Parameter, Roster->Tones[Tone]);
    // The mesh stands on its own origin at the feet, so scaling it keeps the feet on the ground.
    Mesh->SetRelativeScale3D(FVector(Height));
    return true;
}
