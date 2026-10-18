#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "EWPlacementPreviewComponent.generated.h"

class AEWShip;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UEWItemDefinition;

/**
 * Where a placeable would go, before it is placed (owner, October 17: placeable items show a blue highlight where they
 * can be placed, red where they cannot, and look normal once placed; design: Build Mode's blue and red ghost). On the
 * player's own screen only. Today the placeables are ship fittings: carrying one (a sail, a wheel, a cannon, a railing
 * module) and looking at a ship's mount of its kind shows a glowing copy of it there, blue if it would be installed,
 * red if not (the wrong sail size, the mount taken, a cannon place with no cannon railing). Once installed it is drawn
 * as itself. Build Mode's pieces will use the same highlight (EW/UI/M_PlacementGhost_v1).
 */
UCLASS(ClassGroup=(UI))
class EW_API UEWPlacementPreviewComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWPlacementPreviewComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** For the checks: whether a preview is showing, whether it is the blue (placeable) one, and where. */
    UFUNCTION(BlueprintPure, Category="Placement") bool IsShowing() const;
    UFUNCTION(BlueprintPure, Category="Placement") bool IsPlaceable() const { return bPlaceable; }
    UFUNCTION(BlueprintPure, Category="Placement") FName GetPreviewMount() const { return ShownMount; }
    UFUNCTION(BlueprintPure, Category="Placement") UEWItemDefinition* GetPreviewItem() const { return ShownItem; }

    /** The highlight colours (tuning). */
    static const FLinearColor Placeable;
    static const FLinearColor NotPlaceable;

private:
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Ghost;
    UPROPERTY(Transient) TObjectPtr<class AStaticMeshActor> GhostActor;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Glow;
    UPROPERTY(Transient) TObjectPtr<UEWItemDefinition> ShownItem;
    FName ShownMount;
    bool bPlaceable = false;
    void Hide();
};
