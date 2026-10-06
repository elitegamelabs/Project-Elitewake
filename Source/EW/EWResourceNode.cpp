#include "EWResourceNode.h"
#include "Net/UnrealNetwork.h"
void AEWResourceNode::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps); DOREPLIFETIME(AEWResourceNode, ResourceType);
}
FText AEWResourceNode::GetInteractionPrompt_Implementation(AEWCharacter* Survivor) const
{
    return ResourceType == EEWResourceNodeType::Tree ? NSLOCTEXT("Elitewake","TestTree","Inspect Tree (test; no harvest)")
        : NSLOCTEXT("Elitewake","TestRock","Inspect Rock (test; no harvest)");
}
