#include "EWWindSubsystem.h"
#include "Engine/World.h"

void UEWWindSubsystem::SetWindYaw(float NewYaw)
{
    if (FMath::IsFinite(NewYaw) && (!GetWorld() || GetWorld()->GetNetMode() != NM_Client))
        WindYaw = FRotator::NormalizeAxis(NewYaw);
}

float UEWWindSubsystem::GetHeadingFactor(const FVector& ShipForward) const
{
    const FVector Heading = FVector(ShipForward.X, ShipForward.Y, 0).GetSafeNormal();
    if (Heading.IsNearlyZero()) return MinUpwindFactor;
    // Cosine is 1 when the ship runs with the wind and -1 when it heads into it.
    const float Alignment = FVector::DotProduct(Heading, GetWindDirection());
    return MinUpwindFactor + (1.f - MinUpwindFactor) * (Alignment + 1.f) * .5f;
}
