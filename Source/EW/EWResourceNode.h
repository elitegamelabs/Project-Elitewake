#pragma once
#include "CoreMinimal.h"
#include "EWStation.h"
#include "EWResourceNode.generated.h"

UENUM(BlueprintType)
enum class EEWResourceNodeType : uint8 { Tree, Rock };

/** Fixture only. Inspect does not harvest: the later attack/tool path owns gathering. */
UCLASS(Blueprintable)
class EW_API AEWResourceNode : public AEWStation
{
    GENERATED_BODY()
public:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category="Fixture") EEWResourceNodeType ResourceType = EEWResourceNodeType::Tree;
    virtual FText GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const override;
};
