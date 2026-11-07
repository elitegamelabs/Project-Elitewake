#include "EWCompanyComponent.h"
#include "EWPlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"

namespace
{
int32 PlayerId(const UEWCompanyComponent* C)
{
    const auto* PC = C ? Cast<APlayerController>(C->GetOwner()) : nullptr;
    return PC && PC->PlayerState ? PC->PlayerState->GetPlayerId() : INDEX_NONE;
}
UEWCompanyComponent* FindPlayer(UWorld* W, int32 Id)
{
    for (auto It=W->GetPlayerControllerIterator(); It; ++It)
        if (auto* PC=Cast<AEWPlayerController>(It->Get()); PC && PC->PlayerState && PC->PlayerState->GetPlayerId()==Id)
            return PC->GetCompanyComponent();
    return nullptr;
}
FEWCompanyMember Member(UEWCompanyComponent* C)
{
    FEWCompanyMember M; M.PlayerId=PlayerId(C); M.bOnline=true;
    M.Name=Cast<APlayerController>(C->GetOwner())->PlayerState->GetPlayerName(); return M;
}
}
UEWCompanyComponent::UEWCompanyComponent() { SetIsReplicatedByDefault(true); }
void UEWCompanyComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(UEWCompanyComponent,Snapshot,COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWCompanyComponent,InvitationName,COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWCompanyComponent,LastResult,COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(UEWCompanyComponent,OnlinePlayers,COND_OwnerOnly);
}
bool UEWCompanyComponent::IsValidCompanyName(const FString& Name)
{
    if (Name.Len()<3 || Name.Len()>32 || Name!=Name.TrimStartAndEnd()) return false;
    for (TCHAR C:Name) if (!FChar::IsAlnum(C) && C!=' ' && C!='-' && C!='\'') return false;
    return true;
}
bool UEWCompanyComponent::FitsTameCaps(int32 PlayerCount,int32 CompanyCount,int32 Additional)
{
    return PlayerCount>=0 && CompanyCount>=0 && Additional>0 && PlayerCount<=25 && CompanyCount<=75
        && Additional<=25-PlayerCount && Additional<=75-CompanyCount;
}
bool UEWCompanyComponent::BeginRequest()
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || PlayerId(this)==INDEX_NONE || !GetWorld()) return false;
    const double Now=GetWorld()->GetTimeSeconds();
    if (Now-LastRequest<.2) return false;
    LastRequest=Now; return true;
}
void UEWCompanyComponent::ServerCommand_Implementation(EEWCompanyAction Action,const FString& Text,int32 TargetPlayerId)
{
    if (!BeginRequest()) return;
    if (auto* R=AEWCompanyRegistry::Resolve(GetWorld())) R->Command(this,Action,Text,TargetPlayerId);
}
void UEWCompanyComponent::ServerSetPolicy_Implementation(int32 Kind,EEWCompanyOwnership Policy)
{
    if (!BeginRequest()) return;
    if (auto* R=AEWCompanyRegistry::Resolve(GetWorld())) R->SetPolicy(this,Kind,Policy);
}
AEWCompanyRegistry::AEWCompanyRegistry()
{
    bReplicates=false; PrimaryActorTick.bCanEverTick=true; PrimaryActorTick.TickInterval=1.f;
}
AEWCompanyRegistry* AEWCompanyRegistry::Resolve(UWorld* W)
{
    if (!W || W->GetNetMode()==NM_Client) return nullptr;
    for (TActorIterator<AEWCompanyRegistry> It(W); It; ++It) return *It;
    return W->SpawnActor<AEWCompanyRegistry>();
}
void AEWCompanyRegistry::Tick(float DeltaSeconds) { Super::Tick(DeltaSeconds); Refresh(); }
void AEWCompanyRegistry::Refresh()
{
    for (auto& Co:Companies) for (auto& M:Co.Members)
    {
        auto* C=FindPlayer(GetWorld(),M.PlayerId); M.bOnline=C!=nullptr;
        if (C) M.Name=Member(C).Name;
    }
    for (auto It=GetWorld()->GetPlayerControllerIterator(); It; ++It)
        if (auto* PC=Cast<AEWPlayerController>(It->Get()))
        {
            auto* C=PC->GetCompanyComponent(); if (!C) continue;
            const int32 Id=PlayerId(C);
            C->OnlinePlayers.Reset();
            for (auto Players=GetWorld()->GetPlayerControllerIterator(); Players; ++Players)
                if (auto* P=Cast<AEWPlayerController>(Players->Get()); P && P->PlayerState && P!=PC)
                    C->OnlinePlayers.Add(Member(P->GetCompanyComponent()));
            auto* Co=Companies.FindByPredicate([Id](const auto& R){return R.Members.ContainsByPredicate([Id](const auto& M){return M.PlayerId==Id;});});
            C->Snapshot=Co ? *Co : FEWCompanySnapshot();
            const auto* Inv=Companies.FindByPredicate([C](const auto& R){return R.Id==C->PendingInvitation;});
            C->InvitationName=Inv ? Inv->Name : FString();
            if (!Inv) C->PendingInvitation.Invalidate();
        }
}
void AEWCompanyRegistry::Command(UEWCompanyComponent* C,EEWCompanyAction Action,const FString& Text,int32 Target)
{
    if (!HasAuthority() || !C || C->GetWorld()!=GetWorld()) return;
    const int32 Id=PlayerId(C);
    auto* Co=Companies.FindByPredicate([Id](const auto& R){return R.Members.ContainsByPredicate([Id](const auto& M){return M.PlayerId==Id;});});
    C->LastResult=TEXT("Action rejected.");
    if (Action==EEWCompanyAction::Create)
    {
        if (Co || !UEWCompanyComponent::IsValidCompanyName(Text) || Companies.ContainsByPredicate([&Text](const auto& R){return R.Name.Equals(Text,ESearchCase::IgnoreCase);}))
        { C->LastResult=TEXT("Choose an unused name of 3–32 letters, numbers, spaces, apostrophes or hyphens. Leave your Company before creating another."); return; }
        FEWCompanySnapshot New; New.Id=FGuid::NewGuid(); New.Name=Text; New.OwnerId=Id; New.Members.Add(Member(C)); Companies.Add(New);
        C->PendingInvitation.Invalidate(); C->LastResult=TEXT("Company created."); Refresh(); return;
    }
    if (Action==EEWCompanyAction::DeclineInvite) { C->PendingInvitation.Invalidate(); C->LastResult=TEXT("Invitation declined."); Refresh(); return; }
    if (Action==EEWCompanyAction::AcceptInvite)
    {
        auto* Inv=Companies.FindByPredicate([C](const auto& R){return R.Id==C->PendingInvitation;});
        if (Co || !Inv) return;
        // Tame membership accounting must be integrated before persistent tames become available.
        Inv->Members.Add(Member(C)); C->PendingInvitation.Invalidate(); C->LastResult=TEXT("Joined Company."); Refresh(); return;
    }
    if (!Co) return;
    auto* Self=Co->Members.FindByPredicate([Id](const auto& M){return M.PlayerId==Id;});
    auto* Other=Co->Members.FindByPredicate([Target](const auto& M){return M.PlayerId==Target;});
    const bool bIsOwner=Co->OwnerId==Id;
    switch (Action)
    {
    case EEWCompanyAction::Rename:
        if (!bIsOwner || !UEWCompanyComponent::IsValidCompanyName(Text) || Companies.ContainsByPredicate([&](const auto& R){return R.Id!=Co->Id && R.Name.Equals(Text,ESearchCase::IgnoreCase);})) return;
        Co->Name=Text; C->LastResult=TEXT("Company renamed."); break;
    case EEWCompanyAction::Invite:
    {
        if (!bIsOwner && !Self->bManager) return;
        auto* Recipient=FindPlayer(GetWorld(),Target);
        if (!Recipient || Recipient==C || Companies.ContainsByPredicate([Target](const auto& R){return R.Members.ContainsByPredicate([Target](const auto& M){return M.PlayerId==Target;});})) return;
        Recipient->PendingInvitation=Co->Id; C->LastResult=TEXT("Invitation sent."); break;
    }
    case EEWCompanyAction::Promote:
    case EEWCompanyAction::Demote:
        if (!bIsOwner || !Other || Target==Co->OwnerId) return;
        Other->bManager=Action==EEWCompanyAction::Promote; C->LastResult=TEXT("Member role updated."); break;
    case EEWCompanyAction::Remove:
        if (!Other || Target==Id || Target==Co->OwnerId || (!bIsOwner && (!Self->bManager || Other->bManager))) return;
        Co->Members.RemoveAll([Target](const auto& M){return M.PlayerId==Target;}); C->LastResult=TEXT("Member removed."); break;
    case EEWCompanyAction::TransferOwner:
        if (!bIsOwner || !Other || Target==Id || !Other->bOnline) return;
        Co->OwnerId=Target; Other->bManager=false; Self->bManager=false; C->LastResult=TEXT("Company ownership transferred."); break;
    case EEWCompanyAction::Leave:
        if (bIsOwner && Co->Members.Num()>1) { C->LastResult=TEXT("Transfer ownership before leaving."); return; }
        Co->Members.RemoveAll([Id](const auto& M){return M.PlayerId==Id;});
        if (Co->Members.IsEmpty()) { const FGuid Removed=Co->Id; Companies.RemoveAll([Removed](const auto& R){return R.Id==Removed;}); }
        C->LastResult=TEXT("Left Company."); break;
    default: return;
    }
    Refresh();
}
void AEWCompanyRegistry::SetPolicy(UEWCompanyComponent* C,int32 Kind,EEWCompanyOwnership Policy)
{
    if (!HasAuthority() || !C || C->GetWorld()!=GetWorld()) return;
    auto* Co=Companies.FindByPredicate([C](const auto& R){return R.OwnerId==PlayerId(C);});
    C->LastResult=TEXT("Only the Company owner can change ownership policies.");
    if (!Co || Kind<0 || Kind>2 || static_cast<uint8>(Policy)>2) return;
    if (Kind==0) Co->Ships=Policy; else if (Kind==1) Co->Structures=Policy; else Co->Tames=Policy;
    C->LastResult=Kind==0 ? TEXT("Ship policy changed: it decides who may sail members' ships.") : TEXT("Policy saved for this session."); Refresh();
}

