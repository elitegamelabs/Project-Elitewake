#include "EWCobweb.h"
#include "EWCharacter.h"
#include "EWSound.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

namespace
{
    const TCHAR* const WebMesh = TEXT("/Game/Elitewake/World/Caves/Webs/SM_Cobweb_v1.SM_Cobweb_v1");
    const TCHAR* const ShredMesh = TEXT("/Game/Elitewake/World/Caves/Webs/SM_CobwebShred_v1.SM_CobwebShred_v1");
    const TCHAR* const WebSet = TEXT("/Game/Elitewake/World/Caves/Webs/DA_CaveWebs.DA_CaveWebs");
}

AEWCobweb::AEWCobweb()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    bReplicates = false;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    RootComponent = Root;
    Web = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Web"));
    Web->SetupAttachment(Root);
    Web->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Web->SetCastShadow(false);
    // The mesh is 2 m across at scale 1 (build_cave_webs.py), facing +X; the touch box covers it, a hand's depth thick.
    Touch = CreateDefaultSubobject<UBoxComponent>(TEXT("Touch"));
    Touch->SetupAttachment(Root);
    Touch->SetBoxExtent(FVector(20.f, 92.f, 92.f));
    Touch->SetCollisionProfileName(TEXT("Trigger"));
    Touch->SetGenerateOverlapEvents(true);
    Touch->OnComponentBeginOverlap.AddDynamic(this, &AEWCobweb::OnTouched);
}

void AEWCobweb::SetWebMesh(UStaticMesh* Mesh)
{
    Web->SetStaticMesh(Mesh);
}

void AEWCobweb::OnTouched(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
    if (Cast<AEWCharacter>(Other)) Tear();
}

void AEWCobweb::Tear()
{
    if (bTorn) return;
    bTorn = true;
    TornSeconds = 0.f;
    Web->SetVisibility(false);
    // Strands drop from where the web hung, drifting and turning as they fall, and fade to nothing.
    UStaticMesh* Strand = LoadObject<UStaticMesh>(nullptr, ShredMesh, nullptr, LOAD_Quiet | LOAD_NoWarn);
    const FVector Size = GetActorScale3D();
    for (int32 i = 0; i < ShredCount && Strand; ++i)
    {
        auto* Shred = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transient);
        Shred->SetStaticMesh(Strand);
        Shred->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Shred->SetCastShadow(false);
        Shred->SetupAttachment(Root);
        Shred->RegisterComponent();
        Shred->SetUsingAbsoluteScale(true);
        Shred->SetWorldScale3D(FVector(FMath::FRandRange(.8f, 1.3f) * FMath::Max(Size.Y, 1.f) * .6f));
        Shred->SetRelativeLocation(FVector(0, FMath::FRandRange(-80.f, 80.f), FMath::FRandRange(-50.f, 85.f)));
        Shred->SetRelativeRotation(FRotator(0, 0, FMath::FRandRange(-25.f, 25.f)));
        Shreds.Add(Shred);
        ShredDrift.Add(FVector(FMath::FRandRange(-25.f, 25.f), FMath::FRandRange(-25.f, 25.f), -FMath::FRandRange(45.f, 95.f)));
        ShredSpin.Add(FRotator(FMath::FRandRange(-30.f, 30.f), FMath::FRandRange(-60.f, 60.f), FMath::FRandRange(-40.f, 40.f)));
    }
    // A faint tearing whisper.
    UEWSoundLibrary::PlaySoundAt(this, EEWSound::GatherRustle, GetActorLocation(), .3f, 1.7f);
    SetActorTickEnabled(true);
}

void AEWCobweb::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bTorn) return;
    TornSeconds += DeltaSeconds;
    if (!Shreds.IsEmpty())
    {
        const float Left = 1.f - TornSeconds / FallSeconds;
        for (int32 i = 0; i < Shreds.Num(); ++i)
        {
            UStaticMeshComponent* Shred = Shreds[i];
            if (!Shred) continue;
            Shred->AddWorldOffset(ShredDrift[i] * DeltaSeconds);
            Shred->AddWorldRotation(ShredSpin[i] * DeltaSeconds);
            Shred->SetWorldScale3D(Shred->GetComponentScale() * FMath::Clamp(Left / FMath::Max(Left + DeltaSeconds / FallSeconds, KINDA_SMALL_NUMBER), 0.f, 1.f));
        }
        if (Left <= 0.f)
        {
            for (UStaticMeshComponent* Shred : Shreds)
                if (Shred) Shred->DestroyComponent();
            Shreds.Empty();
            ShredDrift.Empty();
            ShredSpin.Empty();
        }
    }
    if (TornSeconds >= RegrowSeconds) Regrow();
}

void AEWCobweb::Regrow()
{
    bTorn = false;
    Web->SetVisibility(true);
    SetActorTickEnabled(false);
    // Spun again while someone stands in it, it waits for them to leave.
    TArray<AActor*> Inside;
    Touch->GetOverlappingActors(Inside, AEWCharacter::StaticClass());
    if (!Inside.IsEmpty()) Tear();
}

void UEWCaveWebSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
    Super::OnWorldBeginPlay(InWorld);
    if (InWorld.GetNetMode() == NM_DedicatedServer) return;   // only for show
    const UEWCaveWebSet* Set = LoadObject<UEWCaveWebSet>(nullptr, WebSet, nullptr, LOAD_Quiet | LOAD_NoWarn);
    if (!Set) return;
    const FString Here = UWorld::RemovePIEPrefix(InWorld.GetOutermost()->GetName());
    if (Here != Set->Map.ToSoftObjectPath().GetLongPackageName()) return;
    UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, WebMesh, nullptr, LOAD_Quiet | LOAD_NoWarn);
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    Spawn.ObjectFlags |= RF_Transient;
    for (const FTransform& Where : Set->Webs)
        if (AEWCobweb* Web = InWorld.SpawnActor<AEWCobweb>(AEWCobweb::StaticClass(), Where, Spawn))
            Web->SetWebMesh(Mesh);
}
