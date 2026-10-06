#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWPickup.generated.h"

class AEWCharacter;
class UEWItemDefinition;
class UStaticMeshComponent;

/** World stack. Transfer is serialized on the server and consumes only accepted inventory units. */
UCLASS(Blueprintable)
class EW_API AEWPickup : public AActor
{
    GENERATED_BODY()
public:
    AEWPickup();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Pickup")
    TObjectPtr<UStaticMeshComponent> Mesh;

    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Pickup")
    TObjectPtr<UEWItemDefinition> ItemDefinition;

    UPROPERTY(EditAnywhere, Replicated, BlueprintReadOnly, Category="Pickup", meta=(ClampMin="1"))
    int32 Quantity = 1;

    /** Uses the possessed character's eyes/control rotation on both client and server. */
    static AEWPickup* FindTarget(const AEWCharacter* Character);

    /** Authority only. Requires possession, range, aim/visibility and any assigned actor ownership. */
    int32 TryPickup(AEWCharacter* Character);

    static constexpr float InteractionRange = 250.f;
private:
    bool bTransferInProgress = false;
};
