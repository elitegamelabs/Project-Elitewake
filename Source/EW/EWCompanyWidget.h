#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWCompanyWidget.generated.h"
class UBorder;
class UEditableTextBox;
class UProgressBar;
class UScrollBox;
class UTextBlock;
class UVerticalBox;
class UWidget;

enum class EEWSampleRank : uint8 { Recruit, Member, Officer, Leader };

/** One row of the sample roster. The Company screen is a front-end prototype (owner, October 25): nothing here reaches a server. */
struct FEWSampleMember
{
    FString Name;
    EEWSampleRank Rank = EEWSampleRank::Member;
    bool bOnline = false;
    FString TimePlayed;
    FString LastSeen;
    FString Info;
};
struct FEWSampleInvite { FString Name; FString Sent; bool bIncoming = false; };
struct FEWSampleLog { FString Time; FString Glyph; FString Text; };

/**
 * The menu's Company section, as a front-end prototype with sample data: members with search, the company's overview, the picked member's details and
 * rank-dependent actions (promote, demote, invite, remove, transfer leadership), an activity log, invitations and a preview of what each rank may do.
 * Every action only changes this screen's sample state; destructive ones ask first. Mouse, keyboard and controller reach all of it.
 */
UCLASS()
class EW_API UEWCompanyWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual TSharedRef<SWidget> RebuildWidget() override;

    /** Keys the Inventory screen hands over while this section is open. Returns true when the key was used (Escape and B return false with no dialog open, so the menu can close). */
    bool HandleMenuKey(const FKey& Key);
    /** True while one of this screen's text boxes has the keyboard. */
    bool IsTyping() const;
    /** True when a screen position is over one of this screen's text boxes. */
    bool IsPointerOverTextBox(const FVector2D& ScreenPosition) const;

    UFUNCTION(BlueprintPure, Category="Company") int32 GetMemberCount() const { return Members.Num(); }
    UFUNCTION(BlueprintPure, Category="Company") int32 GetShownMemberCount() const { return Shown.Num(); }
    UFUNCTION(BlueprintPure, Category="Company") int32 GetOnlineCount() const;
    UFUNCTION(BlueprintPure, Category="Company") int32 GetPendingInviteCount() const;
    UFUNCTION(BlueprintPure, Category="Company") int32 GetLogCount() const { return Log.Num(); }
    UFUNCTION(BlueprintPure, Category="Company") int32 GetSubTab() const { return SubTab; }
    UFUNCTION(BlueprintPure, Category="Company") bool IsConfirmOpen() const { return Confirming != INDEX_NONE; }
    UFUNCTION(BlueprintPure, Category="Company") FText GetSelectedName() const;
    UFUNCTION(BlueprintPure, Category="Company") FText GetSelectedRankText() const;
    /** 0 recruit .. 3 leader */
    UFUNCTION(BlueprintPure, Category="Company") int32 GetSelectedRank() const;
    UFUNCTION(BlueprintPure, Category="Company") int32 GetViewerRank() const;
    UFUNCTION(BlueprintPure, Category="Company") bool IsActionEnabled(int32 Action) const;
    UFUNCTION(BlueprintCallable, Category="Company") void SetSearch(const FString& Text);
    UFUNCTION(BlueprintCallable, Category="Company") void SelectMemberByName(const FString& Name);
    UFUNCTION(BlueprintCallable, Category="Company") void SetSubTab(int32 Tab);
    /** 0 promote, 1 demote, 2 invite, 3 remove, 4 transfer leadership. Remove and transfer open a confirmation first. */
    UFUNCTION(BlueprintCallable, Category="Company") void DoAction(int32 Action);
    UFUNCTION(BlueprintCallable, Category="Company") void ConfirmDialog(bool bConfirm);
    UFUNCTION(BlueprintCallable, Category="Company") void SendSampleInvite(const FString& Name);
    UFUNCTION(BlueprintCallable, Category="Company") void CycleViewerRank();

private:
    UFUNCTION() void MemberPressed(int32 Index);
    UFUNCTION() void ActionPressed(int32 Action) { DoAction(Action); }
    UFUNCTION() void SubTabPressed(int32 Tab) { SetSubTab(Tab); }
    UFUNCTION() void InviteRowPressed(int32 Code);
    UFUNCTION() void DialogPressed(int32 Choice) { ConfirmDialog(Choice == 1); }
    UFUNCTION() void SearchChanged(const FText& Text) { SetSearch(Text.ToString()); }
    UFUNCTION() void InviteCommitted(const FText& Text, ETextCommit::Type Method);
    UFUNCTION() void InviteButtonPressed(int32 Index);
    UFUNCTION() void ViewAsPressed(int32 Index) { CycleViewerRank(); }

    void BuildSampleData();
    void RebuildList();
    void RefreshAll();
    void RefreshInvites();
    void RefreshLog();
    void RefreshRoles();
    void AddLog(const FString& Glyph, const FString& Text);
    void SetViewerRank(EEWSampleRank Rank);
    const FEWSampleMember* SelectedMember() const;
    int32 YouIndex() const;
    int32 IndexOfName(const FString& Name) const;
    static FString RankName(EEWSampleRank Rank);

    TArray<FEWSampleMember> Members;
    TArray<FEWSampleInvite> Invites;
    TArray<FEWSampleLog> Log;
    TArray<int32> Shown;             // indices into Members that pass the search
    int32 Selected = 0;              // index into Members
    FString DisplacedLeader;         // the leader who stepped down to Officer while the preview shows you as Leader
    int32 SubTab = 0;
    int32 ActionCursor = 0;
    int32 Confirming = INDEX_NONE;   // the action waiting for a yes
    int32 DialogChoice = 0;
    FString Filter;
    int32 InviteCounter = 0;

    UPROPERTY(Transient) TObjectPtr<UEditableTextBox> SearchBox;
    UPROPERTY(Transient) TObjectPtr<UEditableTextBox> InviteBox;
    UPROPERTY(Transient) TObjectPtr<UVerticalBox> MemberList;
    UPROPERTY(Transient) TObjectPtr<UScrollBox> MemberScroll;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> MemberRings;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> ActionRings;
    UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> ActionButtons;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> TabRings;
    UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> DialogRings;
    UPROPERTY(Transient) TObjectPtr<UWidget> DialogLayer;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DialogText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> OverviewCounts;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> OverviewLeader;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ViewerText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailName;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailRank;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailStatus;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> DetailTime;
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
