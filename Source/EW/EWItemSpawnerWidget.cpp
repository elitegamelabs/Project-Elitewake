#include "EWItemSpawnerWidget.h"
#include "EWCraftingRecipe.h"
#include "EWInventoryWidget.h"
#include "EWItemDefinition.h"
#include "EWPlayerController.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Image.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/AssetManager.h"
#include "Engine/Texture2D.h"
#include "InputCoreTypes.h"

namespace
{
    const FLinearColor SpawnerGold(1.f, .85f, .35f, 1.f);
    const FLinearColor SpawnerClear(0.f, 0.f, 0.f, 0.f);
    const FLinearColor TileColour(.07f, .085f, .1f, 1.f);
}

void UEWItemSpawnerWidget::GatherItems(TArray<UEWItemDefinition*>& Out, int32& OutCraftable)
{
    Out.Reset();
    // What the recipes make.
    TSet<UEWItemDefinition*> Craftable;
    TArray<FAssetData> Recipes;
    FAssetRegistryModule::GetRegistry().GetAssetsByClass(UEWCraftingRecipe::StaticClass()->GetClassPathName(), Recipes, true);
    for (const FAssetData& Data : Recipes)
        if (const auto* Recipe = Cast<UEWCraftingRecipe>(Data.GetAsset()); Recipe && Recipe->Output) Craftable.Add(Recipe->Output);
    // Every item (the Asset Manager's EWItem list), loaded.
    TSet<UEWItemDefinition*> All = Craftable;
    TArray<FPrimaryAssetId> Ids;
    UAssetManager::Get().GetPrimaryAssetIdList(FPrimaryAssetType(TEXT("EWItem")), Ids);
    for (const FPrimaryAssetId& Id : Ids)
        if (auto* Item = Cast<UEWItemDefinition>(UAssetManager::Get().GetPrimaryAssetPath(Id).TryLoad())) All.Add(Item);
    // The icon-check test items are not things to carry.
    for (auto It = All.CreateIterator(); It; ++It) if ((*It)->GetName().StartsWith(TEXT("DA_TestIcon"))) It.RemoveCurrent();
    auto ByName = [](const UEWItemDefinition& A, const UEWItemDefinition& B) { return A.DisplayName.ToString() < B.DisplayName.ToString(); };
    TArray<UEWItemDefinition*> First, Rest;
    for (UEWItemDefinition* Item : All) (Craftable.Contains(Item) ? First : Rest).Add(Item);
    First.Sort(ByName); Rest.Sort(ByName);
    OutCraftable = First.Num();
    Out = MoveTemp(First);
    Out.Append(Rest);
}

FText UEWItemSpawnerWidget::GetStatus() const { return Status ? Status->GetText() : FText::GetEmpty(); }

TSharedRef<SWidget> UEWItemSpawnerWidget::RebuildWidget()
{
    SetIsFocusable(true);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        TArray<UEWItemDefinition*> Found;
        GatherItems(Found, CraftableCount);
        Items.Append(Found);

        auto* Root = WidgetTree->ConstructWidget<UBorder>();
        Root->SetBrushColor(FLinearColor(.01f, .02f, .03f, .82f));
        Root->SetHorizontalAlignment(HAlign_Center); Root->SetVerticalAlignment(VAlign_Center);
        WidgetTree->RootWidget = Root;
        auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(1120); Size->SetHeightOverride(760); Root->SetContent(Size);
        auto* Panel = WidgetTree->ConstructWidget<UBorder>(); Panel->SetBrushColor(FLinearColor(.03f, .036f, .042f, .95f)); Panel->SetPadding(FMargin(20)); Size->SetContent(Panel);
        auto* Body = WidgetTree->ConstructWidget<UVerticalBox>(); Panel->SetContent(Body);
        auto Text = [&](UVerticalBox* Into, const FString& Value, int32 FontSize, const FLinearColor& Colour, float Below)
        {
            auto* T = WidgetTree->ConstructWidget<UTextBlock>(); T->SetText(FText::FromString(Value)); T->SetColorAndOpacity(FSlateColor(Colour));
            auto F = T->GetFont(); F.Size = FontSize; T->SetFont(F); T->SetAutoWrapText(true);
            Into->AddChildToVerticalBox(T)->SetPadding(FMargin(0, 0, 0, Below));
            return T;
        };
        Text(Body, TEXT("ITEM SPAWNER  ·  testing"), 24, FLinearColor(.93f, .86f, .7f), 2);
        Text(Body, TEXT("Click an item, or move with the d-pad and press A, to get one of it per press. B, F9 or Escape closes."), 13, FLinearColor(.6f, .66f, .72f), 6);
        Status = Text(Body, TEXT(" "), 14, FLinearColor(.5f, .85f, .55f), 8);
        Scroll = WidgetTree->ConstructWidget<UScrollBox>(); Body->AddChildToVerticalBox(Scroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto* List = WidgetTree->ConstructWidget<UVerticalBox>(); Scroll->AddChild(List);

        auto Group = [&](const FString& Heading, int32 From, int32 To)
        {
            Text(List, Heading, 15, FLinearColor(.88f, .86f, .8f), 6);
            auto* Grid = WidgetTree->ConstructWidget<UUniformGridPanel>(); Grid->SetSlotPadding(FMargin(4));
            List->AddChildToVerticalBox(Grid)->SetPadding(FMargin(0, 0, 0, 14));
            for (int32 Index = From; Index < To; ++Index)
            {
                const UEWItemDefinition* Item = Items[Index];
                auto* Ring = WidgetTree->ConstructWidget<UBorder>(); Ring->SetPadding(FMargin(2)); Ring->SetBrushColor(SpawnerClear);
                auto* Tile = WidgetTree->ConstructWidget<UEWRecipeButton>(); Tile->Initialize(Index); Tile->EnableHover(); Tile->SetBackgroundColor(TileColour);
                Tile->OnRecipePressed.AddDynamic(this, &UEWItemSpawnerWidget::TilePressed);
                Tile->OnRecipeHovered.AddDynamic(this, &UEWItemSpawnerWidget::TileHovered);
                auto* Inside = WidgetTree->ConstructWidget<UVerticalBox>();
                auto* Picture = WidgetTree->ConstructWidget<UImage>();
                if (UTexture2D* Icon = Item->Icon.LoadSynchronous()) Picture->SetBrushFromTexture(Icon);
                else Picture->SetColorAndOpacity(FLinearColor(.2f, .24f, .28f, 1.f));
                auto* PictureSize = WidgetTree->ConstructWidget<USizeBox>(); PictureSize->SetWidthOverride(72); PictureSize->SetHeightOverride(72); PictureSize->SetContent(Picture);
                Inside->AddChildToVerticalBox(PictureSize)->SetHorizontalAlignment(HAlign_Center);
                auto* Name = WidgetTree->ConstructWidget<UTextBlock>(); Name->SetText(Item->DisplayName.IsEmpty() ? FText::FromString(Item->GetName()) : Item->DisplayName);
                Name->SetJustification(ETextJustify::Center); Name->SetAutoWrapText(true); { auto F = Name->GetFont(); F.Size = 11; Name->SetFont(F); }
                Inside->AddChildToVerticalBox(Name)->SetPadding(FMargin(0, 4, 0, 0));
                auto* TileSize = WidgetTree->ConstructWidget<USizeBox>(); TileSize->SetWidthOverride(118); TileSize->SetHeightOverride(126); TileSize->SetContent(Inside);
                Tile->SetContent(TileSize); Ring->SetContent(Tile);
                const int32 Local = Index - From;
                Grid->AddChildToUniformGrid(Ring, Local / Columns, Local % Columns);
                Rings.Add(Ring);
            }
        };
        Group(FString::Printf(TEXT("CRAFTABLE  (%d)"), CraftableCount), 0, CraftableCount);
        Group(FString::Printf(TEXT("EVERYTHING ELSE  (%d: no recipe yet)"), Items.Num() - CraftableCount), CraftableCount, Items.Num());
        MoveCursor(0);
    }
    return Super::RebuildWidget();
}

void UEWItemSpawnerWidget::Place(int32 Index, int32& Row, int32& Column) const
{
    const int32 CraftRows = FMath::DivideAndRoundUp(CraftableCount, Columns);
    const bool bFirst = Index < CraftableCount;
    const int32 Local = bFirst ? Index : Index - CraftableCount;
    Row = Local / Columns + (bFirst ? 0 : CraftRows);
    Column = Local % Columns;
}

int32 UEWItemSpawnerWidget::IndexAt(int32 Row, int32 Column) const
{
    const int32 CraftRows = FMath::DivideAndRoundUp(CraftableCount, Columns);
    const bool bFirst = Row < CraftRows;
    const int32 Start = bFirst ? Row * Columns : CraftableCount + (Row - CraftRows) * Columns;
    const int32 End = bFirst ? CraftableCount : Items.Num();
    if (Row < 0 || Start >= End) return INDEX_NONE;
    return FMath::Min(Start + Column, End - 1);
}

void UEWItemSpawnerWidget::MoveCursor(int32 Index)
{
    if (!Items.IsValidIndex(Index)) return;
    Cursor = Index;
    for (int32 Place = 0; Place < Rings.Num(); ++Place) Rings[Place]->SetBrushColor(Place == Cursor ? SpawnerGold : SpawnerClear);
    if (Scroll && Rings.IsValidIndex(Cursor)) Scroll->ScrollWidgetIntoView(Rings[Cursor], true);
}

void UEWItemSpawnerWidget::Give(int32 Index)
{
    if (!Items.IsValidIndex(Index)) return;
    MoveCursor(Index);
    auto* Player = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!Player) return;
    Player->ServerDebugGiveItem(Items[Index]);
    if (Status) Status->SetText(FText::Format(NSLOCTEXT("Elitewake", "SpawnerGave", "+1 {0}"), Items[Index]->DisplayName));
}

FReply UEWItemSpawnerWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key == EKeys::F9 || Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Gamepad_Special_Right)
    {
        if (auto* Player = Cast<AEWPlayerController>(GetOwningPlayer())) Player->SetItemSpawnerOpen(false);
        return FReply::Handled();
    }
    if (Key == EKeys::Gamepad_FaceButton_Bottom || Key == EKeys::Enter || Key == EKeys::SpaceBar)
    {
        // One item per press: a held button does not repeat.
        if (!Event.IsRepeat()) Give(Cursor);
        return FReply::Handled();
    }
    const bool bUp = Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up;
    const bool bDown = Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down;
    const bool bLeft = Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_LeftStick_Left;
    const bool bRight = Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Gamepad_LeftStick_Right;
    if (bUp || bDown || bLeft || bRight)
    {
        int32 Row, Column;
        Place(Cursor, Row, Column);
        if (bLeft || bRight) MoveCursor(FMath::Clamp(Cursor + (bRight ? 1 : -1), 0, Items.Num() - 1));
        else if (const int32 Next = IndexAt(Row + (bDown ? 1 : -1), Column); Next != INDEX_NONE) MoveCursor(Next);
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(Geometry, Event);
}
