#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EWAppearance.generated.h"

class USkeletalMesh;
class USkeletalMeshComponent;
class UMaterialInterface;

/** One body a survivor can be made from, and how its colouring is chosen. */
USTRUCT(BlueprintType)
struct FEWBodyOption
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    FText DisplayName;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TSoftObjectPtr<USkeletalMesh> Mesh;
    /** If set, the body is dressed in this material (every slot) before it is toned. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TSoftObjectPtr<UMaterialInterface> ToneMaterial;
    /** Vector material parameters on the body that take the chosen tone. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TArray<FName> ToneParameters;
};

/** The bodies and tones offered when a survivor is made. Bodies can be added without code. */
UCLASS(BlueprintType)
class EW_API UEWBodyRoster : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TArray<FEWBodyOption> Bodies;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Appearance")
    TArray<FLinearColor> Tones;
};

/** How a survivor looks. Small and replicated; every machine builds the look from it. */
USTRUCT(BlueprintType)
struct FEWAppearance
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    uint8 Body = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    uint8 Tone = 0;
    /** Height relative to the body's own, 1 = as made (tuning range MinHeight-MaxHeight). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance")
    float Height = 1.f;

    static constexpr float MinHeight = .92f;
    static constexpr float MaxHeight = 1.08f;

    bool operator==(const FEWAppearance& Other) const { return Body == Other.Body && Tone == Other.Tone && Height == Other.Height; }
    /** Brought within what the roster offers, so a bad request can never break a survivor. */
    FEWAppearance Clamped(const UEWBodyRoster* Roster) const;
    /** Dresses a mesh in this look: its body, tone and height. Returns false if the roster lacks the body. */
    bool ApplyTo(USkeletalMeshComponent* Mesh, const UEWBodyRoster* Roster) const;
};
