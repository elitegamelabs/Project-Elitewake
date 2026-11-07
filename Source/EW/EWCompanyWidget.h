#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWCompanyWidget.generated.h"
class UBorder;
class UEditableTextBox;
class UScrollBox;
class UTextBlock;
class UVerticalBox;
class UWidget;
class UEWCompanyComponent;
class UEWRecipeButton;

/** The three Company ranks: the owner leads, managers are Officers, everyone else a Member. */
enum class EEWCompanyRank : uint8 { Member, Officer, Leader };

/** One row of the roster, as the server last sent it. */
struct FEWCompanyRow
{
    FString Name;
    int32 PlayerId = INDEX_NONE;
    EEWCompanyRank Rank = EEWCompanyRank::Member;
    bool bOnline = false;
    bool bYou = false;
};
struct FEWCompanyLogLine { FString Time; FString Glyph; FString Text; };

/**
 * The menu's Company section (layout: owner, October 25; live since October 30). It shows the player's real Company from the server:
 * members with search, the overview with the ship policy (who may sail the members' ships), the picked member's details and the
 * actions their rank allows (promote, demote, invite, remove, transfer leadership), this session's activity, invitations (accept or
 * decline one; invite online players) and what each rank may do. Without a Company it offers to create one and lists the incoming
 * invitation. Every action is a request to the server, which decides; destructive ones ask first. Mouse, keyboard and controller.
 */
UCLASS()
class EW_API UEWCompanyWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

    /** Keys the Inventory screen hands over while this section is open. Returns true when the key was used (Escape and B return false with no dialog open, so the menu can close). */
    bool HandleMenuKey(const FKey& Key);
    /** True while one of this screen's text boxes has the keyboard. */
    bool IsTyping() const;
    /** True when a screen position is over one of this screen's text boxes. */
    bool IsPointerOverTextBox(const FVector2D& ScreenPosition) const;

    UFUNCTION(BlueprintPure, Category="Company") bool IsInCompany() const;
    UFUNCTION(BlueprintPure, Category="Company") FString GetCompanyName() const;
    UFUNCTION(BlueprintPure, Category="Company") int32 GetMemberCount() const { return Members.Num(); }
    UFUNCTION(BlueprintPure, Category="Company") int32 GetShownMemberCount() const { return Shown.Num(); }
    UFUNCTION(BlueprintPure, Category="Company") int32 GetOnlineCount() const;
    /** The Company that invited this player, if any. */
    UFUNCTION(BlueprintPure, Category="Company") FString GetIncomingInvitation() const;
    UFUNCTION(BlueprintPure, Category="Company") int32 GetLogCount() const { return Log.Num(); }
    UFUNCTION(BlueprintPure, Category="Company") int32 GetSubTab() const { return SubTab; }
    UFUNCTION(BlueprintPure, Category="Company") bool IsConfirmOpen() const { return Confirming != INDEX_NONE; }
    UFUNCTION(BlueprintPure, Category="Company") FText GetSelectedName() const;
    UFUNCTION(BlueprintPure, Category="Company") FText GetSelectedRankText() const;
    /** 0 member, 1 officer, 2 leader; -1 with nobody picked. */
    UFUNCTION(BlueprintPure, Category="Company") int32 GetSelectedRank() const;
    /** This player's rank, as GetSelectedRank; -1 outside a Company. */
    UFUNCTION(BlueprintPure, Category="Company") int32 GetViewerRank() const;
    /** 0 Personal, 1 Personal Shared, 2 Company (the Company's ship policy). */
    UFUNCTION(BlueprintPure, Category="Company") int32 GetShipPolicy() const;
    /** The server's answer to this player's last request. */
    UFUNCTION(BlueprintPure, Category="Company") FString GetStatusText() const;
    UFUNCTION(BlueprintPure, Category="Company") bool IsActionEnabled(int32 Action) const;
    UFUNCTION(BlueprintCallable, Category="Company") void SetSearch(const FString& Text);
    UFUNCTION(BlueprintCallable, Category="Company") void SelectMemberByName(const FString& Name);
    UFUNCTION(BlueprintCallable, Category="Company") void SetSubTab(int32 Tab);
    /** 0 promote, 1 demote, 2 invite, 3 remove, 4 transfer leadership, 5 leave the Company. Remove, transfer and leave ask first. */
    UFUNCTION(BlueprintCallable, Category="Company") void DoAction(int32 Action);
    UFUNCTION(BlueprintCallable, Category="Company") void ConfirmDialog(bool bConfirm);
    UFUNCTION(BlueprintCallable, Category="Company") void CreateCompany(const FString& Name);
    /** Invites the online player of that name (case ignored). */
    UFUNCTION(BlueprintCallable, Category="Company") void InvitePlayer(const FString& Name);
    UFUNCTION(BlueprintCallable, Category="Company") void AnswerInvitation(bool bAccept);
    /** Leader only: Personal, then Personal Shared, then Company, then Personal again. */
    UFUNCTION(BlueprintCallable, Category="Company") void CycleShipPolicy();

private:
    UFUNCTION() void MemberPressed(int32 Index);
    UFUNCTION() void ActionPressed(int32 Action) { DoAction(Action); }
    UFUNCTION() void SubTabPressed(int32 Tab) { SetSubTab(Tab); }
    UFUNCTION() void InviteRowPressed(int32 Code);
    UFUNCTION() void DialogPressed(int32 Choice) { ConfirmDialog(Choice == 1); }
    UFUNCTION() void SearchChanged(const FText& Text) { SetSearch(Text.ToString()); }
    UFUNCTION() void InviteCommitted(const FText& Text, ETextCommit::Type Method);
    UFUNCTION() void InviteButtonPressed(int32 Index);
    UFUNCTION() void CreateCommitted(const FText& Text, ETextCommit::Type Method);
    UFUNCTION() void CreatePressed(int32 Index);
    UFUNCTION() void PolicyPressed(int32 Index) { CycleShipPolicy(); }
    UFUNCTION() void LeavePressed(int32 Index) { DoAction(5); }

    UEWCompanyComponent* GetCompany() const;
    /** Rebuilds the roster from the server's snapshot when it changed; logs joins, departures and answers. */
    void Sync(bool bForce = false);
    void RebuildList();
    void RefreshAll();
    void RefreshInvites();
    void RefreshLog();
    void RefreshRoles();
    void AddLog(const FString& Glyph, const FString& Text);
    void Send(uint8 Action, const FString& Text, int32 Target);
    const FEWCompanyRow* SelectedMember() const;
    const FEWCompanyRow* You() const;
    int32 IndexOfName(const FString& Name) const;
    static FString RankName(EEWCompanyRank Rank);
    static FString PolicyName(int32 Policy);
public:
    bool IsAtFirstMember() const { return Shown.IsEmpty() || Shown[0] == Selected; }
private:
    TArray<FEWCompanyRow> Members;
    TArray<FString> OnlineNames;     // other players here now, for invitations
    TArray<int32> OnlineIds;
    TArray<FEWCompanyLogLine> Log;
    TArray<int32> Shown;             // indices into Members that pass the search
    int32 Selected = 0;              // index into Members
    int32 SubTab = 0;
    int32 ActionCursor = 0;
    int32 Confirming = INDEX_NONE;   // the action waiting for a yes
    int32 PendingTarget = INDEX_NONE;
    int32 DialogChoice = 0;
    FString Filter;
    FString Signature;               // what the screen last showed, to rebuild only on change
    FString LastAnswer;
    float SyncIn = 0.f;

    UPROPERTY(Transient) TObjectPtr<UEditableTextBox> SearchBox;
    UPROPERTY(Transient) TObjectPtr<UEditableTextBox> InviteBox;
    UPROPERTY(Transient) TObjectPtr<UEditableTextBox> CreateBox;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> MemberList;
    UPROPERTY(Transient) TObjectPtr<UScrollBox> MemberScroll;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> MemberRings;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> ActionRings;
    UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> ActionButtons;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> TabRings;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> DialogRings;
    UPROPERTY(Transient) TObjectPtr<UWidget> DialogLayer;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DialogText;
    UPROPERTY(Transient) TObjectPtr<UWidget> InCompanyBox;
    UPROPERTY(Transient) TObjectPtr<UWidget> NoCompanyBox;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> EmblemText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> CompanyTitle;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> CompanySubtitle;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> OverviewCounts;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> OverviewLeader;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PolicyText;
    UPROPERTY(Transient) TObjectPtr<UWidget> PolicyButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> NoCompanyInvite;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailName;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailRank;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailStatus;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailInfo;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailGlyph;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> LogBox;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> InviteListBox;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> RolesBox;
    UPROPERTY(Transient) TObjectPtr<UWidget> LogPage;
    UPROPERTY(Transient) TObjectPtr<UWidget> InvitePage;
    UPROPERTY(Transient) TObjectPtr<UWidget> RolesPage;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ListHeading;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> InviteStatus;
};
