#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameFramework/Actor.h"
#include "EWCompanyComponent.generated.h"

UENUM(BlueprintType)
enum class EEWCompanyOwnership : uint8 { Personal, PersonalShared, Company };
UENUM(BlueprintType)
enum class EEWCompanyAction : uint8 { Create, Rename, Invite, AcceptInvite, DeclineInvite, Promote, Demote, Remove, TransferOwner, Leave };
USTRUCT(BlueprintType)
struct FEWCompanyMember
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) int32 PlayerId = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly) FString Name;
    UPROPERTY(BlueprintReadOnly) bool bManager = false;
    UPROPERTY(BlueprintReadOnly) bool bOnline = false;
};
USTRUCT(BlueprintType)
struct FEWCompanySnapshot
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly) FGuid Id;
    UPROPERTY(BlueprintReadOnly) FString Name;
    UPROPERTY(BlueprintReadOnly) int32 OwnerId = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly) TArray<FEWCompanyMember> Members;
    UPROPERTY(BlueprintReadOnly) EEWCompanyOwnership Ships = EEWCompanyOwnership::Personal;
    UPROPERTY(BlueprintReadOnly) EEWCompanyOwnership Structures = EEWCompanyOwnership::Personal;
    UPROPERTY(BlueprintReadOnly) EEWCompanyOwnership Tames = EEWCompanyOwnership::Personal;
};

/** Session-only authoritative membership; snapshots and invitations go only to the owning player.
 * Asset ownership/persistence/taming are separate integrations, not implied by policy selection. */
UCLASS(ClassGroup=(Elitewake), meta=(BlueprintSpawnableComponent))
class EW_API UEWCompanyComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UEWCompanyComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
    UFUNCTION(BlueprintPure) FEWCompanySnapshot GetCompany() const { return Snapshot; }
    UFUNCTION(BlueprintPure) FString GetInvitationName() const { return InvitationName; }
    UFUNCTION(BlueprintPure) FString GetLastResult() const { return LastResult; }
    UFUNCTION(BlueprintPure) TArray<FEWCompanyMember> GetOnlinePlayers() const { return OnlinePlayers; }
    UFUNCTION(Server, Reliable) void ServerCommand(EEWCompanyAction Action, const FString& Text, int32 TargetPlayerId);
    UFUNCTION(Server, Reliable) void ServerSetPolicy(int32 AssetKind, EEWCompanyOwnership Policy);
    static bool IsValidCompanyName(const FString& Name);
    /** Trusted future tame integration must supply authoritative counts including personal tames. */
    static bool FitsTameCaps(int32 PlayerCount, int32 CompanyCount, int32 Additional);
private:
    friend class AEWCompanyRegistry;
    UPROPERTY(Replicated) FEWCompanySnapshot Snapshot;
    UPROPERTY(Replicated) FString InvitationName;
    UPROPERTY(Replicated) FString LastResult;
    UPROPERTY(Replicated) TArray<FEWCompanyMember> OnlinePlayers;
    FGuid PendingInvitation;
    double LastRequest = -100;
    bool BeginRequest();
};

/** Server-only world lifetime registry. No process-global records or client-owned membership writes. */
UCLASS(NotBlueprintable)
class EW_API AEWCompanyRegistry : public AActor
{
    GENERATED_BODY()
public:
    AEWCompanyRegistry();
    virtual void Tick(float DeltaSeconds) override;
    static AEWCompanyRegistry* Resolve(UWorld* World);
    void Command(UEWCompanyComponent* Requester, EEWCompanyAction Action, const FString& Text, int32 Target);
    void SetPolicy(UEWCompanyComponent* Requester, int32 Kind, EEWCompanyOwnership Policy);
private:
    UPROPERTY() TArray<FEWCompanySnapshot> Companies;
    void Refresh();
};
