#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Blueprint/UserWidget.h"
#include "EWWorkFeedback.generated.h"

class UEWItemDefinition;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;

/** What a blow or a gather put in the survivor's pack: an item and how many. */
USTRUCT(BlueprintType)
struct FEWGatherGain
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Gathering") TObjectPtr<UEWItemDefinition> Item = nullptr;
    UPROPERTY(BlueprintReadOnly, Category="Gathering") int32 Count = 0;
};

/** What a work blow struck, for its chips and sound. */
UENUM(BlueprintType)
enum class EEWWorkSurface : uint8 { Wood, Stone };

/** Why a blow at a tree or rock gave nothing. */
UENUM(BlueprintType)
enum class EEWWorkRefusal : uint8 { None, NeedsHatchet, NeedsPickaxe, PackFull };

/**
 * Chips knocked off where a hatchet or pickaxe lands: splinters and bark from wood, grit and flakes from stone. Made
 * on each machine for the blow it sees (cosmetic, never replicated); they fly out from the face, tumble, fall and
 * fade within a second and a half.
 */
UCLASS(NotBlueprintable)
class EW_API AEWImpactBurst : public AActor
{
    GENERATED_BODY()
public:
    AEWImpactBurst();
    virtual void Tick(float DeltaSeconds) override;
    /** Every machine: chips at Point, flying off the face (Normal). Returns the burst, or null on a server without a screen. */
    static AEWImpactBurst* Spawn(UWorld* World, const FVector& Point, const FVector& Normal, EEWWorkSurface Surface);
    UFUNCTION(BlueprintPure, Category="Gathering") int32 GetChipCount() const { return Chips.Num(); }

private:
    struct FChip { TObjectPtr<UStaticMeshComponent> Part; FVector Velocity; FRotator Spin; FVector Scale; };
    TArray<FChip> Chips;
    float Age = 0.f;
    UPROPERTY() TObjectPtr<UStaticMesh> CubeMesh;
    UPROPERTY() TObjectPtr<UMaterialInterface> ShapeMaterial;
    void Fill(const FVector& Normal, EEWWorkSurface Surface);
};

/**
 * The striker's own hit marker: four ticks round the centre of the screen that pop and fade when a blow lands (white
 * when it gave something, amber when it did not), what the blow or a gather gave rising beside it ("+3 Wood"), and
 * why nothing came ("Needs a pickaxe") under it.
 */
UCLASS()
class EW_API UEWHitMarkerWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void ShowHit(bool bGave, const TArray<FEWGatherGain>& Gains, EEWWorkRefusal Refusal);
    void ShowGains(const TArray<FEWGatherGain>& Gains);
    /** For the checks: markers and popups shown so far, and the latest line of text. */
    UFUNCTION(BlueprintPure, Category="Gathering") int32 GetMarkerCount() const { return MarkerCount; }
    UFUNCTION(BlueprintPure, Category="Gathering") FString GetLastLine() const { return LastLine; }
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& Geometry, float Delta) override;
    virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
private:
    struct FPopup { FString Text; float Age = 0.f; FLinearColor Colour; bool bBelow = false; };
    void AddLine(const FString& Text, const FLinearColor& Colour, bool bBelow);
    TArray<FPopup> Popups;
    float MarkerAge = -1.f;
    bool bMarkerGave = false;
    int32 MarkerCount = 0;
    FString LastLine;
};
