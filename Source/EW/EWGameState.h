#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "EWGameState.generated.h"

/** A ship's coarse position for the world map, independent of actor relevancy at sea. */
USTRUCT(BlueprintType)
struct FEWShipMapEntry
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Map") FVector Location = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Map") float Yaw = 0.f;
};

/** The public map shows boats even when terrain or a sea cavern hides them in the world. */
UCLASS()
class EW_API AEWGameState : public AGameStateBase
{
    GENERATED_BODY()
public:
    AEWGameState();
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(Replicated, BlueprintReadOnly, Category="Map")
    TArray<FEWShipMapEntry> ShipsOnMap;
};
