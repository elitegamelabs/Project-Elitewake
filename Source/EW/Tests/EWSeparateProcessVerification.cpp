// Opt-in editor-build game-mode harness. No packaged game grant or request surface.
#if WITH_EDITOR
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "EWInventoryComponent.h"
#include "EWCraftingRecipe.h"
#include "EWPickup.h"
#include "Containers/Ticker.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "GameFramework/CharacterMovementComponent.h"

namespace EWSeparateTest
{
static FTSTicker::FDelegateHandle Handle;
static bool bHost = false;
static int32 Phase = 0;
static double Start = 0., Changed = 0.;
static FVector LocalStart, OtherStart;
static TWeakObjectPtr<AEWPickup> Pickup;
static TArray<FString> Checks;
static FString Path(const TCHAR* Name) { return FPaths::ProjectSavedDir()/TEXT("SeparateGameplay")/Name; }
static void Write(const TCHAR* Name, const FString& Value) { FFileHelper::SaveStringToFile(Value,*Path(Name)); }
static bool Exists(const TCHAR* Name) { return IFileManager::Get().FileExists(*Path(Name)); }
static bool Finish(bool bSuccess, const FString& Error = FString())
{
    Write(bHost ? TEXT("HostResult.txt") : TEXT("ClientResult.txt"),
        (bSuccess ? TEXT("PASS\n") : TEXT("FAIL\n")) + FString::Join(Checks,TEXT("\n")) + TEXT("\n") + Error);
    return false;
}
static bool Tick(float Delta)
{
    const double Now = FPlatformTime::Seconds();
    if (Now-Start>90.) return Finish(false,FString::Printf(TEXT("Timed out waiting for gameplay checkpoint, phase %d."),Phase));
    UWorld* World=nullptr;
    if (GEngine) for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType==EWorldType::Game && Context.World()) { World=Context.World(); break; }
    if (!World || (bHost ? World->GetNetMode()!=NM_ListenServer : World->GetNetMode()!=NM_Client)) return true;
    AEWPlayerController* Local=nullptr;
    AEWCharacter* Other=nullptr;
    for (TActorIterator<AEWPlayerController> It(World);It;++It)
        if (It->IsLocalPlayerController()) { Local=*It; break; }
    auto* Own = Local ? Cast<AEWCharacter>(Local->GetPawn()) : nullptr;
    if (!Own) return true;
    for (TActorIterator<AEWCharacter> It(World);It;++It) if (*It!=Own) { Other=*It; break; }
    if (!Other || World->GetTimeSeconds()<3.f) return true;
    auto* Recipe=LoadObject<UEWCraftingRecipe>(nullptr,TEXT("/Game/Elitewake/Crafting/Testing/DA_RecipeWoodenAxe.DA_RecipeWoodenAxe"));
    if (!Recipe || Recipe->Ingredients.Num()!=1 || Recipe->Ingredients[0].Quantity!=20 || !Recipe->Output)
        return Finish(false,TEXT("Approved opt-in recipe fixture is missing or has unexpected cost."));
    auto* Wood=Recipe->Ingredients[0].Item.Get();
    auto* Inventory=Own->GetInventoryComponent();
    auto* OtherInventory=Other->GetInventoryComponent();
    if (bHost)
    {
        if (!Other->GetController()) return true;
        if (Phase==0)
        {
            if (Inventory->GetUsedSlotCount() || OtherInventory->GetUsedSlotCount()
                || Inventory->GetAvailableRecipes().Num() || OtherInventory->GetAvailableRecipes().Num())
                return Finish(false,TEXT("Normal starts must be empty."));
            if (Inventory->AddItem(Wood,3)!=3 || OtherInventory->AddItem(Wood,20)!=20 || !OtherInventory->UnlockRecipe(Recipe))
                return Finish(false,TEXT("Authority fixture setup failed."));
            for (TActorIterator<AEWPickup> It(World);It;++It) It->Destroy(); // Remove saved opt-in fixture only in this disposable test world.
            LocalStart=Own->GetActorLocation(); OtherStart=Other->GetActorLocation();
            Checks.Add(TEXT("Normal players start empty; only explicit authority fixture grants ingredients/unlock"));
            Write(TEXT("Host1"),TEXT("ready")); Phase=1;
        }
        else if (Phase==1 && Exists(TEXT("Client1")))
        {
            if (!Changed) Changed=Now;
            Own->AddMovementInput(FVector(0,1,0),1.f);
            if (Now-Changed>2.) { Write(TEXT("Host2"),TEXT("moved")); Phase=2; Changed=0.; }
        }
        else if (Phase==2 && Exists(TEXT("Client2")))
        {
            if (OtherInventory->GetItemCount(Recipe->Output)!=1 || OtherInventory->GetItemCount(Wood)!=0) return true;
            if (Inventory->GetItemCount(Wood)!=3 || Inventory->GetItemCount(Recipe->Output)!=0
                || FVector::Dist(OtherStart,Other->GetActorLocation())<30.f || FVector::Dist(LocalStart,Own->GetActorLocation())<30.f)
                return Finish(false,TEXT("Owned craft/movement isolation failed."));
            Checks.Add(TEXT("Client movement reaches server; owned craft consumes exactly 20 Wood without changing host inventory"));
            Own->TeleportTo(FVector(0,-45,92),FRotator::ZeroRotator,false,true);
            Other->TeleportTo(FVector(0,45,92),FRotator::ZeroRotator,false,true);
            Own->GetCharacterMovement()->StopMovementImmediately(); Other->GetCharacterMovement()->StopMovementImmediately();
            Local->SetControlRotation(FRotator::ZeroRotator);
            Other->GetController()->SetControlRotation(FRotator::ZeroRotator);
            FActorSpawnParameters Params; Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            auto* Stack=World->SpawnActor<AEWPickup>(FVector(150,0,156),FRotator::ZeroRotator,Params);
            if (!Stack) return Finish(false,TEXT("Pickup spawn failed."));
            Stack->ItemDefinition=Wood; Stack->Quantity=10; Stack->SetActorScale3D(FVector(1,5,2)); Stack->ForceNetUpdate(); Pickup=Stack;
            Write(TEXT("Host3"),TEXT("pickup")); Phase=3;
        }
        else if (Phase==3 && Exists(TEXT("Client3")))
        {
            Local->ServerInteract(Pickup.Get()); Changed=Now; Phase=4;
        }
        else if (Phase==4 && Now-Changed>1.)
        {
            const int32 A=Inventory->GetItemCount(Wood), B=OtherInventory->GetItemCount(Wood);
            if (A+B!=13 || !((A==13 && B==0)||(A==3 && B==10)) || Pickup.IsValid())
                return Finish(false,TEXT("Competing pickup did not conserve the ten-unit world stack."));
            Checks.Add(TEXT("Competing host/client interaction requests collect ten world units exactly once"));
            Write(TEXT("Host4"),FString::Printf(TEXT("%d"),B)); Phase=5; Changed=0.;
        }
        else if (Phase==5 && Exists(TEXT("Client4")))
        {
            if (!Changed) Changed=Now;
            if (Now-Changed<1.) return true;
            if (OtherInventory->GetItemCount(Recipe->Output)!=1 || Inventory->GetItemCount(Recipe->Output)!=0
                || Inventory->GetItemCount(Wood)+OtherInventory->GetItemCount(Wood)!=13)
                return Finish(false,TEXT("Unaffordable/repeated request changed conserved resources."));
            Checks.Add(TEXT("Insufficient-material craft and invalid repeat interaction leave resources unchanged"));
            Write(TEXT("Host5"),TEXT("done")); return Finish(true);
        }
    }
    else
    {
        if (Phase==0 && Exists(TEXT("Host1")))
        {
            if (Inventory->GetItemCount(Wood)!=20 || Inventory->GetAvailableRecipes().Num()!=1) return true;
            if (Inventory->AddItem(Wood,100)!=0 || Inventory->UnlockRecipe(Recipe)
                || OtherInventory->AddItem(Wood,100)!=0 || OtherInventory->GetAvailableRecipes().Num())
                return Finish(false,TEXT("Client mutation or non-owner recipe visibility failed."));
            Checks.Add(TEXT("Owned ingredients/recipe resolve across processes; client grants rejected and peer recipes hidden"));
            // Existing inventory entry replication is public. Record this separately from mutation ownership.
            Checks.Add(FString::Printf(TEXT("Peer inventory visibility observed: %d Wood (not a privacy certification)"),OtherInventory->GetItemCount(Wood)));
            LocalStart=Own->GetActorLocation(); OtherStart=Other->GetActorLocation();
            Write(TEXT("Client1"),TEXT("ready")); Phase=1;
        }
        else if (Phase==1)
        {
            Own->AddMovementInput(FVector(0,-1,0),1.f);
            if (!Exists(TEXT("Host2"))) return true;
            if (FVector::Dist(LocalStart,Own->GetActorLocation())<30.f || FVector::Dist(OtherStart,Other->GetActorLocation())<30.f) return true;
            Checks.Add(TEXT("Own movement and host movement are visible in the separate client process"));
            Local->RequestCraft(Recipe); Write(TEXT("Client2"),TEXT("craft")); Phase=2;
        }
        else if (Phase==2 && Exists(TEXT("Host3")))
        {
            if (Inventory->GetItemCount(Wood)!=0 || Inventory->GetItemCount(Recipe->Output)!=1 || FMath::Abs(Own->GetActorLocation().X)>20.f) return true;
            AEWPickup* Stack=nullptr;
            for (TActorIterator<AEWPickup> It(World);It;++It) if (It->ItemDefinition==Wood && It->Quantity==10) { Stack=*It; break; }
            if (!Stack) return true;
            Local->SetControlRotation(FRotator::ZeroRotator);
            if (AEWPickup::FindTarget(Own)!=Stack) return true;
            Local->ServerInteract(Stack); Write(TEXT("Client3"),TEXT("compete")); Phase=3;
        }
        else if (Phase==3 && Exists(TEXT("Host4")))
        {
            FString Expected; FFileHelper::LoadFileToString(Expected,*Path(TEXT("Host4")));
            if (Inventory->GetItemCount(Wood)!=FCString::Atoi(*Expected)) return true;
            for (TActorIterator<AEWPickup> It(World);It;++It) if (It->ItemDefinition==Wood) return true;
            Checks.Add(TEXT("Winning transfer and world-stack destruction replicate to client without duplication"));
            Local->RequestCraft(Recipe); Local->ServerInteract(nullptr); Write(TEXT("Client4"),TEXT("reject")); Phase=4;
        }
        else if (Phase==4 && Exists(TEXT("Host5")))
        {
            if (Inventory->GetItemCount(Recipe->Output)!=1) return Finish(false,TEXT("Client crafted output unexpectedly changed."));
            Checks.Add(TEXT("Rejected follow-up requests preserve crafted output")); return Finish(true);
        }
    }
    return true;
}
}
void StartEWSeparateProcessVerification()
{
    FString Role;
    if (!FParse::Value(FCommandLine::Get(),TEXT("EWVerifyRole="),Role) || (Role!=TEXT("Host") && Role!=TEXT("Client"))) return;
    EWSeparateTest::bHost=Role==TEXT("Host"); EWSeparateTest::Start=FPlatformTime::Seconds();
    IFileManager::Get().MakeDirectory(*EWSeparateTest::Path(TEXT("")),true);
    EWSeparateTest::Handle=FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&EWSeparateTest::Tick));
}
void StopEWSeparateProcessVerification()
{
    if (EWSeparateTest::Handle.IsValid()) FTSTicker::GetCoreTicker().RemoveTicker(EWSeparateTest::Handle);
}
#endif
