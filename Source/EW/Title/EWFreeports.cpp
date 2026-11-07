#include "Title/EWFreeports.h"
#include "EWCrewMaster.h"
#include "EWMerchant.h"
#include "EngineUtils.h"

bool EWFreeports::FindSpawn(UWorld* World, int32 Index, FVector& OutLocation, FRotator& OutFacing)
{
    if (!World || Index < 0 || Index >= Count) return false;
    const FVector2D Centre = List[Index].Centre;
    // The Port's general merchant (not its crew master) nearest the site's middle, within the Port.
    const AEWMerchant* Merchant = nullptr;
    for (TActorIterator<AEWMerchant> It(World); It; ++It)
    {
        if (It->IsA<AEWCrewMaster>()) continue;
        const double Distance = FVector2D::Distance(FVector2D(It->GetActorLocation()), Centre);
        if (Distance < 40000.0 && (!Merchant || Distance < FVector2D::Distance(FVector2D(Merchant->GetActorLocation()), Centre))) Merchant = *It;
    }
    if (!Merchant) return false;
    OutLocation = Merchant->GetActorLocation() + Merchant->GetActorForwardVector() * 220.f + FVector(0.f, 0.f, 110.f);
    OutFacing = FRotator(0.f, (-Merchant->GetActorForwardVector()).Rotation().Yaw, 0.f);
    return true;
}
