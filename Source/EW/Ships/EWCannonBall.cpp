#include "Ships/EWCannonBall.h"
#include "Ships/EWShip.h"
#include "EWCharacter.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"
#include "Net/UnrealNetwork.h"
#include "WaterBodyActor.h"

TArray<TWeakObjectPtr<AEWCannonBall>> AEWCannonBall::RecentShots;

AEWCannonBall::AEWCannonBall()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    SetReplicatingMovement(true);
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    Collision->InitSphereRadius(Radius);
    // A physics body, which ships' hull boxes let through so it strikes the planking itself. It is stopped by
    // hulls, rock and ground; it flies past swimmers and crew for now.
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Collision->SetCollisionObjectType(ECC_PhysicsBody);
    Collision->SetCollisionResponseToAllChannels(ECR_Block);
    Collision->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
    Collision->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
    Collision->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
    RootComponent = Collision;
    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (Sphere.Succeeded()) Visual->SetStaticMesh(Sphere.Object);
    Visual->SetRelativeScale3D(FVector(Radius * 2.f / 100.f));
    Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
    Movement->UpdatedComponent = Collision;
    Movement->bAutoActivate = false;
    Movement->ProjectileGravityScale = 1.f;
    Movement->bShouldBounce = false;
    Movement->bRotationFollowsVelocity = true;
    InitialLifeSpan = 20.f;
}

void AEWCannonBall::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWCannonBall, bLanded);
    DOREPLIFETIME(AEWCannonBall, LandedAt);
}

void AEWCannonBall::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority()) return;
    // Each screen flies its own copy from the server's velocity, smoothly between updates; only the server's
    // copy collides and decides where it lands.
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RecentShots.Add(this);
    if (!bLanded) Movement->Activate(true);
}

void AEWCannonBall::PostNetReceiveVelocity(const FVector& NewVelocity)
{
    if (!bLanded) Movement->Velocity = NewVelocity;
}

void AEWCannonBall::OnRep_Landed()
{
    if (!bLanded) return;
    Movement->StopMovementImmediately();
    Movement->Deactivate();
    SetActorLocation(LandedAt);
}

void AEWCannonBall::Launch(AEWShip* From, AEWCharacter* ByGunner, const FVector& Velocity)
{
    if (!HasAuthority()) return;
    FiredFrom = From;
    Gunner = ByGunner;
    if (From)
    {
        WaterZ = From->SurfaceZ;
        Collision->IgnoreActorWhenMoving(From, true);
    }
    Movement->Velocity = Velocity;
    Movement->OnProjectileStop.AddDynamic(this, &AEWCannonBall::OnStopped);
    Movement->Activate(true);
    RecentShots.Add(this);
    RecentShots.RemoveAll([](const TWeakObjectPtr<AEWCannonBall>& Shot) { return !Shot.IsValid(); });
}

AEWCannonBall* AEWCannonBall::GetLastShot(const UObject* WorldContext)
{
    const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
    for (int32 i = RecentShots.Num() - 1; i >= 0; --i)
        if (AEWCannonBall* Shot = RecentShots[i].Get()) if (Shot->GetWorld() == World) return Shot;
    return nullptr;
}

void AEWCannonBall::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (HasAuthority() && !bLanded && GetActorLocation().Z < WaterZ) Land(FVector(GetActorLocation().X, GetActorLocation().Y, WaterZ), FVector::UpVector, nullptr);
}

void AEWCannonBall::OnStopped(const FHitResult& Hit)
{
    if (!bLanded) Land(Hit.ImpactPoint, Hit.ImpactNormal, Hit.GetActor());
}

void AEWCannonBall::Land(const FVector& Where, const FVector& Normal, AActor* Hit)
{
    if (!HasAuthority() || bLanded) return;
    if (Cast<AWaterBody>(Hit)) Hit = nullptr;   // the sea's surface: a splash, not a strike
    if (auto* Ship = Cast<AEWShip>(Hit)) Ship->TakeRoundShot(Where, Normal, Gunner.Get());
    bLanded = true;
    LandedAt = Where;
    Struck = Hit;
    Movement->StopMovementImmediately();
    Movement->Deactivate();
    SetActorLocation(Where);
    ForceNetUpdate();
    // Gone a moment later, long enough for every screen to see where it fell.
    SetLifeSpan(1.f);
}
