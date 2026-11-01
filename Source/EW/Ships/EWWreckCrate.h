#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EWInteractable.h"
#include "EWWreckCrate.generated.h"

class UEWInventoryComponent;
class UStaticMeshComponent;
struct FEWSavedContainer;

/**
 * A crate floating where a ship went down, holding part of what she carried (design reference: wreck loot floats in
 * crates for about 15 real minutes). A survivor beside it (swimming or aboard a boat) opens it like a ship's hold and
 * takes what they want. It bobs on the swell where it surfaced; an emptied crate sinks at once, and every crate is
 * gone after LifeSeconds. The server owns its contents.
 */
UCLASS(NotPlaceable)
class EW_API AEWWreckCrate : public AActor, public IEWInteractable
{
    GENERATED_BODY()
public:
    AEWWreckCrate();
    virtual void Tick(float DeltaSeconds) override;
    virtual void BeginPlay() override;

    /** Design reference: about 15 real minutes. */
    static constexpr float LifeSeconds = 15.f * 60.f;
    /** How close a survivor must be to reach into it, cm (tuning). */
    static constexpr float Reach = 350.f;
    /** Item stacks per crate (tuning). */
    static constexpr int32 SlotsPerCrate = 6;

    UFUNCTION(BlueprintPure, Category="Wreck")
    UEWInventoryComponent* GetContents() const { return Contents; }
    UFUNCTION(BlueprintPure, Category="Wreck")
    bool CanAccess(const AEWCharacter* Character) const;
    /** The sea surface it floats on, world cm. */
    UPROPERTY(Replicated, BlueprintReadOnly, Category="Wreck")
    float SurfaceZ = -65.f;

    /** Saving (M7): the crate as a save keeps it, and a new crate made as saved (authority). */
    FEWSavedContainer CaptureForSave() const;
    void RestoreSaved(const FEWSavedContainer& Saved);

    virtual bool CanInteract_Implementation(AEWCharacter* Character) const override;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Character) const override;
    virtual bool Interact_Implementation(AEWCharacter* Character) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    UPROPERTY(VisibleAnywhere, Category="Wreck")
    TObjectPtr<UStaticMeshComponent> Box;
    UPROPERTY(VisibleAnywhere, Category="Wreck")
    TObjectPtr<UEWInventoryComponent> Contents;
    float BobTime = 0.f;
    bool bEverFilled = false;
};

/** What a survivor may open in the container screen: a ship's hold, a wreck crate, a death bag or their strongbox. */
struct EW_API FEWContainerAccess
{
    /** The goods the screen shows. A strongbox's are the survivor's own, so it needs to know whose. */
    static UEWInventoryComponent* Inventory(const AActor* Container, const AEWCharacter* Survivor = nullptr);
    static bool CanAccess(const AActor* Container, const AEWCharacter* Survivor);
    /** The screen's title and the container column's heading. */
    static FText Title(const AActor* Container);
    static FText Heading(const AActor* Container);
};
