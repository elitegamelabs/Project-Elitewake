#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Engine/DataAsset.h"
#include "Subsystems/WorldSubsystem.h"
#include "EWCobweb.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class UStaticMesh;

/** Where the caves' cobwebs hang in one map, written by Scripts/Setup/build_cave_webs.py from the caves' layout. */
UCLASS(BlueprintType)
class EW_API UEWCaveWebSet : public UDataAsset
{
    GENERATED_BODY()
public:
    /** The map the webs belong to. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Webs")
    TSoftObjectPtr<UWorld> Map;
    /** Each web: where its middle hangs, which way it faces (+X through it), and its size (1 = 2 m across). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Webs")
    TArray<FTransform> Webs;
};

/**
 * A cobweb in a cave, only for show (owner, October 15: webs you can walk through that fall apart). It blocks
 * nothing; a survivor walking into it tears it, and it falls away in drifting strands. Each machine keeps its own
 * webs (nothing is replicated): every screen sees a survivor walk through, so every screen tears the same web.
 * DECIDED (delegated, tuning): a torn web is spun again after ten minutes.
 */
UCLASS(NotPlaceable)
class EW_API AEWCobweb : public AActor
{
    GENERATED_BODY()
public:
    AEWCobweb();
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintPure, Category="Webs") bool IsTorn() const { return bTorn; }
    /** How many torn strands are still falling (for the checks). */
    UFUNCTION(BlueprintPure, Category="Webs") int32 GetFallingStrands() const { return Shreds.Num(); }
    /** Tears it as if walked through (the checks use this to watch it fall). */
    UFUNCTION(BlueprintCallable, Category="Webs") void Tear();

    /** Gives it the web's mesh (the subsystem that hangs it). */
    void SetWebMesh(UStaticMesh* Mesh);

    static constexpr float FallSeconds = 2.5f;
    static constexpr float RegrowSeconds = 600.f;
    static constexpr int32 ShredCount = 7;

private:
    UPROPERTY(VisibleAnywhere, Category="Webs") TObjectPtr<USceneComponent> Root;
    UPROPERTY(VisibleAnywhere, Category="Webs") TObjectPtr<UStaticMeshComponent> Web;
    UPROPERTY(VisibleAnywhere, Category="Webs") TObjectPtr<UBoxComponent> Touch;
    UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Shreds;
    TArray<FVector> ShredDrift;
    TArray<FRotator> ShredSpin;
    bool bTorn = false;
    float TornSeconds = 0.f;

    UFUNCTION()
    void OnTouched(UPrimitiveComponent* Component, AActor* Other, UPrimitiveComponent* OtherComponent, int32 BodyIndex,
        bool bFromSweep, const FHitResult& Sweep);
    void Regrow();
};

/** Hangs the cobwebs of the caves in the map being played (DA_CaveWebs), on every machine that shows the world. */
UCLASS()
class EW_API UEWCaveWebSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void OnWorldBeginPlay(UWorld& InWorld) override;
    virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override
    {
        return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
    }
};
