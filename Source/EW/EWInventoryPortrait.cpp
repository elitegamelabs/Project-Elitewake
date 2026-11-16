// Copyright Elite Game Labs. All Rights Reserved.

#include "EWInventoryWidget.h"
#include "EWCharacter.h"
#include "Components/Image.h"
#include "Components/PointLightComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
    constexpr int32 PortraitWidth = 440, PortraitHeight = 880;
    // Keep the capture-only subject and lights away from gameplay and map captures.
    const FVector PortraitStage(-4000000, -4000000, 200000);

    UPointLightComponent* MakePortraitLight(AActor* Capture, float Lumens, FColor Colour)
    {
        auto* Light = NewObject<UPointLightComponent>(Capture);
        Capture->AddInstanceComponent(Light);
        Light->SetMobility(EComponentMobility::Movable);
        Light->ViewLightingChannels.bViewChannel0 = false;
        Light->ViewLightingChannels.bViewChannel4 = true;
        Light->SetLightColor(Colour);
        Light->SetIntensityUnits(ELightUnits::Lumens);
        Light->SetIntensity(Lumens);
        Light->SetAttenuationRadius(520.f);
        Light->SetCastShadows(false);
        Light->RegisterComponent();
        return Light;
    }
}

void UEWInventoryWidget::ClosePortrait()
{
    if (PortraitCapture) PortraitCapture->Destroy();
    if (PortraitSubject) PortraitSubject->Destroy();
    PortraitCapture = nullptr;
    PortraitSubject = nullptr;
    PortraitBody = nullptr;
    PortraitKey = nullptr;
    PortraitFill = nullptr;
    PortraitTarget = nullptr;
    PortraitParts.Reset();
    if (PortraitImage)
    {
        PortraitImage->SetBrush(FSlateBrush());
        PortraitImage->SetColorAndOpacity(FLinearColor::Transparent);
    }
}

void UEWInventoryWidget::UpdatePortrait(float DeltaTime)
{
    auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    auto* Source = Character ? Character->GetMesh() : nullptr;
    UWorld* World = GetWorld();
    if (!RightHost || RightHost->GetVisibility() != ESlateVisibility::Visible
        || !PortraitImage || !Source || !Source->GetSkeletalMeshAsset() || !World)
    {
        if (PortraitCapture) ClosePortrait();
        return;
    }

    if (!PortraitCapture)
    {
        auto* Material = LoadObject<UMaterialInterface>(nullptr,
            TEXT("/Game/Elitewake/UI/Inventory/M_InventoryPortrait.M_InventoryPortrait"));
        if (!Material) return;
        FActorSpawnParameters Params;
        Params.ObjectFlags |= RF_Transient;
        PortraitCapture = World->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), PortraitStage, FRotator::ZeroRotator, Params);
        PortraitSubject = World->SpawnActor<AActor>(AActor::StaticClass(), PortraitStage, FRotator::ZeroRotator, Params);
        if (!PortraitCapture || !PortraitSubject) { ClosePortrait(); return; }
        PortraitBody = NewObject<UPoseableMeshComponent>(PortraitSubject);
        PortraitSubject->SetRootComponent(PortraitBody);
        PortraitSubject->AddInstanceComponent(PortraitBody);
        PortraitBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        PortraitBody->SetVisibleInSceneCaptureOnly(true);
        PortraitBody->SetCastShadow(false);
        PortraitBody->RegisterComponent();

        PortraitTarget = NewObject<UTextureRenderTarget2D>(this);
        PortraitTarget->RenderTargetFormat = RTF_RGBA16f;
        PortraitTarget->ClearColor = FLinearColor(0, 0, 0, 1);
        PortraitTarget->InitAutoFormat(PortraitWidth, PortraitHeight);
        PortraitTarget->UpdateResourceImmediate(true);

        auto* Camera = PortraitCapture->GetCaptureComponent2D();
        Camera->TextureTarget = PortraitTarget;
        Camera->CaptureSource = SCS_SceneColorHDR;
        Camera->bCaptureEveryFrame = false;
        Camera->bCaptureOnMovement = false;
        Camera->bAlwaysPersistRenderingState = true;
        Camera->ProjectionType = ECameraProjectionMode::Orthographic;
        Camera->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
        Camera->ShowOnlyActors.Add(PortraitSubject);
        Camera->ViewLightingChannels.bViewChannel0 = false;
        Camera->ViewLightingChannels.bViewChannel4 = true;
        Camera->ShowFlags.SetAtmosphere(false);
        Camera->ShowFlags.SetFog(false);
        Camera->ShowFlags.SetBloom(false);
        Camera->ShowFlags.SetEyeAdaptation(false);
        Camera->ShowFlags.SetDynamicShadows(false);
        Camera->PostProcessSettings.bOverride_AutoExposureMethod = true;
        Camera->PostProcessSettings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
        Camera->PostProcessSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Camera->PostProcessSettings.AutoExposureApplyPhysicalCameraExposure = false;
        PortraitKey = MakePortraitLight(PortraitCapture, 195.f, FColor(255, 242, 224));
        PortraitFill = MakePortraitLight(PortraitCapture, 56.f, FColor(227, 237, 255));

        auto* Composite = UMaterialInstanceDynamic::Create(Material, this);
        Composite->SetTextureParameterValue(TEXT("Portrait"), PortraitTarget);
        PortraitImage->SetBrushFromMaterial(Composite);
        PortraitImage->SetColorAndOpacity(FLinearColor::White);
        PortraitClock = .10f;
    }

    PortraitClock += DeltaTime;
    if (PortraitClock < .10f) return;
    PortraitClock = 0.f;

    if (PortraitBody->GetSkinnedAsset() != Source->GetSkeletalMeshAsset())
        PortraitBody->SetSkinnedAssetAndUpdate(Source->GetSkeletalMeshAsset());
    for (int32 Index = 0; Index < Source->GetNumMaterials(); ++Index)
        if (PortraitBody->GetMaterial(Index) != Source->GetMaterial(Index))
            PortraitBody->SetMaterial(Index, Source->GetMaterial(Index));
    FTransform BodyTransform = Source->GetComponentTransform();
    BodyTransform.SetLocation(PortraitStage);
    PortraitBody->SetWorldTransform(BodyTransform);
    PortraitBody->CopyPoseFromSkeletalComponent(Source);
    // First person hides the head on the gameplay mesh. The portrait restores those bones on its own copy.
    const auto& RestPose = Source->GetSkeletalMeshAsset()->GetRefSkeleton().GetRefBonePose();
    for (int32 Index = 0; Index < PortraitBody->BoneSpaceTransforms.Num() && Index < RestPose.Num(); ++Index)
        if (Source->IsBoneHidden(Index)) PortraitBody->BoneSpaceTransforms[Index] = RestPose[Index];
    PortraitBody->RefreshBoneTransforms();
    PortraitBody->UpdateBounds();

    TArray<UStaticMeshComponent*> Worn;
    for (USceneComponent* Child : Source->GetAttachChildren())
        if (auto* Mesh = Cast<UStaticMeshComponent>(Child); Mesh && Mesh->GetStaticMesh()
            && (Mesh->IsVisible() || Mesh->GetAttachSocketName() == TEXT("head") || Mesh->GetAttachSocketName() == TEXT("neck_01")))
            Worn.Add(Mesh);
    while (PortraitParts.Num() > Worn.Num())
    {
        PortraitParts.Last()->DestroyComponent();
        PortraitParts.Pop();
    }

    FBox Bounds = PortraitBody->Bounds.GetBox();
    for (int32 Index = 0; Index < Worn.Num(); ++Index)
    {
        auto* Original = Worn[Index];
        if (!PortraitParts.IsValidIndex(Index))
        {
            auto* Part = NewObject<UStaticMeshComponent>(PortraitSubject);
            PortraitSubject->AddInstanceComponent(Part);
            Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Part->SetVisibleInSceneCaptureOnly(true);
            Part->SetCastShadow(false);
            Part->RegisterComponent();
            PortraitParts.Add(Part);
        }
        auto* Part = PortraitParts[Index].Get();
        if (Part->GetStaticMesh() != Original->GetStaticMesh()) Part->SetStaticMesh(Original->GetStaticMesh());
        for (int32 MaterialIndex = 0; MaterialIndex < Original->GetNumMaterials(); ++MaterialIndex)
            if (Part->GetMaterial(MaterialIndex) != Original->GetMaterial(MaterialIndex))
                Part->SetMaterial(MaterialIndex, Original->GetMaterial(MaterialIndex));
        if (Part->GetAttachParent() != PortraitBody || Part->GetAttachSocketName() != Original->GetAttachSocketName())
            Part->AttachToComponent(PortraitBody, FAttachmentTransformRules::KeepRelativeTransform, Original->GetAttachSocketName());
        Part->SetRelativeTransform(Original->GetRelativeTransform());
        Part->UpdateBounds();
        Bounds += Part->Bounds.GetBox();
    }

    const FVector Centre = Bounds.GetCenter();
    const FVector Forward = Character->GetActorForwardVector().GetSafeNormal2D().RotateAngleAxis(24.f, FVector::UpVector);
    const FVector Side = FVector::CrossProduct(FVector::UpVector, Forward);
    const FVector Extent = Bounds.GetExtent();
    const double HalfWidth = FMath::Abs(Side.X) * Extent.X + FMath::Abs(Side.Y) * Extent.Y;
    PortraitCapture->GetCaptureComponent2D()->OrthoWidth =
        2.10 * FMath::Max(HalfWidth, Extent.Z * (double(PortraitWidth) / PortraitHeight));
    PortraitCapture->SetActorLocationAndRotation(Centre + Forward * 300, (-Forward).Rotation());
    PortraitKey->SetWorldLocation(Centre + Forward * 145 + Side * 115 + FVector(0, 0, 125));
    PortraitFill->SetWorldLocation(Centre + Forward * 145 - Side * 110 + FVector(0, 0, 20));
    PortraitCapture->GetCaptureComponent2D()->CaptureScene();
}

FLinearColor UEWInventoryWidget::ProbePortraitPixel(FVector2D Uv) const
{
    if (!PortraitTarget) return FLinearColor::Transparent;
    const int32 X = FMath::Clamp(int32(Uv.X * PortraitTarget->SizeX), 0, PortraitTarget->SizeX - 1);
    const int32 Y = FMath::Clamp(int32(Uv.Y * PortraitTarget->SizeY), 0, PortraitTarget->SizeY - 1);
    FLinearColor Pixel = UKismetRenderingLibrary::ReadRenderTargetRawPixel(
        const_cast<UEWInventoryWidget*>(this), PortraitTarget, X, Y, false);
    Pixel.A = 1.f - Pixel.A; // The scene capture stores inverse opacity.
    return Pixel;
}
