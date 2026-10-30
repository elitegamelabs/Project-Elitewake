#include "EWMerchant.h"
#include "EWCharacter.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWWalletComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EWInteractable.h"
#include "TimerManager.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

AEWMerchant::AEWMerchant()
{
    USceneComponent* Root = GetRootComponent();
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
    DOREPLIFETIME(AEWMerchant, StockLeft);
}

void AEWMerchant::BeginPlay()
{
    Super::BeginPlay();
    // With a person's figure the placeholder shapes go (the figure's capsule takes aim and blocks instead).
    if (FigureMesh)
    {
        for (UStaticMeshComponent* Part : {Body.Get(), Head.Get(), Hat.Get()}) Part->SetVisibility(false);
        Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    BuildStall();
    if (!HasAuthority() || Goods.IsEmpty()) return;
    StockLeft.SetNum(Goods.Num());
    for (int32 Index = 0; Index < Goods.Num(); ++Index) StockLeft[Index] = FMath::Max(1, Goods[Index].MaxStock);
    GetWorldTimerManager().SetTimer(RestockTimer, this, &AEWMerchant::Restock, FMath::Max(1.f, RestockSeconds), true);
}

void AEWMerchant::BuildStall()
{
    if (!bBuildStall || Goods.IsEmpty() || Counter) return;
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (!Cube) return;
    // A plain counter at the merchant's right hand, one crate per goods line on it (placeholders). Crates take aim, so a survivor
    // picks goods by looking at them; the counter stands clear of the line to the merchant, so selling is aimed as before.
    constexpr float Spacing = 45.f, Start = 95.f;
    const float Length = Goods.Num() * Spacing + 20.f;
    auto MakePart = [&](const TCHAR* Name, const FVector& Location, const FVector& Scale, UStaticMesh* Mesh) {
        auto* Part = NewObject<UStaticMeshComponent>(this, Name);
        Part->SetupAttachment(GetRootComponent());
        Part->SetStaticMesh(Mesh);
        Part->SetRelativeLocation(Location);
        Part->SetRelativeScale3D(Scale);
        Part->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Part->SetCollisionObjectType(ECC_WorldDynamic);
        Part->SetCollisionResponseToAllChannels(ECR_Ignore);
        Part->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
        Part->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
        Part->RegisterComponent();
        return Part;
    };
    Counter = MakePart(TEXT("Counter"), FVector(40, Start - 10.f + Length * .5f, 40), FVector(.55f, Length / 100.f, .8f), Cube);
    for (int32 Index = 0; Index < Goods.Num(); ++Index)
    {
        const FVector Spot(40, Start + Spacing * (Index + .5f), 80 + 16);
        Crates.Add(MakePart(*FString::Printf(TEXT("GoodsCrate%d"), Index), Spot, FVector(.34f, .34f, .32f), Cube));
        // The goods themselves on top when the item has a model, shrunk to sit on the crate; looks only.
        const UEWItemDefinition* Item = Goods[Index].Item;
        if (UStaticMesh* Model = Item ? Item->HeldMesh.LoadSynchronous() : nullptr)
        {
            auto* Show = NewObject<UStaticMeshComponent>(this, *FString::Printf(TEXT("GoodsShow%d"), Index));
            Show->SetupAttachment(GetRootComponent());
            Show->SetStaticMesh(Model);
            const float Extent = FMath::Max(1.f, Model->GetBounds().BoxExtent.GetMax());
            Show->SetRelativeScale3D(FVector(FMath::Min(1.f, 15.f / Extent)));
            Show->SetRelativeLocation(Spot + FVector(0, 0, 32));
            Show->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Show->RegisterComponent();
        }
    }
}

int64 AEWMerchant::GetGoodsPrice(int32 Index) const
{
    if (!Goods.IsValidIndex(Index) || !Goods[Index].Item) return 0;
    const FEWMerchantGoods& Line = Goods[Index];
    const int64 SellsBackFor = int64(Line.Item->SellValueCopper) * Line.Bundle;
    return FMath::Max<int64>(Line.PriceCopper, SellsBackFor + 1);
}

int32 AEWMerchant::FindAimedGoods(const AEWCharacter* Character) const
{
    if (Crates.IsEmpty() || !IsValid(Character) || !GetWorld() || !Character->GetController()
        || Character->GetController()->GetPawn() != Character) return INDEX_NONE;
    FVector Eye; FRotator Rotation;
    Character->GetActorEyesViewPoint(Eye, Rotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(EWMerchantAim), false, Character);
    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(Hit, Eye, Eye + Rotation.Vector() * FEWInteractionTargeting::Range, ECC_Visibility, Query)
        || Hit.GetActor() != this) return INDEX_NONE;
    return Crates.IndexOfByKey(Hit.GetComponent());
}

FVector AEWMerchant::GetGoodsLocation(int32 Index) const
{
    return Crates.IsValidIndex(Index) && Crates[Index] ? Crates[Index]->GetComponentLocation() : GetActorLocation();
}

bool AEWMerchant::Buy(AEWCharacter* Character, int32 Index)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character) || !Goods.IsValidIndex(Index) || !Goods[Index].Item
        || GetStockLeft(Index) <= 0 || FVector::Dist(Character->GetActorLocation(), GetActorLocation()) > TradeReach) return false;
    UEWInventoryComponent* Pack = Character->GetInventoryComponent();
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    const int64 Price = GetGoodsPrice(Index);
    if (!Pack || !Purse || !Purse->CanAfford(Price)) return false;
    const FEWMerchantGoods& Line = Goods[Index];
    const int32 Added = Pack->AddItem(Line.Item, Line.Bundle);
    if (Added < Line.Bundle || !Purse->TrySpend(Price))
    {
        // Not all of it fits, or the purse came up short: nothing is sold.
        if (Added > 0) Pack->RemoveItem(Line.Item, Added);
        return false;
    }
    --StockLeft[Index];
    ForceNetUpdate();
    return true;
}

void AEWMerchant::Restock()
{
    if (!HasAuthority()) return;
    bool bChanged = false;
    for (int32 Index = 0; Index < StockLeft.Num() && Index < Goods.Num(); ++Index)
        if (StockLeft[Index] < Goods[Index].MaxStock) { ++StockLeft[Index]; bChanged = true; }
    if (bChanged) ForceNetUpdate();
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
    if (const int32 Index = FindAimedGoods(Character); Goods.IsValidIndex(Index) && Goods[Index].Item)
    {
        const FEWMerchantGoods& Line = Goods[Index];
        const FText Name = Line.Bundle > 1
            ? FText::Format(NSLOCTEXT("Elitewake", "MerchantBundle", "{0} x{1}"), Line.Item->DisplayName, FText::AsNumber(Line.Bundle))
            : Line.Item->DisplayName;
        const FText Price = FText::FromString(UEWWalletComponent::Format(GetGoodsPrice(Index)));
        if (GetStockLeft(Index) <= 0) return FText::Format(NSLOCTEXT("Elitewake", "MerchantSoldOut", "{0}: sold out"), Name);
        const UEWWalletComponent* Purse = IsValid(Character) ? Character->GetWalletComponent() : nullptr;
        if (!Purse || !Purse->CanAfford(GetGoodsPrice(Index)))
            return FText::Format(NSLOCTEXT("Elitewake", "MerchantTooDear", "{0} costs {1}"), Name, Price);
        return FText::Format(NSLOCTEXT("Elitewake", "MerchantBuy", "Buy {0} for {1} ({2} left)"), Name, Price, FText::AsNumber(GetStockLeft(Index)));
    }
    if (HasDialogue()) return Super::GetInteractionPrompt_Implementation(Character);
    int32 Items = 0; int64 Copper = 0;
    Appraise(Character, Items, Copper);
    if (Items <= 0) return NSLOCTEXT("Elitewake", "MerchantNothing", "Merchant: nothing here I would buy");
    return FText::Format(NSLOCTEXT("Elitewake", "MerchantSell", "Sell {0} items for {1}"), FText::AsNumber(Items), FText::FromString(UEWWalletComponent::Format(Copper)));
}

bool AEWMerchant::Interact_Implementation(AEWCharacter* Character)
{
    if (!HasAuthority() || !CanInteract_Implementation(Character) || FVector::Dist(Character->GetActorLocation(), GetActorLocation()) > TradeReach) return false;
    if (const int32 Index = FindAimedGoods(Character); Index != INDEX_NONE) return Buy(Character, Index);
    if (HasDialogue()) return Super::Interact_Implementation(Character);
    return SellAll(Character) > 0;
}

int64 AEWMerchant::SellAll(AEWCharacter* Character)
{
    if (!HasAuthority() || !IsValid(Character) || Character->IsDead() || FVector::Dist(Character->GetActorLocation(), GetActorLocation()) > TradeReach) return 0;
    UEWInventoryComponent* Pack = Character->GetInventoryComponent();
    UEWWalletComponent* Purse = Character->GetWalletComponent();
    if (!Pack || !Purse) return 0;
    int64 Earned = 0;
    for (const FEWInventoryEntry& Entry : Pack->GetInventoryEntries())          // a copy: removing changes the pack
    {
        if (!Entry.ItemDefinition || Entry.ItemDefinition->SellValueCopper <= 0 || Entry.Quantity <= 0) continue;
        const int32 Taken = Pack->RemoveItem(Entry.ItemDefinition, Entry.Quantity);
        Earned += int64(Entry.ItemDefinition->SellValueCopper) * Taken;
    }
    if (Earned <= 0) return 0;
    Purse->AddCopper(Earned);
    ++SalesMade;
    ForceNetUpdate();
    return Earned;
}

FText AEWMerchant::GoodsName(int32 Index) const
{
    if (!Goods.IsValidIndex(Index) || !Goods[Index].Item) return FText::GetEmpty();
    const FEWMerchantGoods& Line = Goods[Index];
    return Line.Bundle > 1
        ? FText::Format(NSLOCTEXT("Elitewake", "MerchantBundle", "{0} x{1}"), Line.Item->DisplayName, FText::AsNumber(Line.Bundle))
        : Line.Item->DisplayName;
}

void AEWMerchant::GetDialogueOptions(const AEWCharacter* Character, TArray<FEWDialogueOption>& Out) const
{
    const UEWWalletComponent* Purse = IsValid(Character) ? Character->GetWalletComponent() : nullptr;
    for (int32 Index = 0; Index < Goods.Num(); ++Index)
    {
        if (!Goods[Index].Item) continue;
        const int64 Price = GetGoodsPrice(Index);
        const FText Label = GetStockLeft(Index) <= 0
            ? FText::Format(NSLOCTEXT("Elitewake", "MerchantOptionSoldOut", "{0}: sold out"), GoodsName(Index))
            : FText::Format(NSLOCTEXT("Elitewake", "MerchantOptionBuy", "Buy {0} for {1} ({2} left)"), GoodsName(Index),
                FText::FromString(UEWWalletComponent::Format(Price)), FText::AsNumber(GetStockLeft(Index)));
        Out.Add({FName(*FString::Printf(TEXT("Buy%d"), Index)), Label, GetStockLeft(Index) > 0 && Purse && Purse->CanAfford(Price)});
    }
    int32 Items = 0; int64 Copper = 0;
    Appraise(Character, Items, Copper);
    Out.Add({FName(TEXT("SellAll")), Items > 0
        ? FText::Format(NSLOCTEXT("Elitewake", "MerchantOptionSell", "Sell everything I would buy: {0} items for {1}"), FText::AsNumber(Items), FText::FromString(UEWWalletComponent::Format(Copper)))
        : NSLOCTEXT("Elitewake", "MerchantOptionSellNone", "Sell: you carry nothing I would buy"), Items > 0});
}

FText AEWMerchant::ActOnDialogue(AEWCharacter* Character, FName Key)
{
    if (Key == FName(TEXT("SellAll")))
    {
        const int64 Earned = SellAll(Character);
        return Earned > 0 ? FText::Format(NSLOCTEXT("Elitewake", "MerchantSold", "A fair lot. {0} for the lot."), FText::FromString(UEWWalletComponent::Format(Earned)))
                          : NSLOCTEXT("Elitewake", "MerchantNothingSold", "Nothing there I would buy.");
    }
    const FString Name = Key.ToString();
    if (Name.StartsWith(TEXT("Buy")))
    {
        const int32 Index = FCString::Atoi(*Name.RightChop(3));
        if (Buy(Character, Index))
            return FText::Format(NSLOCTEXT("Elitewake", "MerchantBought", "{0}, yours. That is {1}."), GoodsName(Index), FText::FromString(UEWWalletComponent::Format(GetGoodsPrice(Index))));
        return NSLOCTEXT("Elitewake", "MerchantNoSale", "Your pack is too full for that, friend.");
    }
    return FText::GetEmpty();
}
