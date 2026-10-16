#include "Wildlife/EWWildlifeRest.h"
#include "EWCharacter.h"
#include "EngineUtils.h"

bool FEWWildlifeRest::IsAwake(const AActor* Creature, float DeltaSeconds)
{
    Look -= DeltaSeconds;
    if (Look <= 0.f && Creature && Creature->GetWorld())
    {
        Look = LookSeconds * FMath::FRandRange(.8f, 1.2f);   // spread the looks over frames
        bAwake = false;
        const FVector Here = Creature->GetActorLocation();
        for (TActorIterator<AEWCharacter> It(Creature->GetWorld()); It && !bAwake; ++It)
            bAwake = FVector::DistSquared(It->GetActorLocation(), Here) < RestRange * RestRange;
    }
    return bAwake;
}
