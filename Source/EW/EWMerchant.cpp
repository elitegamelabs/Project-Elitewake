#include "EWMerchant.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWWalletComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWMerchant::AEWMerchant()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetNetUpdateFrequency(2.f);
    auto* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
    Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
    Body->SetupAttachment(Root);
    if (Cylinder.Succeeded()) Body->SetStaticMesh(Cylinder.Object);
    Body->SetRelativeLocation(FVector(0, 0, 60));
    Body->SetRelativeScale3D(FVector(.55f, .55f, 1.2f));
    // Solid to people and to aim (the interaction trace), nothing else: a ship moored by the plaza must never catch on it.
    Body->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Body->SetCollisionObjectType(ECC_WorldDynamic);
    Body->SetCollisionResponseToAllChannels(ECR_Ignore);
    Body->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Head = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Head"));
    Head->SetupAttachment(Body);
    if (Sphere.Succeeded()) Head->SetStaticMesh(Sphere.Object);
    Head->SetRelativeLocation(FVector(0, 0, 62));
    Head->SetRelativeScale3D(FVector(.7f, .7f, .4f));
    Head->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Hat = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Hat"));
    Hat->SetupAttachment(Head);
    if (Cone.Succeeded()) Hat->SetStaticMesh(Cone.Object);
    Hat->SetRelativeLocation(FVector(0, 0, 50));
    Hat->SetRelativeScale3D(FVector(.9f, .9f, .6f));
    Hat->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AEWMerchant::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AEWMerchant, SalesMade);
}

void AEWMerchant::Appraise(const AEWCharacter* Character, int32& OutItems, int64& OutCopper)
{
    OutItems = 0;
    OutCopper = 0;
    if (!IsValid(Character) || !Character->GetInventoryComponent()) return;
    for (const FEWInventoryEntry& Entry : Character->GetInventoryComponent()->GetInventoryEntries())
    {
        if (!Entry.ItemDefinition || Entry.ItemDefinition->SellValueCopper <= 0 || Entry.Quantity <= 0) continue;
        OutItems += Entry.Quantity;
        OutCopper += int64(Entry.ItemDefinition->SellValueCopper) * Entry.Quantity;
    }
}

bool AEWMerchant::CanInteract_Implementation(AEWCharacter* Character) const
{
    return IsValid(Character) && !Character->IsDead();
}

FText AEWMerchant::GetInteractionPrompt_Implementation(AEWCharacter* Character) const
{
    int32 Items = 0; int64 Copper = 0;
    Appraise(Character, Items, Copper);
    if (Items <= 0) return NSLOCTEXT("Elitewake", "MerchantNothing", "Merchant: nothing here I would buy");
    return FText::Format(NSLOCTEXT("Elitewake", "MerchantSell", "Sell {0} items for {1}"), FText::AsNumber(Items), FText::FromString(UEWWalletComponent::Format(Copper)));
}

bool AEWMerchant::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character) || FVector::Dist(Character->GetActorLocation(), GetActorLocation()) > TradeReach) return false;
    UEWInventoryComponent* Pack = Character->GetInventoryComponent();
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Pack || !Purse) return false;
    int64 Earned = 0;
    for (const FEWInventoryEntry& Entry : Pack->GetInventoryEntries())          // a copy: removing changes the pack
    {
        if (!Entry.ItemDefinition || Entry.ItemDefinition->SellValueCopper <= 0 || Entry.Quantity <= 0) continue;
        const int32 Taken = Pack->RemoveItem(Entry.ItemDefinition, Entry.Quantity);
        Earned += int64(Entry.ItemDefinition->SellValueCopper) * Taken;
    }
    if (Earned <= 0) return false;
    Purse->AddCopper(Earned);
    ++SalesMade;
    ForceNetUpdate();
    return true;
}
