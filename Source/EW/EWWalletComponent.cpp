#include "EWWalletComponent.h"
#include "Net/UnrealNetwork.h"
#include "GameFramework/Actor.h"

UEWWalletComponent::UEWWalletComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UEWWalletComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWWalletComponent, Copper, COND_OwnerOnly);
}

void UEWWalletComponent::BeginPlay()
{
    Super::BeginPlay();
    if (GetOwner() && GetOwner()->HasAuthority() && Copper == 0) Copper = StartingCopper;
}

void UEWWalletComponent::SetCopper(int64 Amount)
{
    if (GetOwner() && GetOwner()->HasAuthority()) Copper = FMath::Max<int64>(0, Amount);
}

void UEWWalletComponent::AddCopper(int64 Amount)
{
    if (GetOwner() && GetOwner()->HasAuthority() && Amount > 0) Copper += Amount;
}

bool UEWWalletComponent::TrySpend(int64 Amount)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || Amount < 0 || Copper < Amount) return false;
    Copper -= Amount;
    return true;
}

FString UEWWalletComponent::Format(int64 Amount)
{
    const int64 Gold = Amount / (CopperPerSilver * SilverPerGold);
    const int64 Silver = (Amount / CopperPerSilver) % SilverPerGold;
    const int64 Rest = Amount % CopperPerSilver;
    TArray<FString> Parts;
    if (Gold > 0) Parts.Add(FString::Printf(TEXT("%lld Gold"), Gold));
    if (Silver > 0) Parts.Add(FString::Printf(TEXT("%lld Silver"), Silver));
    if (Rest > 0 || Parts.IsEmpty()) Parts.Add(FString::Printf(TEXT("%lld Copper"), Rest));
    return FString::Join(Parts, TEXT(" "));
}

FString UEWWalletComponent::FormatShort(int64 Amount)
{
    const int64 Gold = Amount / (CopperPerSilver * SilverPerGold);
    const int64 Silver = (Amount / CopperPerSilver) % SilverPerGold;
    const int64 Rest = Amount % CopperPerSilver;
    TArray<FString> Parts;
    if (Gold > 0) Parts.Add(FString::Printf(TEXT("%lldg"), Gold));
    if (Silver > 0) Parts.Add(FString::Printf(TEXT("%llds"), Silver));
    if (Rest > 0 || Parts.IsEmpty()) Parts.Add(FString::Printf(TEXT("%lldc"), Rest));
    return FString::Join(Parts, TEXT(" "));
}
