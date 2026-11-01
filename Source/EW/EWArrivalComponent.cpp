#include "EWArrivalComponent.h"
#include "EWCharacter.h"
#include "EWCraftingRecipe.h"
#include "EWInventoryComponent.h"
#include "EWInventoryWidget.h"
#include "EWCrewMaster.h"
#include "EWFreeportServices.h"
#include "EWPlayerController.h"
#include "World/EWSafeZone.h"
#include "Ships/EWShip.h"
#include "EWItemDefinition.h"
#include "World/EWStrongbox.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerStart.h"
#include "Net/UnrealNetwork.h"

void FEWArrivalTracker::Begin(EEWArrivalStep InStep, const FEWArrivalSnapshot& Now)
{
    Step = InStep;
    Start = Last = Now;
    Looked = 0.f;
}

bool FEWArrivalTracker::Update(const FEWArrivalSnapshot& Now)
{
    bool bDone = false;
    switch (Step)
    {
    case EEWArrivalStep::Look:
        Looked += FMath::Abs(FRotator::NormalizeAxis(Now.Yaw - Last.Yaw)) + FMath::Abs(FRotator::NormalizeAxis(Now.Pitch - Last.Pitch));
        bDone = Looked >= LookDegrees;
        break;
    case EEWArrivalStep::Move: bDone = FVector::Dist2D(Now.Location, Start.Location) >= WalkDistance; break;
    case EEWArrivalStep::Jump: bDone = Now.bJumping; break;
    case EEWArrivalStep::Crouch: bDone = Now.bLow; break;
    default: break;   // the interact step is the server's to judge
    }
    Last = Now;
    return bDone;
}

UEWArrivalComponent::UEWArrivalComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = .05f;
    SetIsReplicatedByDefault(true);
    // The first tools, made by hand, then a fire and a berry dish cooked on it (Content/Elitewake/Crafting/Testing; slices 2-3 of Phase 1).
    for (const TCHAR* Name : {TEXT("StoneHatchet"), TEXT("WoodenPickaxe"), TEXT("Campfire"), TEXT("CookedBerryDish")})
        FirstRecipes.Add(TSoftObjectPtr<UEWCraftingRecipe>(FSoftObjectPath(FString::Printf(TEXT("/Game/Elitewake/Crafting/Testing/DA_Recipe%s.DA_Recipe%s"), Name, Name))));
}

void UEWArrivalComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWArrivalComponent, Step, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWArrivalComponent, TownDone, COND_OwnerOnly);
}

void UEWArrivalComponent::BeginPlay()
{
    Super::BeginPlay();
    ShowAt = GetWorld()->GetTimeSeconds() + FirstPromptDelay;
    if (!GetOwner()->HasAuthority()) return;
    // Only a map built for arriving teaches it (build_arrival.py tags its PlayerStart); test maps start finished.
    for (TActorIterator<APlayerStart> It(GetWorld()); It && !bArrivalMap; ++It) bArrivalMap = It->PlayerStartTag == ArrivalStartTag;
    if (!bArrivalMap) { Step = StepCount; TownDone = AllTownSteps; return; }
    if (auto* Pack = GetOwner()->FindComponentByClass<UEWInventoryComponent>())
        for (const TSoftObjectPtr<UEWCraftingRecipe>& Recipe : FirstRecipes)
            if (UEWCraftingRecipe* Loaded = Recipe.LoadSynchronous()) Pack->UnlockRecipe(Loaded);
}

bool UEWArrivalComponent::ReadSnapshot(FEWArrivalSnapshot& Out) const
{
    const auto* Survivor = Cast<AEWCharacter>(GetOwner());
    if (!Survivor || !Survivor->IsLocallyControlled() || !Survivor->GetController()) return false;
    const FRotator View = Survivor->GetControlRotation();
    const auto* Movement = Survivor->GetCharacterMovement();
    Out.Location = Survivor->GetActorLocation();
    Out.Yaw = View.Yaw;
    Out.Pitch = View.Pitch;
    Out.bJumping = Movement && Movement->IsFalling() && Movement->Velocity.Z > 50.f && Survivor->JumpCurrentCount > 0;
    Out.bLow = Survivor->bIsCrouched || Survivor->IsProne();
    return true;
}

void UEWArrivalComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    FEWArrivalSnapshot Now;
    if (!ReadSnapshot(Now)) return;
    const double Time = GetWorld()->GetTimeSeconds();
    if (IsComplete()) { TickTown(Time); return; }
    if (Time < ShowAt) return;
    if (Tracker.Step != GetStep())
    {
        Tracker.Begin(GetStep(), Now);
        return;
    }
    if (!Tracker.Update(Now)) return;
    // Told once a second at most until the server's answer arrives (it may be on its way).
    if (SentFor == Step && Time - SentAt < 1.) return;
    SentFor = Step;
    SentAt = Time;
    ServerCompleteStep(Step);
}

bool UEWArrivalComponent::IsPromptDue() const
{
    return !IsComplete() && GetWorld() && GetWorld()->GetTimeSeconds() >= ShowAt && Tracker.Step == GetStep();
}

void UEWArrivalComponent::ServerCompleteStep_Implementation(int32 Completed)
{
    if (Completed == Step && Step < int32(EEWArrivalStep::Interact)) Advance();
}

void UEWArrivalComponent::NoteInteracted()
{
    if (GetOwner() && GetOwner()->HasAuthority() && GetStep() == EEWArrivalStep::Interact) Advance();
}

void UEWArrivalComponent::SetStepIndex(int32 NewStep)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    Step = FMath::Clamp(NewStep, 0, StepCount);
    GetOwner()->ForceNetUpdate();
    OnRep_Step();
}

void UEWArrivalComponent::Advance()
{
    Step = FMath::Min(Step + 1, StepCount);
    GetOwner()->ForceNetUpdate();
    OnRep_Step();   // the host's own survivor has no replication to wait for
}

void UEWArrivalComponent::OnRep_Step()
{
    if (GetWorld()) ShowAt = FMath::Max(ShowAt, GetWorld()->GetTimeSeconds() + StepGap);
    Tracker.Step = EEWArrivalStep::Done;
}

// ---- Saltreach (slice 5) ----------------------------------------------------------------------------------------------

EEWTownStep UEWArrivalComponent::GetTownStep() const
{
    for (int32 Index = 0; Index < TownStepCount; ++Index)
        if (!(TownDone & (1 << Index))) return EEWTownStep(Index);
    return EEWTownStep::Done;
}

bool UEWArrivalComponent::IsInTown() const
{
    return GetOwner() && AEWSafeZone::FindAt(GetOwner(), GetOwner()->GetActorLocation()) != nullptr;
}

FEWVoyageProvisions FEWVoyageProvisions::Count(const UEWInventoryComponent* Hold)
{
    FEWVoyageProvisions Out;
    if (!Hold) return Out;
    for (const FEWInventoryEntry& Entry : Hold->GetInventoryEntries())
    {
        const UEWItemDefinition* Item = Entry.ItemDefinition;
        if (!Item || Entry.Quantity <= 0) continue;
        if (Item->bFoodConsumptionEnabled && Item->FoodKind != EEWFoodKind::None && Item->FoodKind != EEWFoodKind::Remedy && Item->HungerRestoreFraction > 0.f)
            Out.Food += Entry.Quantity;
        if (!Item->EmptiedVersion.IsNull()) Out.Water += Entry.Quantity;     // a full skin: drinking empties it
        Out.Patch += Item->PatchValue * Entry.Quantity;
    }
    return Out;
}

bool UEWArrivalComponent::IsAtDestination(const FVector& Location) const
{
    return GetWorld() && AEWClimateRegion::SampleClimate(GetWorld(), Location).Region == VoyageRegion;
}

void UEWArrivalComponent::NoteHoldLoaded(const AEWShip* Ship)
{
    const auto* Survivor = Cast<AEWCharacter>(GetOwner());
    if (!Survivor || !Survivor->HasAuthority() || !IsValid(Ship) || IsTownStepDone(EEWTownStep::Provision)) return;
    // Her own boat: owned, and this survivor one of her shipmates (not someone else's, nor the yard's).
    if (!Ship->IsOwned() || Ship->bHeldByYard || !Ship->IsShipmate(Survivor)) return;
    if (FEWVoyageProvisions::Count(Ship->GetCargo()).IsReady()) NoteTownStep(EEWTownStep::Provision);
}

void UEWArrivalComponent::TickTown(double Time)
{
    if (IsTownComplete()) return;
    // Arriving: the owning machine sees it and says so; the server checks where it has the survivor.
    if (!IsTownStepDone(EEWTownStep::Voyage) && Time - TownSentAt >= 1. && GetOwner() && IsAtDestination(GetOwner()->GetActorLocation()))
    {
        TownSentAt = Time;
        ServerCompleteTownStep(int32(EEWTownStep::Voyage));
    }
    // Entering the town gives the first view a moment without a prompt, as arriving does.
    const bool bInTown = IsInTown();
    if (bInTown && !bWasInTown) TownShowAt = FMath::Max(TownShowAt, Time + FirstPromptDelay);
    bWasInTown = bInTown;
    // The Company page is a menu: the owning machine sees it open and says so (once a second at most until the answer comes).
    if (IsTownStepDone(EEWTownStep::Company) || Time - TownSentAt < 1.) return;
    const auto* Survivor = Cast<AEWCharacter>(GetOwner());
    const auto* PC = Survivor ? Cast<AEWPlayerController>(Survivor->GetController()) : nullptr;
    const UEWInventoryWidget* Menu = PC ? PC->GetInventoryWidget() : nullptr;
    if (PC && PC->IsInventoryOpen() && Menu && Menu->IsInViewport() && Menu->GetSelectedSection() == UEWInventoryWidget::CompanySection)
    {
        TownSentAt = Time;
        ServerCompleteTownStep(int32(EEWTownStep::Company));
    }
}

bool UEWArrivalComponent::IsTownPromptDue() const
{
    // The town's steps show in the town; the voyage's wherever the survivor is (at sea, most of all).
    return IsComplete() && !IsTownComplete() && (bWasInTown || GetTownStep() == EEWTownStep::Voyage)
        && GetWorld() && GetWorld()->GetTimeSeconds() >= TownShowAt;
}

bool UEWArrivalComponent::GetTownTarget(FVector& OutLocation) const
{
    if (!IsTownPromptDue() || !GetOwner()) return false;
    const FVector From = GetOwner()->GetActorLocation();
    const AActor* Best = nullptr;
    auto Consider = [&](const AActor* Candidate)
    {
        if (IsValid(Candidate) && (!Best || FVector::DistSquared(From, Candidate->GetActorLocation()) < FVector::DistSquared(From, Best->GetActorLocation())))
            Best = Candidate;
    };
    switch (GetTownStep())
    {
    case EEWTownStep::Sell:
        // The market's traders: the recruiter buys too, but the prompt sends the survivor to the stalls.
        for (TActorIterator<AEWMerchant> It(GetWorld()); It; ++It) if (It->bBuysPack && !It->IsA<AEWCrewMaster>()) Consider(*It);
        break;
    case EEWTownStep::Store: for (TActorIterator<AEWStrongbox> It(GetWorld()); It; ++It) Consider(*It); break;
    case EEWTownStep::Shipyard: case EEWTownStep::Boat:
        for (TActorIterator<AEWShipwright> It(GetWorld()); It; ++It) Consider(*It);
        break;
    case EEWTownStep::Provision:
    {
        // Her own boat (the nearest, if more than one).
        const auto* Survivor = Cast<AEWCharacter>(GetOwner());
        for (TActorIterator<AEWShip> It(GetWorld()); It; ++It)
            if (It->IsOwned() && !It->bHeldByYard && It->IsShipmate(Survivor)) Consider(*It);
        break;
    }
    case EEWTownStep::Voyage:
        for (TActorIterator<AEWClimateRegion> It(GetWorld()); It; ++It) if (It->Region == VoyageRegion) Consider(*It);
        break;
    default: break;   // the Company page is in the menu, not a place
    }
    if (!Best) return false;
    OutLocation = Best->GetActorLocation();
    return true;
}

void UEWArrivalComponent::SetTownStepsDone(int32 Mask)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) return;
    TownDone = Mask & AllTownSteps;
    GetOwner()->ForceNetUpdate();
    OnRep_TownDone();
}

void UEWArrivalComponent::NoteTownStep(EEWTownStep Done)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || Done >= EEWTownStep::Done || IsTownStepDone(Done)) return;
    SetTownStepsDone(TownDone | (1 << int32(Done)));
}

void UEWArrivalComponent::ServerCompleteTownStep_Implementation(int32 Completed)
{
    if (Completed == int32(EEWTownStep::Company)) NoteTownStep(EEWTownStep::Company);
    else if (Completed == int32(EEWTownStep::Voyage) && GetOwner() && IsAtDestination(GetOwner()->GetActorLocation())) NoteTownStep(EEWTownStep::Voyage);
}

void UEWArrivalComponent::OnRep_TownDone()
{
    if (GetWorld()) TownShowAt = FMath::Max(TownShowAt, GetWorld()->GetTimeSeconds() + StepGap);
}

FText UEWArrivalComponent::TownPromptFor(EEWTownStep Step, bool bController)
{
    switch (Step)
    {
    case EEWTownStep::Sell: return bController ? NSLOCTEXT("Elitewake", "TownSellPad", "Your purse is empty. X: sell what you gathered to a trader at the market")
                                                : NSLOCTEXT("Elitewake", "TownSellKeys", "Your purse is empty. E: sell what you gathered to a trader at the market");
    case EEWTownStep::Store: return bController ? NSLOCTEXT("Elitewake", "TownStorePad", "X: keep what you will not carry in your strongbox by the warehouse")
                                                 : NSLOCTEXT("Elitewake", "TownStoreKeys", "E: keep what you will not carry in your strongbox by the warehouse");
    case EEWTownStep::Shipyard: return bController ? NSLOCTEXT("Elitewake", "TownYardPad", "Ships are sold and mended at the shipyard. X: talk to Elias Thorne")
                                                    : NSLOCTEXT("Elitewake", "TownYardKeys", "Ships are sold and mended at the shipyard. E: talk to Elias Thorne");
    case EEWTownStep::Company: return bController ? NSLOCTEXT("Elitewake", "TownCompanyPad", "To sail with friends, form a Company. Y, then RB twice: Company")
                                                   : NSLOCTEXT("Elitewake", "TownCompanyKeys", "To sail with friends, form a Company. I, then Tab twice: Company");
    case EEWTownStep::Boat: return bController ? NSLOCTEXT("Elitewake", "TownBoatPad", "X: buy your first boat, a raft, from Elias Thorne at the shipyard")
                                                : NSLOCTEXT("Elitewake", "TownBoatKeys", "E: buy your first boat, a raft, from Elias Thorne at the shipyard");
    case EEWTownStep::Provision: return bController ? NSLOCTEXT("Elitewake", "TownProvisionPad", "X at her hold: load 2 food, a full waterskin and 20 wood")
                                                     : NSLOCTEXT("Elitewake", "TownProvisionKeys", "E at her hold: load 2 food, a full waterskin and 20 wood");
    case EEWTownStep::Voyage: return NSLOCTEXT("Elitewake", "TownVoyage", "First voyage: sail to the Swamp island. Follow the compass");
    default: return FText::GetEmpty();
    }
}

FText UEWArrivalComponent::PromptFor(EEWArrivalStep Step, bool bController)
{
    switch (Step)
    {
    case EEWArrivalStep::Look: return bController ? NSLOCTEXT("Elitewake", "ArrivalLookPad", "Right stick: look around")
                                                   : NSLOCTEXT("Elitewake", "ArrivalLookKeys", "Mouse: look around");
    case EEWArrivalStep::Move: return bController ? NSLOCTEXT("Elitewake", "ArrivalMovePad", "Left stick: walk")
                                                   : NSLOCTEXT("Elitewake", "ArrivalMoveKeys", "W A S D: walk");
    case EEWArrivalStep::Jump: return bController ? NSLOCTEXT("Elitewake", "ArrivalJumpPad", "A: jump")
                                                   : NSLOCTEXT("Elitewake", "ArrivalJumpKeys", "Space: jump");
    case EEWArrivalStep::Crouch: return bController ? NSLOCTEXT("Elitewake", "ArrivalCrouchPad", "B: crouch (hold to lie flat)")
                                                     : NSLOCTEXT("Elitewake", "ArrivalCrouchKeys", "C: crouch (hold to lie flat)");
    case EEWArrivalStep::Interact: return bController ? NSLOCTEXT("Elitewake", "ArrivalUsePad", "X: drink at the spring ahead, or use what you face")
                                                       : NSLOCTEXT("Elitewake", "ArrivalUseKeys", "E: drink at the spring ahead, or use what you face");
    default: return FText::GetEmpty();
    }
}
