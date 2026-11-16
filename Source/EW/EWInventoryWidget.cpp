// Copyright Elite Game Labs. All Rights Reserved.

#include "EWInventoryWidget.h"
#include "EWCompanyWidget.h"
#include "EWJournalWidget.h"
#include "EWSkillTreeWidget.h"
#include "EWTamesWidget.h"
#include "GameFramework/PlayerState.h"
#include "Components/EditableTextBox.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "EWHotbarWidget.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWCraftingRecipe.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Components/ScaleBox.h"
#include "Components/WrapBox.h"
#include "EWHudIcon.h"
#include "Components/WrapBoxSlot.h"
#include "Engine/Texture2D.h"
#include "EWSurvivalComponent.h"
#include "EWProgressionComponent.h"
#include "EWWalletComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/ProgressBar.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScaleBoxSlot.h"
#include "Components/WidgetSwitcher.h"
#include "Widgets/Layout/SBorder.h"
#include "InputCoreTypes.h"
#include "Styling/SlateColor.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Fonts/CompositeFont.h"
#include "Materials/MaterialInterface.h"
#include "Misc/Paths.h"

void UEWCraftingRecipeTile::SynchronizeProperties()
{
    Super::SynchronizeProperties();
    if (!MyBorder) return;
    MyBorder->SetOnMouseButtonDown(FPointerEventHandler::CreateUObject(this, &UEWCraftingRecipeTile::Inspect));
    MyBorder->SetOnMouseDoubleClick(FPointerEventHandler::CreateUObject(this, &UEWCraftingRecipeTile::Craft));
    MyBorder->SetOnMouseEnter(FNoReplyPointerEventHandler::CreateUObject(this, &UEWCraftingRecipeTile::Enter));
    MyBorder->SetOnMouseLeave(FSimpleNoReplyPointerEventHandler::CreateUObject(this, &UEWCraftingRecipeTile::Leave));
}

FReply UEWCraftingRecipeTile::Inspect(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();
    OnInspect.Broadcast(RecipeIndex);
    return FReply::Handled();
}

FReply UEWCraftingRecipeTile::Craft(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();
    OnCraft.Broadcast(RecipeIndex);
    return FReply::Handled();
}

void UEWCraftingRecipeTile::Enter(const FGeometry& Geometry, const FPointerEvent& Event) { OnHover.Broadcast(RecipeIndex); }
void UEWCraftingRecipeTile::Leave(const FPointerEvent& Event) { OnHover.Broadcast(INDEX_NONE); }

namespace
{
    constexpr float InventoryWidth = 1856.f, InventoryHeight = 944.f;
    constexpr float SlotTileWidth = 100.f, SlotTileHeight = 76.f, GridGap = 6.f;
    constexpr float RecipeTileWidth = 93.f, RecipeGridGap = 1.f;
    constexpr int32 InventoryColumns = 6, CraftingColumns = 7;
    const FLinearColor Ivory = FLinearColor::FromSRGBColor(FColor(250, 232, 200));
    const FLinearColor MutedGold = FLinearColor::FromSRGBColor(FColor(229, 190, 115));
    const FLinearColor InventoryPanelTint = FLinearColor::FromSRGBColor(FColor(62, 40, 26, 179));
    const FLinearColor SurvivorPanelTint = FLinearColor::FromSRGBColor(FColor(62, 40, 26, 204));
    const FLinearColor CursorGold(1.f, .79f, .38f);
    constexpr float SlotStroke = 2.f;
    constexpr float HeaderEndInset = 44.f;

    TMap<UEWItemDefinition*, int64> RecipeCosts(const UEWCraftingRecipe& Recipe)
    {
        TMap<UEWItemDefinition*, int64> Costs;
        for (const auto& Ingredient : Recipe.Ingredients)
            if (Ingredient.Item && Ingredient.Quantity > 0)
                Costs.FindOrAdd(Ingredient.Item) += Ingredient.Quantity;
        return Costs;
    }

    FText CraftReadinessText(EEWCraftResult Result)
    {
        switch (Result)
        {
        case EEWCraftResult::Success: return NSLOCTEXT("Elitewake", "RecipeReady", "Ready");
        case EEWCraftResult::MissingIngredients: return NSLOCTEXT("Elitewake", "RecipeMissing", "Not enough materials");
        case EEWCraftResult::InventoryFull: return NSLOCTEXT("Elitewake", "RecipeFull", "Make room in your inventory");
        case EEWCraftResult::NeedsFire: return NSLOCTEXT("Elitewake", "RecipeFire", "Requires a lit campfire");
        case EEWCraftResult::Locked: return NSLOCTEXT("Elitewake", "RecipeLocked", "Recipe is not unlocked");
        case EEWCraftResult::Busy: return NSLOCTEXT("Elitewake", "RecipeBusy", "Crafting in progress");
        default: return NSLOCTEXT("Elitewake", "RecipeUnavailable", "Recipe unavailable");
        }
    }

    FSlateBrush BrassRect(float Width, const FLinearColor& Edge = MutedGold,
        const FLinearColor& Fill = FLinearColor::Transparent, float Radius = 5.f)
    {
        FSlateRoundedBoxBrush Brush(Fill, Radius);
        Brush.OutlineSettings.Color = FSlateColor(Edge);
        Brush.OutlineSettings.Width = Width;
        Brush.OutlineSettings.bUseBrushTransparency = false;
        return Brush;
    }

    FSlateBrush InventoryBrush(const TCHAR* Texture, ESlateBrushDrawType::Type Type, FVector2D Size, FMargin Margin)
    {
        FSlateBrush Brush;
        Brush.SetResourceObject(LoadObject<UTexture2D>(nullptr, *FString::Printf(
            TEXT("/Game/Elitewake/UI/Inventory/T_Inventory%s.T_Inventory%s"), Texture, Texture)));
        Brush.DrawAs = Type;
        Brush.ImageSize = Size;
        Brush.Margin = Margin;
        return Brush;
    }

    FSlateBrush InventoryHeaderBrush()
    {
        auto Brush = InventoryBrush(TEXT("SectionHeader"), ESlateBrushDrawType::Box, FVector2D(240, 70), FMargin(.18f));
        if (auto* Material = LoadObject<UMaterialInterface>(nullptr,
            TEXT("/Game/Elitewake/UI/Inventory/M_InventoryRoundedHeader.M_InventoryRoundedHeader")))
        {
            Brush.SetResourceObject(Material);
        }
        return Brush;
    }

    void StyleText(UTextBlock* Text, int32 Size, const FLinearColor& Tint = Ivory, bool bSerif = false)
    {
        auto Font = Text->GetFont();
        Font.Size = Size;
        if (bSerif)
        {
            const FString Path = FPaths::ProjectContentDir() / TEXT("Slate/Fonts/IMFeENrm28P.ttf");
            if (FPaths::FileExists(Path)) Font = FSlateFontInfo(Path, Size);
        }
        else Font.TypefaceFontName = TEXT("Medium");
        Font.OutlineSettings.OutlineSize = bSerif ? 1 : 2;
        Font.OutlineSettings.OutlineColor = FLinearColor(.018f, .010f, .005f, .96f);
        Text->SetFont(Font);
        Text->SetColorAndOpacity(FSlateColor(Tint));
        Text->SetShadowOffset(FVector2D(1, 1));
        Text->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, .9f));
    }

    void StyleInventoryButton(UButton* Button, bool bSocket = false)
    {
        const auto Normal = bSocket ? BrassRect(SlotStroke)
            : BrassRect(1.8f, MutedGold, FLinearColor(.085f, .043f, .020f), 8.f);
        const auto Hover = bSocket ? BrassRect(2.5f, CursorGold)
            : BrassRect(1.8f, CursorGold, FLinearColor(.15f, .075f, .032f), 8.f);
        const auto Pressed = bSocket ? BrassRect(SlotStroke, CursorGold)
            : BrassRect(1.8f, CursorGold, FLinearColor(.055f, .027f, .013f), 8.f);
        const auto Disabled = bSocket ? Normal
            : BrassRect(1.5f, MutedGold * .75f, FLinearColor(.052f, .031f, .021f), 8.f);
        FButtonStyle Style = Button->GetStyle();
        Style.SetNormal(Normal).SetHovered(Hover).SetPressed(Pressed).SetDisabled(Disabled);
        const FMargin ContentPadding = bSocket ? FMargin(0, 2) : FMargin(5, 3);
        Style.SetNormalPadding(ContentPadding).SetPressedPadding(ContentPadding);
        Button->SetStyle(Style);
    }

    void StyleInventoryHeading(UTextBlock* Text, int32 Size, const FLinearColor& Tint = Ivory)
    {
        static const TSharedRef<const FCompositeFont> HeadingFont = MakeShared<FCompositeFont>(
            FName(TEXT("Bold")), FPaths::ProjectContentDir() / TEXT("Slate/Fonts/Tinos-Bold.ttf"),
            EFontHinting::Default, EFontLoadingPolicy::LazyLoad);
        StyleText(Text, Size, Tint);
        FSlateFontInfo Font(HeadingFont, Size);
        Font.OutlineSettings = Text->GetFont().OutlineSettings;
        Font.OutlineSettings.OutlineSize = 1;
        Text->SetFont(Font);
        Text->SetAutoWrapText(false);
    }

    void StyleInventoryScroll(UScrollBox* Scroll)
    {
        auto Style = Scroll->GetWidgetBarStyle();
        Style.SetNormalThumbImage(BrassRect(1.f, MutedGold, FLinearColor(.22f, .12f, .04f)));
        Style.SetHoveredThumbImage(BrassRect(1.f, CursorGold, FLinearColor(.32f, .18f, .06f)));
        Style.SetDraggedThumbImage(Style.HoveredThumbImage);
        Scroll->SetWidgetBarStyle(Style);
    }
}

TSharedRef<SWidget> UEWInventoryWidget::RebuildWidget()
{
	// The native tree must exist before UUserWidget creates its Slate content.
	BuildWidgetTree();
	return Super::RebuildWidget();
}

void UEWInventoryWidget::NativeConstruct()
{
	Super::NativeConstruct();
    SetIsFocusable(true);
    SelectedIndex = INDEX_NONE;
    bShowingDetails = false;
    bLbChordUsed = true;
    if (EquipmentResultText) EquipmentResultText->SetText(FText::GetEmpty());

	BoundInventory = ResolveInventory();
    BoundEquipment = ResolveEquipment();
    if (const auto* Pawn = Cast<AEWCharacter>(GetOwningPlayerPawn())) BoundHotbar = Pawn->GetHotbarComponent();
    if (BoundHotbar) BoundHotbar->OnHotbarChanged.AddDynamic(this, &UEWInventoryWidget::RefreshHotbarAssignments);
    if (BoundEquipment) BoundEquipment->OnEquipmentChanged.AddDynamic(this, &UEWInventoryWidget::RefreshInventory);
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.AddDynamic(this, &UEWInventoryWidget::RefreshInventory);
	}

	// The menu always opens on the inventory page (owner, October 25), whatever section it was closed on.
	ResetToInventoryPage();
}

void UEWInventoryWidget::NativeDestruct()
{
    CancelAttributeChanges();
    ClosePortrait();
	if (BoundInventory)
	{
		BoundInventory->OnInventoryChanged.RemoveDynamic(this, &UEWInventoryWidget::RefreshInventory);
	}
	BoundInventory = nullptr;
    InventoryImages.Reset(); MaterialImages.Reset();
    if (BoundEquipment) BoundEquipment->OnEquipmentChanged.RemoveDynamic(this, &UEWInventoryWidget::RefreshInventory);
    BoundEquipment = nullptr;
    if (BoundHotbar) BoundHotbar->OnHotbarChanged.RemoveDynamic(this, &UEWInventoryWidget::RefreshHotbarAssignments);
    BoundHotbar = nullptr;
    AnalogDirection = 0; AnalogHorizontal = 0;
	Super::NativeDestruct();
}

void EWStyleSearchBox(UEditableTextBox* Box)
{
	if (!Box) return;
	FEditableTextBoxStyle Style = Box->WidgetStyle;
	Style.SetBackgroundColor(FSlateColor(FLinearColor(.05f, .06f, .07f, .92f)));
	Style.SetForegroundColor(FSlateColor(FLinearColor(.92f, .92f, .9f)));
	Style.SetFocusedForegroundColor(FSlateColor(FLinearColor::White));
	Style.SetReadOnlyForegroundColor(FSlateColor(FLinearColor(.7f, .72f, .74f)));
	Box->SetWidgetStyle(Style);
	Box->SetHintText(Box->GetHintText());
}

void UEWInventoryWidget::BuildWidgetTree()
{
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("InventoryPanel"));
    MenuBackdrop = Panel;
	Panel->SetBrushColor(FLinearColor::Transparent);
	Panel->SetPadding(FMargin(16.f, 8.f, 16.f, 12.f));
	Panel->SetHorizontalAlignment(HAlign_Fill);
	Panel->SetVerticalAlignment(VAlign_Fill);
	WidgetTree->RootWidget = Panel;

	UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryContent"));
	Panel->SetContent(Content);

	// Top navigation (owner, October 25): INVENTORY, SKILLS, COMPANY, TAMES, JOURNAL. The open tab is light, the rest dark translucent grey.
	auto* Tabs = WidgetTree->ConstructWidget<UHorizontalBox>();
    auto* TabFrame = WidgetTree->ConstructWidget<UBorder>();
    TabFrame->SetBrush(InventoryHeaderBrush());
    TabFrame->SetPadding(FMargin(25.f, 5.f));
    TabFrame->SetContent(Tabs);
	Content->AddChildToVerticalBox(TabFrame);
	const TCHAR* Sections[] = {TEXT("INVENTORY"), TEXT("SKILLS"), TEXT("COMPANY"), TEXT("TAMES"), TEXT("JOURNAL")};
	for (int32 Index = 0; Index < 5; ++Index)
	{
		auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
		Button->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::SelectSection);
		auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(Sections[Index]));
        StyleInventoryHeading(Label, 21);
		Label->SetJustification(ETextJustify::Center); Button->SetContent(Label);
		auto* NavSlot = Tabs->AddChildToHorizontalBox(Button); NavSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		NavSlot->SetPadding(FMargin(2, 0)); SectionButtons.Add(Button); SectionLabels.Add(Label);
	}
	auto* Body = WidgetTree->ConstructWidget<UHorizontalBox>();
	Content->AddChildToVerticalBox(Body)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	auto FillSlot = [&](UWidget* Widget, float Weight, const FMargin& Inset)
	{
		auto* BodySlot = Body->AddChildToHorizontalBox(Widget);
		auto Size = FSlateChildSize(ESlateSizeRule::Fill); Size.Value = Weight;
		BodySlot->SetSize(Size); BodySlot->SetPadding(Inset);
	};
	// Whole-screen sections: each fills the space under the tabs, like any other MMO's tab (owner, October 25).
	CompanyPanel = CreateWidget<UEWCompanyWidget>(GetOwningPlayer());
	FillSlot(CompanyPanel, 1.f, FMargin(0, 12, 0, 0)); CompanyPanel->SetVisibility(ESlateVisibility::Collapsed);
	JournalPanel = CreateWidget<UEWJournalWidget>(GetOwningPlayer());
	FillSlot(JournalPanel, 1.f, FMargin(0, 12, 0, 0)); JournalPanel->SetVisibility(ESlateVisibility::Collapsed);
	SkillsPanel = CreateWidget<UEWSkillTreeWidget>(GetOwningPlayer());
	FillSlot(SkillsPanel, 1.f, FMargin(0, 12, 0, 0)); SkillsPanel->SetVisibility(ESlateVisibility::Collapsed);
	TamesPanel = CreateWidget<UEWTamesWidget>(GetOwningPlayer());
	FillSlot(TamesPanel, 1.f, FMargin(0, 12, 0, 0)); TamesPanel->SetVisibility(ESlateVisibility::Collapsed);

    // Scale the approved desktop proportions as a unit. Each scroll view keeps its own hit geometry.
    auto* Scale = WidgetTree->ConstructWidget<UScaleBox>();
    Scale->SetStretch(EStretch::ScaleToFit);
    auto* Reference = WidgetTree->ConstructWidget<USizeBox>();
    Reference->SetWidthOverride(InventoryWidth);
    Reference->SetHeightOverride(InventoryHeight);
    auto* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
    Reference->SetContent(Columns);
    auto* ScaledSlot = CastChecked<UScaleBoxSlot>(Scale->AddChild(Reference));
    ScaledSlot->SetVerticalAlignment(VAlign_Top);
    InventoryLayout = Scale;
    FillSlot(Scale, 1.f, FMargin(0, 7, 0, 0));
    auto Frame = InventoryBrush(TEXT("Frame"), ESlateBrushDrawType::Border, FVector2D(72), FMargin(.20f));
    if (auto* RoundedFrame = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/Elitewake/UI/Inventory/M_InventoryRoundedFrame.M_InventoryRoundedFrame")))
    {
        Frame.SetResourceObject(RoundedFrame);
        Frame.ImageSize = FVector2D(288.f);
    }
    const auto Header = InventoryHeaderBrush();
    auto AddColumn = [&](UWidget* In, float Weight, const FMargin& Gap, const FLinearColor& Tint)
    {
        auto* Layers = WidgetTree->ConstructWidget<UOverlay>();
        auto* Backing = WidgetTree->ConstructWidget<UBorder>();
        Backing->SetBrush(FSlateRoundedBoxBrush(Tint, 13.f));
        Backing->SetVisibility(ESlateVisibility::HitTestInvisible);
        auto* BackingSlot = Layers->AddChildToOverlay(Backing);
        BackingSlot->SetHorizontalAlignment(HAlign_Fill);
        BackingSlot->SetVerticalAlignment(VAlign_Fill);
        BackingSlot->SetPadding(FMargin(4.f));
        auto* ContentSlot = Layers->AddChildToOverlay(In);
        ContentSlot->SetHorizontalAlignment(HAlign_Fill);
        ContentSlot->SetVerticalAlignment(VAlign_Fill);

        auto* Slot = Columns->AddChildToHorizontalBox(Layers);
        FSlateChildSize Size(ESlateSizeRule::Fill); Size.Value = Weight;
        Slot->SetSize(Size);
        Slot->SetPadding(Gap);
    };
	// Left: the inventory panel, and the crafting section directly beneath it.
	auto* Browser = WidgetTree->ConstructWidget<UVerticalBox>(); BrowserPanel = Browser;
	auto* BrowserBorder = WidgetTree->ConstructWidget<UBorder>(); BrowserBorder->SetPadding(FMargin(12, 15, 6, 15));
	BrowserBorder->SetBrush(Frame); BrowserBorder->SetContent(Browser);
	BrowserHost = BrowserBorder;
	AddColumn(BrowserBorder, 37.f, FMargin(0, 0, 6, 0), InventoryPanelTint);
	// A section's heading, its search box and (for the inventory) a small sort button.
	auto Heading = [&](UVerticalBox* Into, const TCHAR* Title, UEditableTextBox*& Search, bool bSort)
	{
		auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
		auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(Title));
        StyleInventoryHeading(Label, 23);
		Row->AddChildToHorizontalBox(Label)->SetVerticalAlignment(VAlign_Center);
		Search = WidgetTree->ConstructWidget<UEditableTextBox>(); Search->SetHintText(NSLOCTEXT("Elitewake", "SearchHint", "Search"));
        if (!bSort) Search->SetHintText(NSLOCTEXT("Elitewake", "SearchRecipes", "Search recipes"));
        FEditableTextBoxStyle SearchStyle = Search->WidgetStyle;
        const auto SearchFrame = BrassRect(1.5f, MutedGold, FLinearColor(.038f, .021f, .011f));
        SearchStyle.SetBackgroundImageNormal(SearchFrame).SetBackgroundImageHovered(SearchFrame).SetBackgroundImageFocused(SearchFrame);
        SearchStyle.SetBackgroundColor(FSlateColor(FLinearColor::White));
        SearchStyle.SetForegroundColor(FSlateColor(Ivory)).SetFocusedForegroundColor(FSlateColor(Ivory));
        auto SearchText = SearchStyle.TextStyle;
        auto SearchFont = SearchText.Font;
        SearchFont.Size = 16;
        SearchFont.TypefaceFontName = TEXT("Medium");
        SearchText.SetFont(SearchFont).SetColorAndOpacity(FSlateColor(Ivory));
        SearchStyle.SetTextStyle(SearchText);
        SearchStyle.SetPadding(FMargin(10, 5));
        Search->SetWidgetStyle(SearchStyle);
		Search->OnTextCommitted.AddDynamic(this, &UEWInventoryWidget::OnSearchCommitted);
		auto* SearchSlot = Row->AddChildToHorizontalBox(Search); SearchSlot->SetPadding(FMargin(16, 0, bSort ? 6 : 0, 0));
		SearchSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); SearchSlot->SetVerticalAlignment(VAlign_Center);
		if (bSort)
		{
			// The small action icon: sorts the grid by name, or back to the order things arrived.
			auto* Sort = WidgetTree->ConstructWidget<UEWInventoryActionButton>(UEWInventoryActionButton::StaticClass(), TEXT("InventorySort"));
            Sort->OnClicked.AddDynamic(this, &UEWInventoryWidget::ToggleSort);
			auto* Glyph = WidgetTree->ConstructWidget<UTextBlock>(); Glyph->SetText(FText::FromString(TEXT("A-Z"))); Glyph->SetJustification(ETextJustify::Center);
            StyleInventoryHeading(Glyph, 17); Sort->SetContent(Glyph);
            StyleInventoryButton(Sort); SortButton = Sort;
			auto* SortSize = WidgetTree->ConstructWidget<USizeBox>(); SortSize->SetWidthOverride(65); SortSize->SetContent(Sort);
			Row->AddChildToHorizontalBox(SortSize)->SetVerticalAlignment(VAlign_Center);
		}
        auto* Plaque = WidgetTree->ConstructWidget<UBorder>();
        Plaque->SetBrush(Header);
        Plaque->SetPadding(FMargin(HeaderEndInset, 12.f));
        Plaque->SetVerticalAlignment(VAlign_Center);
        Plaque->SetContent(Row);
        auto* HeaderSize = WidgetTree->ConstructWidget<USizeBox>();
        HeaderSize->SetMinDesiredHeight(54.f);
        HeaderSize->SetContent(Plaque);
		Into->AddChildToVerticalBox(HeaderSize)->SetPadding(FMargin(0, 0, 0, 4));
	};
	UEditableTextBox* InventorySearchBox = nullptr; UEditableTextBox* CraftSearchBox = nullptr;
	Heading(Browser, TEXT("INVENTORY"), InventorySearchBox, true); SearchBox = InventorySearchBox;
	SearchBox->OnTextChanged.AddDynamic(this, &UEWInventoryWidget::OnInventorySearch);
	SummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventorySummary"));
    StyleText(SummaryText, 18, Ivory, true);
	Browser->AddChildToVerticalBox(SummaryText)->SetPadding(FMargin(0, 0, 0, 6));
	ItemsBox = WidgetTree->ConstructWidget<UWrapBox>(); ItemsBox->SetInnerSlotPadding(FVector2D(GridGap));
    ItemsBox->SetExplicitWrapSize(true); ItemsBox->SetWrapSize(InventoryColumns * (SlotTileWidth + GridGap));
    ItemsScroll = WidgetTree->ConstructWidget<UScrollBox>();
    auto* InventoryGridSlot = CastChecked<UScrollBoxSlot>(ItemsScroll->AddChild(ItemsBox));
    InventoryGridSlot->SetHorizontalAlignment(HAlign_Center);
    auto* PackHeight = WidgetTree->ConstructWidget<USizeBox>();
    PackHeight->SetHeightOverride(328.f); PackHeight->SetContent(ItemsScroll);
	Browser->AddChildToVerticalBox(PackHeight)->SetPadding(FMargin(0, 0, 0, 9));
	Heading(Browser, TEXT("CRAFTING"), CraftSearchBox, false); RecipeSearchBox = CraftSearchBox;
	RecipeSearchBox->OnTextChanged.AddDynamic(this, &UEWInventoryWidget::OnRecipeSearch);
	CraftingBox = WidgetTree->ConstructWidget<UVerticalBox>();
	CraftScroll = WidgetTree->ConstructWidget<UScrollBox>(); CraftScroll->AddChild(CraftingBox);
    StyleInventoryScroll(CraftScroll);
    CraftScroll->SetScrollbarThickness(FVector2D(4.f, 4.f));
    auto* RecipeHeight = WidgetTree->ConstructWidget<USizeBox>();
    RecipeHeight->SetHeightOverride(276); RecipeHeight->SetContent(CraftScroll);
	Browser->AddChildToVerticalBox(RecipeHeight);

	// Centre: the character, equipment, world, stats and the level-up arrows.
	auto* SurvivorBorder = WidgetTree->ConstructWidget<UBorder>();
	SurvivorPanel = SurvivorBorder;
	SurvivorBorder->SetPadding(FMargin(20, 11, 20, 11)); SurvivorBorder->SetBrush(Frame);
	AddColumn(SurvivorBorder, 37.f, FMargin(0, 0, 6, 0), InventoryPanelTint);
    auto* SurvivorColumn = WidgetTree->ConstructWidget<UVerticalBox>();
    SurvivorBorder->SetContent(SurvivorColumn);
    SurvivorScroll = WidgetTree->ConstructWidget<UScrollBox>();
    SurvivorColumn->AddChildToVerticalBox(SurvivorScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    StyleInventoryScroll(SurvivorScroll);
	auto* SurvivorBody = WidgetTree->ConstructWidget<UVerticalBox>(); SurvivorScroll->AddChild(SurvivorBody);
    BuildCharacterPanel(SurvivorBody, SurvivorColumn);

	// Right: the live survivor render composites over the tinted world.
	auto* ViewerBorder = WidgetTree->ConstructWidget<UBorder>(); ViewerBorder->SetPadding(FMargin(17));
	ViewerBorder->SetBrush(Frame);
    RightHost = ViewerBorder;
    AddColumn(ViewerBorder, 26.f, FMargin(0), SurvivorPanelTint);
    PortraitImage = WidgetTree->ConstructWidget<UImage>();
    PortraitImage->SetColorAndOpacity(FLinearColor::Transparent);
    PortraitImage->SetVisibility(ESlateVisibility::HitTestInvisible);
    auto* PortraitScale = WidgetTree->ConstructWidget<UScaleBox>();
    PortraitScale->SetStretch(EStretch::ScaleToFit);
    auto* PortraitSize = WidgetTree->ConstructWidget<USizeBox>();
    PortraitSize->SetWidthOverride(440);
    PortraitSize->SetHeightOverride(880);
    PortraitSize->SetContent(PortraitImage);
    PortraitScale->SetContent(PortraitSize);
    ViewerBorder->SetContent(PortraitScale);

    // Existing actions remain close to the left grids. Recipe ingredients are available on each tile.
    CraftActions = WidgetTree->ConstructWidget<UVerticalBox>();
    Browser->AddChildToVerticalBox(CraftActions)->SetPadding(FMargin(3, 6, 3, 0));
	auto* DetailBorder = WidgetTree->ConstructWidget<UBorder>();
	DetailsPanel = DetailBorder; DetailBorder->SetPadding(FMargin(3, 6)); DetailBorder->SetBrushColor(FLinearColor::Transparent);
	Browser->AddChildToVerticalBox(DetailBorder)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* ItemDetailsScroll = WidgetTree->ConstructWidget<UScrollBox>();
    auto* DetailContent = WidgetTree->ConstructWidget<UVerticalBox>();
    DetailBorder->SetContent(DetailContent);
    DetailContent->AddChildToVerticalBox(ItemDetailsScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	auto* DetailPanel = WidgetTree->ConstructWidget<UVerticalBox>(); ItemDetailsScroll->AddChild(DetailPanel);
	ItemPreview = WidgetTree->ConstructWidget<UImage>();
	auto* PreviewSize = WidgetTree->ConstructWidget<USizeBox>();
	PreviewSize->SetWidthOverride(38); PreviewSize->SetHeightOverride(38); PreviewSize->SetContent(ItemPreview);
	DetailPanel->AddChildToVerticalBox(PreviewSize)->SetHorizontalAlignment(HAlign_Center);
	ItemPreview->GetParent()->SetVisibility(ESlateVisibility::Collapsed);
	DetailsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryDetails"));
	DetailsText->SetAutoWrapText(true);
    StyleText(DetailsText, 16);
	DetailPanel->AddChildToVerticalBox(DetailsText)->SetPadding(FMargin(0, 3));
	EquipmentActionButton = WidgetTree->ConstructWidget<UEWInventoryActionButton>(UEWInventoryActionButton::StaticClass(), TEXT("EquipmentAction"));
	EquipmentActionText = WidgetTree->ConstructWidget<UTextBlock>();
	EquipmentActionButton->SetContent(EquipmentActionText);
    StyleInventoryButton(EquipmentActionButton); StyleText(EquipmentActionText, 17, Ivory, true);
	EquipmentActionButton->OnClicked.AddDynamic(this, &UEWInventoryWidget::PerformEquipmentAction);
    // Keep the existing equip/unequip action accessible even when its description needs scrolling.
	DetailContent->AddChildToVerticalBox(EquipmentActionButton);
	FoodActionButton = WidgetTree->ConstructWidget<UEWInventoryActionButton>(UEWInventoryActionButton::StaticClass(), TEXT("FoodAction"));
	auto* FoodLabel = WidgetTree->ConstructWidget<UTextBlock>();
	FoodLabel->SetText(FText::FromString(TEXT("Eat (R / X)")));
	FoodActionButton->SetContent(FoodLabel);
    StyleInventoryButton(FoodActionButton); StyleText(FoodLabel, 17, Ivory, true);
	FoodActionButton->OnClicked.AddDynamic(this, &UEWInventoryWidget::PerformFoodAction);
	DetailPanel->AddChildToVerticalBox(FoodActionButton);
	EquipmentResultText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("EquipmentResult"));
	EquipmentResultText->SetAutoWrapText(true);
    StyleText(EquipmentResultText, 16, MutedGold);
	Browser->AddChildToVerticalBox(EquipmentResultText)->SetPadding(FMargin(17, 2, 3, 0));

	HotbarAssignments = WidgetTree->ConstructWidget<UVerticalBox>();
	DetailPanel->AddChildToVerticalBox(HotbarAssignments)->SetPadding(FMargin(0, 8));
	auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
	Label->SetText(FText::FromString(TEXT("Hotbar assignment")));
	HotbarAssignments->AddChildToVerticalBox(Label);
	auto* Buttons = WidgetTree->ConstructWidget<UHorizontalBox>();
	HotbarAssignments->AddChildToVerticalBox(Buttons);
	for (int32 i = 0; i < UEWHotbarComponent::SlotCount; ++i)
	{
		auto* Button = WidgetTree->ConstructWidget<UEWHotbarSlotButton>();
		Button->InitializeSlot(i);
		Button->OnSlotPressed.AddDynamic(this, &UEWInventoryWidget::AssignHotbarSlot);
		auto* Text = WidgetTree->ConstructWidget<UTextBlock>();
		Button->SetContent(Text);
        StyleInventoryButton(Button); StyleText(Text, 15, Ivory, true);
		auto* ButtonSlot = Buttons->AddChildToHorizontalBox(Button);
		ButtonSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); ButtonSlot->SetPadding(FMargin(2));
		HotbarButtons.Add(Button); HotbarButtonLabels.Add(Text);
	}
}

void UEWInventoryWidget::BuildCharacterPanel(UVerticalBox* Into, UVerticalBox* Footer)
{
    const auto Header = InventoryHeaderBrush();
    auto Plaque = [&](UWidget* Content, float Above)
    {
        auto* Border = WidgetTree->ConstructWidget<UBorder>();
        Border->SetBrush(Header);
        // Keep content inside the wood face, clear of the trim and corner artwork.
        Border->SetPadding(FMargin(HeaderEndInset, 10.f));
        Border->SetVerticalAlignment(VAlign_Center);
        Border->SetContent(Content);
        Into->AddChildToVerticalBox(Border)->SetPadding(FMargin(0, Above, 0, 3));
    };
    auto Line = [&](int32 Size, const FLinearColor& Colour = Ivory, bool bSerif = false)
    {
        auto* Text = WidgetTree->ConstructWidget<UTextBlock>();
        StyleText(Text, Size, Colour, bSerif);
        return Text;
    };
    auto Heading = [&](const TCHAR* Title, float Above)
    {
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
        StyleInventoryHeading(Label, 23);
        Label->SetText(FText::FromString(Title));
        Plaque(Label, Above);
    };
    auto Meter = [&](UVerticalBox* Parent, FLinearColor Colour, float Height)
    {
        auto* Bar = WidgetTree->ConstructWidget<UProgressBar>();
        FProgressBarStyle Style = Bar->GetWidgetStyle();
        Style.SetBackgroundImage(BrassRect(1.f, MutedGold * .72f, FLinearColor::Transparent, 3.f));
        Style.SetFillImage(BrassRect(0.f, FLinearColor::Transparent, FLinearColor::White, 3.f));
        Bar->SetWidgetStyle(Style);
        Bar->SetFillColorAndOpacity(Colour);
        auto* Size = WidgetTree->ConstructWidget<USizeBox>();
        Size->SetHeightOverride(Height);
        Size->SetContent(Bar);
        Parent->AddChildToVerticalBox(Size)->SetPadding(FMargin(0, 2));
        return Bar;
    };

    auto* Identity = WidgetTree->ConstructWidget<UVerticalBox>();
    NameText = WidgetTree->ConstructWidget<UTextBlock>();
    StyleInventoryHeading(NameText, 28);
    NameText->SetClipping(EWidgetClipping::ClipToBounds);
    NameText->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
    SubtitleText = WidgetTree->ConstructWidget<UTextBlock>();
    StyleInventoryHeading(SubtitleText, 17);
    Identity->AddChildToVerticalBox(NameText);
    Identity->AddChildToVerticalBox(SubtitleText);
    Plaque(Identity, 0);

    LevelValue = WidgetTree->ConstructWidget<UTextBlock>();
    StyleInventoryHeading(LevelValue, 23, CursorGold);
    Into->AddChildToVerticalBox(LevelValue)->SetPadding(FMargin(3, 2, 3, 0));
    LevelBar = Meter(Into, FLinearColor(.92f, .62f, .18f), 11);
    PointsValue = Line(17, Ivory);
    Into->AddChildToVerticalBox(PointsValue)->SetPadding(FMargin(3, 3));

    Heading(TEXT("EQUIPMENT"), 4);
    EquippedBox = WidgetTree->ConstructWidget<UWrapBox>();
    EquippedBox->SetInnerSlotPadding(FVector2D(GridGap));
    Into->AddChildToVerticalBox(EquippedBox);
    HandEquipmentBox = WidgetTree->ConstructWidget<UWrapBox>();
    HandEquipmentBox->SetInnerSlotPadding(FVector2D(GridGap));
    Into->AddChildToVerticalBox(HandEquipmentBox)->SetPadding(FMargin(0, 5, 0, 0));
    ArmorText = Line(15, Ivory);
    ArmorText->SetAutoWrapText(true);
    Into->AddChildToVerticalBox(ArmorText)->SetPadding(FMargin(3, 4, 3, 0));

    Heading(TEXT("WORLD"), 5);
    auto* WorldReadout = WidgetTree->ConstructWidget<UBorder>();
    WorldReadout->SetBrush(BrassRect(1.8f, MutedGold, FLinearColor::Transparent, 10.f));
    WorldReadout->SetPadding(FMargin(10.f, 7.f));
    ClimateValue = Line(18);
    ClimateValue->SetAutoWrapText(true);
    WorldReadout->SetContent(ClimateValue);
    Into->AddChildToVerticalBox(WorldReadout)->SetPadding(FMargin(5, 1, 5, 2));
    HumidityBar = Meter(Into, FLinearColor(.33f, .62f, .64f), 4);

    Heading(TEXT("CHARACTER STATS"), 6);
    struct FRow
    {
        const TCHAR* Name;
        int32 Icon;
        int32 Allocation;
        FLinearColor Colour;
    };
    const FRow RowsToBuild[] = {
        {TEXT("HEALTH"), 0, int32(EEWStat::Vitality), FLinearColor(.72f, .12f, .10f)},
        {TEXT("STAMINA"), 1, int32(EEWStat::Endurance), FLinearColor(.86f, .68f, .12f)},
        {TEXT("OXYGEN"), -1, INDEX_NONE, FLinearColor(.18f, .46f, .80f)},
        {TEXT("FORTITUDE"), -1, int32(EEWStat::Fortitude), FLinearColor(.74f, .44f, .17f)},
        {TEXT("WEIGHT"), 4, int32(EEWStat::Strength), FLinearColor(.62f, .55f, .43f)},
        {TEXT("INTELLIGENCE"), -1, INDEX_NONE, FLinearColor::Transparent}
    };
    AllocValues.SetNum(UEWProgressionComponent::StatCount);
    AllocArrows.SetNum(UEWProgressionComponent::StatCount);
    AllocMinus.SetNum(UEWProgressionComponent::StatCount);
    PendingAttributes.Init(0, UEWProgressionComponent::StatCount);
    for (const auto& Definition : RowsToBuild)
    {
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* IconSize = WidgetTree->ConstructWidget<USizeBox>();
        IconSize->SetWidthOverride(40);
        IconSize->SetHeightOverride(42);
        if (Definition.Icon >= 0)
        {
            const int32 Key = 200 + Definition.Icon;
            if (!FallbackIcons.Contains(Key))
            {
                const TCHAR* Art = Definition.Allocation == int32(EEWStat::Vitality) ? TEXT("Health")
                    : Definition.Allocation == int32(EEWStat::Endurance) ? TEXT("Stamina")
                    : Definition.Allocation == int32(EEWStat::Strength) ? TEXT("Weight") : nullptr;
                auto* Texture = Art ? LoadObject<UTexture2D>(nullptr, *FString::Printf(
                    TEXT("/Game/Elitewake/UI/HUD/T_Maritime_%s.T_Maritime_%s"), Art, Art)) : nullptr;
                FallbackIcons.Add(Key, Texture ? Texture : EWHudIcon::Make(Definition.Icon, false));
            }
            auto* Icon = WidgetTree->ConstructWidget<UImage>();
            Icon->SetBrushFromTexture(FallbackIcons[Key]);
            IconSize->SetContent(Icon);
        }
        else
        {
            auto* Glyph = Line(16, MutedGold);
            Glyph->SetText(FText::FromString(Definition.Allocation == int32(EEWStat::Fortitude) ? TEXT("FRT")
                : Definition.Colour.A > 0.f ? TEXT("O2") : TEXT("INT")));
            Glyph->SetJustification(ETextJustify::Center);
            IconSize->SetContent(Glyph);
        }
        Row->AddChildToHorizontalBox(IconSize)->SetPadding(FMargin(2, 0, 9, 0));

        auto* Readout = WidgetTree->ConstructWidget<UVerticalBox>();
        auto* NameAndValue = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Name = Line(18);
        Name->SetText(FText::FromString(Definition.Name));
        auto* NameSlot = NameAndValue->AddChildToHorizontalBox(Name);
        NameSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        NameSlot->SetPadding(FMargin(0, 0, 8, 0));
        auto* Value = Line(16, Ivory);
        NameAndValue->AddChildToHorizontalBox(Value)->SetPadding(FMargin(6, 0, 0, 0));
        Readout->AddChildToVerticalBox(NameAndValue);
        TileValues.Add(Value);
        TileBars.Add(Definition.Colour.A > 0.f ? Meter(Readout, Definition.Colour, 8) : nullptr);
        auto* ReadoutSlot = Row->AddChildToHorizontalBox(Readout);
        ReadoutSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        ReadoutSlot->SetVerticalAlignment(VAlign_Center);
        ReadoutSlot->SetPadding(FMargin(0, 0, 14, 0));

        auto Step = [&](UButton* Button, const TCHAR* Text)
        {
            auto Style = Button->GetStyle();
            const auto Face = FLinearColor::FromSRGBColor(FColor(52, 31, 16));
            Style.SetNormal(BrassRect(1.8f, MutedGold, Face))
                .SetHovered(BrassRect(2.1f, CursorGold, Face))
                .SetPressed(BrassRect(1.8f, CursorGold, Face))
                .SetDisabled(BrassRect(1.6f, MutedGold, Face));
            Style.SetNormalPadding(FMargin(2)).SetPressedPadding(FMargin(2));
            Button->SetStyle(Style);
            auto* Glyph = Line(20, Ivory);
            Glyph->SetText(FText::FromString(Text));
            Glyph->SetJustification(ETextJustify::Center);
            Glyph->SetVisibility(ESlateVisibility::HitTestInvisible);
            auto* FaceAndLabel = WidgetTree->ConstructWidget<UOverlay>();
            auto* FaceSlot = FaceAndLabel->AddChildToOverlay(Button);
            FaceSlot->SetHorizontalAlignment(HAlign_Fill);
            FaceSlot->SetVerticalAlignment(VAlign_Fill);
            auto* GlyphSlot = FaceAndLabel->AddChildToOverlay(Glyph);
            GlyphSlot->SetHorizontalAlignment(HAlign_Center);
            GlyphSlot->SetVerticalAlignment(VAlign_Center);
            auto* Size = WidgetTree->ConstructWidget<USizeBox>();
            Size->SetWidthOverride(55);
            Size->SetHeightOverride(31);
            Size->SetContent(FaceAndLabel);
            Row->AddChildToHorizontalBox(Size)->SetVerticalAlignment(VAlign_Center);
        };
        auto* Minus = WidgetTree->ConstructWidget<UEWRecipeButton>(UEWRecipeButton::StaticClass(),
            FName(*FString::Printf(TEXT("AttributeMinus_%s"), Definition.Name)));
        Minus->SetIsEnabled(false);
        Step(Minus, TEXT("−"));
        auto* Invested = Line(18);
        Invested->SetText(FText::FromString(TEXT("—")));
        Invested->SetJustification(ETextJustify::Center);
        auto* Count = WidgetTree->ConstructWidget<USizeBox>();
        Count->SetWidthOverride(43);
        Count->SetContent(Invested);
        Row->AddChildToHorizontalBox(Count)->SetVerticalAlignment(VAlign_Center);
        auto* Plus = WidgetTree->ConstructWidget<UEWRecipeButton>(UEWRecipeButton::StaticClass(),
            FName(*FString::Printf(TEXT("AttributePlus_%s"), Definition.Name)));
        Step(Plus, TEXT("+"));
        Plus->SetIsEnabled(false);
        if (Definition.Allocation != INDEX_NONE)
        {
            Plus->Initialize(Definition.Allocation);
            Plus->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::SpendStat);
            AllocValues[Definition.Allocation] = Invested;
            AllocArrows[Definition.Allocation] = Plus;
            Minus->Initialize(Definition.Allocation);
            Minus->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::UndoStat);
            AllocMinus[Definition.Allocation] = Minus;
        }
        Into->AddChildToVerticalBox(Row)->SetPadding(FMargin(3, 0, 3, 1));
    }

    StatPrompt = Line(14, MutedGold);
    StatPrompt->SetAutoWrapText(true);
    Into->AddChildToVerticalBox(StatPrompt)->SetPadding(FMargin(3, 1, 3, 6));
    AttributeStatus = WidgetTree->ConstructWidget<UTextBlock>();
    StyleText(AttributeStatus, 14, MutedGold);
    AttributeStatus->SetAutoWrapText(true);
    Footer->AddChildToVerticalBox(AttributeStatus)->SetPadding(FMargin(12, 2));
    auto* AttributeActionRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    AttributeActions = AttributeActionRow;
    Footer->AddChildToVerticalBox(AttributeActionRow)->SetPadding(FMargin(12, 2, 12, 5));
    auto Action = [&](const TCHAR* Name, const TCHAR* Caption, bool bConfirm)
    {
        auto* Button = WidgetTree->ConstructWidget<UEWInventoryActionButton>(UEWInventoryActionButton::StaticClass(), FName(Name));
        StyleInventoryButton(Button);
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); StyleInventoryHeading(Label, 17);
        Label->SetText(FText::FromString(Caption)); Label->SetJustification(ETextJustify::Center);
        Button->SetContent(Label);
        AttributeActionRow->AddChildToHorizontalBox(Button)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        if (bConfirm) { AttributeConfirmButton = Button; Button->OnClicked.AddDynamic(this, &UEWInventoryWidget::ConfirmAttributeChanges); }
        else { AttributeCancelButton = Button; Button->OnClicked.AddDynamic(this, &UEWInventoryWidget::CancelAttributeChanges); }
    };
    Action(TEXT("AttributeConfirm"), TEXT("CONFIRM (Enter / A)"), true);
    Action(TEXT("AttributeCancel"), TEXT("CANCEL (Esc / B)"), false);
    AttributeActions->SetVisibility(ESlateVisibility::Collapsed);
    auto* Reset = WidgetTree->ConstructWidget<UEWInventoryActionButton>(UEWInventoryActionButton::StaticClass(), TEXT("ResetAttributePoints"));
    AttributeResetButton = Reset;
    Reset->OnClicked.AddDynamic(this, &UEWInventoryWidget::OpenAttributeReset);
    StyleInventoryButton(Reset);
    auto ResetStyle = Reset->GetStyle();
    auto ResetHover = Header;
    ResetHover.TintColor = FSlateColor(FLinearColor(1.08f, 1.08f, 1.08f, 1.f));
    ResetStyle.SetNormal(Header).SetHovered(ResetHover).SetPressed(Header);
    ResetStyle.SetDisabled(Header);
    Reset->SetStyle(ResetStyle);
    Reset->SetIsEnabled(false);
    auto* ResetText = WidgetTree->ConstructWidget<UTextBlock>();
    StyleInventoryHeading(ResetText, 22);
    ResetText->SetJustification(ETextJustify::Center);
    ResetText->SetText(NSLOCTEXT("Elitewake", "ResetStatPoints", "RESET STAT POINTS (5 GOLD)"));
    auto* ResetFace = WidgetTree->ConstructWidget<UOverlay>();
    auto* ResetPlate = ResetFace->AddChildToOverlay(Reset);
    ResetPlate->SetHorizontalAlignment(HAlign_Fill);
    ResetPlate->SetVerticalAlignment(VAlign_Fill);
    auto* ResetLabel = ResetFace->AddChildToOverlay(ResetText);
    ResetLabel->SetHorizontalAlignment(HAlign_Center);
    ResetLabel->SetVerticalAlignment(VAlign_Center);
    ResetLabel->SetPadding(FMargin(HeaderEndInset, 10.f));
    ResetText->SetVisibility(ESlateVisibility::HitTestInvisible);
    auto* ResetSize = WidgetTree->ConstructWidget<USizeBox>();
    ResetSize->SetMinDesiredHeight(59.f);
    ResetSize->SetContent(ResetFace);
    ResetSize->SetRenderTranslation(FVector2D(0.f, -8.f));
    auto* ResetFooterSlot = Footer->AddChildToVerticalBox(ResetSize);
    ResetFooterSlot->SetPadding(FMargin(11, 3, 11, 8));
    ResetFooterSlot->SetHorizontalAlignment(HAlign_Center);
}

namespace
{
    FString ItemNameOf(const UEWItemDefinition* Item)
	{
		return !Item ? FString() : (Item->DisplayName.IsEmpty() ? Item->ItemId.ToString() : Item->DisplayName.ToString());
	}
}

namespace
{
    // Match the display order so the inventory cursor, click targets, and equipped selection share indices.
    constexpr EEWEquipmentSlot ShownEquipment[] = {EEWEquipmentSlot::Head, EEWEquipmentSlot::Chest, EEWEquipmentSlot::Legs,
        EEWEquipmentSlot::Feet, EEWEquipmentSlot::Accessory, EEWEquipmentSlot::MainHand, EEWEquipmentSlot::OffHand, EEWEquipmentSlot::Hands};
    const TCHAR* const EquipmentNames[] = {TEXT("HAT"), TEXT("CHEST"), TEXT("LEGS"), TEXT("BOOTS"), TEXT("ACCESSORY"), TEXT("MAIN HAND"), TEXT("OFF HAND"), TEXT("HANDS")};

    int32 EquipmentOrder(EEWEquipmentSlot Slot)
    {
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(ShownEquipment); ++Index)
            if (ShownEquipment[Index] == Slot) return Index;
        return MAX_int32;
    }
}

void UEWInventoryWidget::RefreshInventory()
{
	if (!SummaryText || !ItemsBox)
	{
		return;
	}

	UEWInventoryComponent* Inventory = BoundInventory ? BoundInventory.Get() : ResolveInventory();
	if (!Inventory)
	{
		SummaryText->SetText(FText::FromString(TEXT("Inventory unavailable")));
        ItemsBox->ClearChildren(); EquippedBox->ClearChildren(); HandEquipmentBox->ClearChildren();
        Rows.Reset(); RowRings.Reset(); RowFreshness.Reset(); DisplayedEntries.Reset(); DisplayedEquipment.Reset();
        InventoryImages.Reset(); MaterialImages.Reset();
        SelectedIndex = INDEX_NONE; bShowingDetails = false;
        DetailsText->SetText(FText::FromString(TEXT("No item selected")));
        EquipmentActionButton->SetVisibility(ESlateVisibility::Collapsed);
        FoodActionButton->SetVisibility(ESlateVisibility::Collapsed);
        HotbarAssignments->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}

    RefreshSummary();
    UEWItemDefinition* PreviousItem = SelectedItem();
    const EEWEquipmentSlot PreviousSlot = SelectedEquipmentSlot();
    int32 PreviousOrdinal = 0;
    for (int32 i = 0; i < FMath::Min(SelectedIndex, DisplayedEntries.Num()); ++i)
        if (DisplayedEntries[i].ItemDefinition == PreviousItem) ++PreviousOrdinal;
    DisplayedEntries = Inventory->GetInventoryEntries();
    DisplayedEntries.RemoveAll([](const FEWInventoryEntry& Entry) { return !Entry.ItemDefinition || Entry.Quantity <= 0; });
    if (!InventoryFilter.IsEmpty())
        DisplayedEntries.RemoveAll([this](const FEWInventoryEntry& Entry) { return !ItemNameOf(Entry.ItemDefinition).Contains(InventoryFilter, ESearchCase::IgnoreCase); });
    if (bSortByName)
        DisplayedEntries.StableSort([](const FEWInventoryEntry& A, const FEWInventoryEntry& B) { return ItemNameOf(A.ItemDefinition) < ItemNameOf(B.ItemDefinition); });
    DisplayedEquipment = BoundEquipment ? BoundEquipment->GetEquipmentEntries() : TArray<FEWEquipmentEntry>();
    DisplayedEquipment.RemoveAll([](const FEWEquipmentEntry& Entry) { return Entry.Slot == EEWEquipmentSlot::None || !Entry.ItemDefinition; });
    for (int32 SlotIndex = 0; SlotIndex < 5; ++SlotIndex)
        if (!DisplayedEquipment.ContainsByPredicate([&](const FEWEquipmentEntry& Entry) { return Entry.Slot == ShownEquipment[SlotIndex]; }))
        {
            auto& Empty = DisplayedEquipment.AddDefaulted_GetRef();
            Empty.Slot = ShownEquipment[SlotIndex];
        }
    DisplayedEquipment.Sort([](const FEWEquipmentEntry& A, const FEWEquipmentEntry& B) { return EquipmentOrder(A.Slot) < EquipmentOrder(B.Slot); });
    int32 Match = INDEX_NONE, Ordinal = 0;
    for (int32 i = 0; i < DisplayedEntries.Num(); ++i)
        if (PreviousSlot == EEWEquipmentSlot::None && DisplayedEntries[i].ItemDefinition == PreviousItem && Ordinal++ == PreviousOrdinal) { Match = i; break; }
    if (PreviousSlot != EEWEquipmentSlot::None)
        for (int32 i=0; i<DisplayedEquipment.Num(); ++i) if (DisplayedEquipment[i].Slot == PreviousSlot) { Match = DisplayedEntries.Num()+i; break; }
    // A removed inventory stack clamps within Inventory; empty equipment positions must not steal its cursor.
    if (Match == INDEX_NONE && PreviousItem && PreviousSlot == EEWEquipmentSlot::None && !DisplayedEntries.IsEmpty())
        Match = FMath::Clamp(SelectedIndex, 0, DisplayedEntries.Num() - 1);
    const bool bHasItems = !DisplayedEntries.IsEmpty() || DisplayedEquipment.ContainsByPredicate([](const FEWEquipmentEntry& Entry) { return Entry.ItemDefinition != nullptr; });
    SelectedIndex = !bHasItems && PreviousSlot == EEWEquipmentSlot::None ? INDEX_NONE
        : (Match != INDEX_NONE ? Match : FMath::Clamp(SelectedIndex, 0, SelectionCount()-1));
    if (PreviousItem && SelectedItem() != PreviousItem) bShowingDetails = false;
    ItemsBox->ClearChildren();
    EquippedBox->ClearChildren();
    HandEquipmentBox->ClearChildren();
    InventoryImages.Reset();
    Rows.Reset();
    RowRings.Reset();
    RowFreshness.Reset();
    for (const FEWInventoryEntry& Entry : DisplayedEntries)
    {
        float Freshness = -1.f;
        if (Entry.ItemDefinition->FoodKind == EEWFoodKind::Berry && Entry.ItemDefinition->FreshLifetimeSeconds > 0.f)
            Freshness = FMath::Clamp(1.f - Entry.FoodAgeSeconds / Entry.ItemDefinition->FreshLifetimeSeconds, 0.f, 1.f);
        UImage* ItemImage = nullptr; UProgressBar* FreshBar = nullptr;
        // Counts only for things that stack; a lone tool needs none.
        const FString Count = Entry.ItemDefinition->MaxStackSize > 1 ? FString::Printf(TEXT("x%d"), Entry.Quantity) : FString();
        const FString Weight = FString::Printf(TEXT("%.1f kg"), Entry.ItemDefinition->UnitWeight * Entry.Quantity);
        UBorder* Tile = MakeSlotTile(Entry.ItemDefinition, Count, Freshness, ItemImage, FreshBar, Weight);
        if (ItemImage) InventoryImages.Add(Entry.ItemDefinition, ItemImage);
        UBorder* Ring = AddToGrid(ItemsBox, Tile);
        Rows.Add(Tile); RowRings.Add(Ring); RowFreshness.Add(FreshBar);
    }
    // The rest of the survivor's slots, empty, so the grid shows how much room is left (not while searching: the empties would only crowd the matches).
    if (InventoryFilter.IsEmpty())
        for (int32 Empty = Inventory->GetMaxSlotCount() - DisplayedEntries.Num(); Empty > 0; --Empty)
        {
            UImage* None = nullptr; UProgressBar* NoBar = nullptr;
            AddToGrid(ItemsBox, MakeSlotTile(nullptr, FString(), -1.f, None, NoBar));
        }
    // Keep hands reachable as existing equipment, below the five approved wearable positions.
    for (int32 SlotIndex = 0; SlotIndex < UE_ARRAY_COUNT(ShownEquipment); ++SlotIndex)
    {
        const FEWEquipmentEntry* Worn = DisplayedEquipment.FindByPredicate([&](const FEWEquipmentEntry& E) { return E.Slot == ShownEquipment[SlotIndex]; });
        if (SlotIndex >= 5 && !Worn)
            continue;
        auto* Grid = SlotIndex < 5 ? EquippedBox.Get() : HandEquipmentBox.Get();
        UImage* ItemImage = nullptr; UProgressBar* NoBar = nullptr;
        if (!Worn) { AddToGrid(Grid, MakeSlotTile(nullptr, FString(), -1.f, ItemImage, NoBar, FString(), EquipmentNames[SlotIndex])); continue; }
        UBorder* Tile = MakeSlotTile(Worn->ItemDefinition, FString(), -1.f, ItemImage, NoBar, FString(), EquipmentNames[SlotIndex]);
        Tile->SetToolTipText(Worn->ItemDefinition ? Worn->ItemDefinition->DisplayName : FText::FromString(FString(EquipmentNames[SlotIndex]) + TEXT(" — empty")));
        if (ItemImage && Worn->ItemDefinition) InventoryImages.Add(Worn->ItemDefinition, ItemImage);
        UBorder* Ring = AddToGrid(Grid, Tile);
        Rows.Add(Tile); RowRings.Add(Ring); RowFreshness.Add(nullptr);
    }
    HandEquipmentBox->SetVisibility(HandEquipmentBox->GetChildrenCount() ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (SelectionCount() == 0) bShowingDetails = false;
    UpdateSelection();
    RefreshCrafting();
}

void UEWInventoryWidget::ResetToInventoryPage()
{
    bAttributeRequestPending = false;
    AttributeResponseRevision = -1;
    CancelAttributeChanges();
    SelectedSection = 0; bCraftingOpen = false; StatFocus = INDEX_NONE; HotbarPick = INDEX_NONE; SelectedRecipeIndex = 0; bShowingDetails = false;
    InspectedRecipe = nullptr;
    bCraftRequestPending = false;
    RecipeScrollAxis = 0.f;
    InventoryFilter.Reset(); RecipeFilter.Reset(); bSortByName = false;
    if (SearchBox) SearchBox->SetText(FText::GetEmpty());
    if (RecipeSearchBox) RecipeSearchBox->SetText(FText::GetEmpty());
    if (SortButton) SortButton->SetBackgroundColor(FLinearColor(.07f, .085f, .1f));
    RefreshInventory();
}

void UEWInventoryWidget::SetInventorySearch(const FString& Text)
{
    if (Text == InventoryFilter) return;
    InventoryFilter = Text;
    if (SearchBox && SearchBox->GetText().ToString() != Text) SearchBox->SetText(FText::FromString(Text));
    bShowingDetails = false;
    RefreshInventory();
    if (ItemsScroll) ItemsScroll->ScrollToStart();
}

void UEWInventoryWidget::SetRecipeSearch(const FString& Text)
{
    if (Text == RecipeFilter) return;
    RecipeFilter = Text;
    if (RecipeSearchBox && RecipeSearchBox->GetText().ToString() != Text) RecipeSearchBox->SetText(FText::FromString(Text));
    SelectedRecipeIndex = 0;
    RefreshCrafting();
}

void UEWInventoryWidget::OnSearchCommitted(const FText& Text, ETextCommit::Type Method)
{
    // Enter or Escape hands the keyboard back to the menu.
    if (Method == ETextCommit::OnEnter || Method == ETextCommit::OnCleared) SetUserFocus(GetOwningPlayer());
}

void UEWInventoryWidget::ToggleSort()
{
    bSortByName = !bSortByName;
    if (SortButton) SortButton->SetBackgroundColor(bSortByName ? CursorGold * 1.45f : FLinearColor::White);
    RefreshInventory();
    SetUserFocus(GetOwningPlayer());
}

bool UEWInventoryWidget::IsSkillsShown() const
{
    return SkillsPanel && SkillsPanel->GetVisibility() == ESlateVisibility::Visible;
}

bool UEWInventoryWidget::IsTypingText() const
{
    return (SearchBox && SearchBox->HasKeyboardFocus()) || (RecipeSearchBox && RecipeSearchBox->HasKeyboardFocus()) || (CompanyPanel && CompanyPanel->IsTyping());
}

void UEWInventoryWidget::ToggleCrafting()
{
    if (bCraftingOpen) FocusInventory(); else FocusCrafting();
}
void UEWInventoryWidget::FocusCrafting()
{
    if (GetPendingAttributeTotal() > 0 || bResetConfirmation) CancelAttributeChanges();
    if (DisplayedRecipes.IsEmpty()) return;
    bCraftingOpen = true; bShowingDetails = false; HotbarPick = INDEX_NONE;
    RefreshCrafting();
    if (RecipeCards.IsValidIndex(SelectedRecipeIndex))
        CraftScroll->ScrollWidgetIntoView(RecipeCards[SelectedRecipeIndex].Tile, false);
    SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::FocusInventory()
{
    bCraftingOpen = false; bShowingDetails = false;
    InspectedRecipe = nullptr;
    RecipeScrollAxis = 0.f;
    RefreshCrafting();
    SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::SelectSection(int32 Index)
{
    CancelAttributeChanges();
    if (!SectionButtons.IsValidIndex(Index)) return;
    SelectedSection = Index; TabCursor = Index; bTabFocus = false; bCraftingOpen = false; bShowingDetails = false; StatFocus = INDEX_NONE; HotbarPick = INDEX_NONE;
    InspectedRecipe = nullptr;
    RecipeScrollAxis = 0.f;
    RefreshCrafting(); SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::SelectRecipe(int32 Index)
{
    if (!DisplayedRecipes.IsValidIndex(Index)) return;
    if (Index != SelectedRecipeIndex && InspectedRecipe)
        InspectedRecipe = DisplayedRecipes[Index];
    SelectedRecipeIndex = Index; SelectedSection = 0; bCraftingOpen = true; bShowingDetails = false; HotbarPick = INDEX_NONE;
    RefreshCrafting();
    if (RecipeCards.IsValidIndex(Index)) CraftScroll->ScrollWidgetIntoView(RecipeCards[Index].Tile, false);
    SetUserFocus(GetOwningPlayer());
}

void UEWInventoryWidget::InspectRecipe(int32 Index)
{
    if (!DisplayedRecipes.IsValidIndex(Index)) return;
    const bool bClose = bCraftingOpen && InspectedRecipe == DisplayedRecipes[Index];
    SelectRecipe(Index);
    InspectedRecipe = bClose ? nullptr : DisplayedRecipes[Index].Get();
    RecipeScrollAxis = 0.f;
    UpdateRecipeCards();
    if (InspectedRecipe) RecipeCards[Index].Scroll->ScrollToStart();
}

void UEWInventoryWidget::CraftRecipe(int32 Index)
{
    if (!DisplayedRecipes.IsValidIndex(Index)) return;
    SelectRecipe(Index);
    InspectedRecipe = DisplayedRecipes[Index];
    UpdateRecipeCards();
    PerformCraft();
}

UWidget* UEWInventoryWidget::GetRecipeTile(int32 Index) const
{
    return RecipeCards.IsValidIndex(Index) ? RecipeCards[Index].Tile.Get() : nullptr;
}

float UEWInventoryWidget::GetRecipeCardScrollOffset() const
{
    return IsRecipeInspected() && RecipeCards.IsValidIndex(SelectedRecipeIndex)
        ? RecipeCards[SelectedRecipeIndex].Scroll->GetScrollOffset() : 0.f;
}

FText UEWInventoryWidget::GetRecipeCardRequirements() const
{
    if (!IsRecipeInspected() || !RecipeCards.IsValidIndex(SelectedRecipeIndex)) return FText::GetEmpty();
    const auto& Card = RecipeCards[SelectedRecipeIndex];
    FString Text;
    for (const auto& Label : Card.Materials) Text += Label.Value->GetText().ToString() + TEXT("\n");
    Text += Card.Summary->GetText().ToString();
    return FText::FromString(Text);
}

void UEWInventoryWidget::ScrollRecipeCard(float Delta)
{
    if (!IsRecipeInspected() || !RecipeCards.IsValidIndex(SelectedRecipeIndex)) return;
    auto* Scroll = RecipeCards[SelectedRecipeIndex].Scroll.Get();
    Scroll->SetScrollOffset(FMath::Clamp(Scroll->GetScrollOffset() + Delta, 0.f, Scroll->GetScrollOffsetOfEnd()));
}

int32 UEWInventoryWidget::ItemColumns() const
{
    return InventoryColumns;
}
int32 UEWInventoryWidget::RecipeColumns() const
{
    return CraftingColumns;
}

void UEWInventoryWidget::MoveCursor(int32 Dx, int32 Dy)
{
    if (SelectedSection != 0) return;
    if (bCraftingOpen)
    {
        if (DisplayedRecipes.IsEmpty()) { FocusInventory(); return; }
        const int32 Columns = RecipeColumns();
        if (Dy < 0 && SelectedRecipeIndex < Columns) { FocusInventory(); return; }      // off the top row: back up to the inventory
        const int32 Next = FMath::Clamp(SelectedRecipeIndex + Dx + Dy * Columns, 0, DisplayedRecipes.Num() - 1);
        if (Next != SelectedRecipeIndex && CraftSecondsLeft <= 0.f) SelectRecipe(Next);
        return;
    }
    const int32 ItemCount = DisplayedEntries.Num();
    if (SelectionCount() == 0) { if (Dy > 0) FocusCrafting(); else if (Dy < 0) SetTabFocus(true); return; }
    if (SelectedIndex == INDEX_NONE) { Select(0); return; }
    if (SelectedIndex >= ItemCount)
    {
        // The equipment tiles: left and right (or up and down) step along them; up from the first returns to the last item.
        const int32 Step = Dx + Dy;
        if (SelectedIndex + Step < ItemCount)
        {
            if (ItemCount > 0 && Step < 0) Select(ItemCount - 1);
            else if (Step < 0) SetTabFocus(true);
        }
        else Select(SelectedIndex + Step);
        return;
    }
    const int32 Columns = ItemColumns();
    if (Dy > 0 && SelectedIndex + Columns >= ItemCount)
    {
        if (SelectedIndex / Columns == (ItemCount - 1) / Columns) FocusCrafting();   // past the last row: on into the crafting list
        else Select(ItemCount - 1);
        return;
    }
    if (Dy < 0 && SelectedIndex < Columns) { SetTabFocus(true); return; }      // off the top row: up to the tab bar
    Select(SelectedIndex + Dx + Dy * Columns);
}

void UEWInventoryWidget::ApplySectionVisibility()
{
    for (int32 Index = 0; Index < SectionButtons.Num(); ++Index)
    {
        const bool bActive = Index == SelectedSection;
        const bool bCursor = bTabFocus && Index == TabCursor;
        const auto GoldFace = FLinearColor::FromSRGBColor(FColor(233, 192, 113));
        FButtonStyle Style;
        Style.SetNormal(bActive ? BrassRect(1.5f, CursorGold, GoldFace, 8.f)
            : BrassRect(1.f, bCursor ? CursorGold : MutedGold * .55f, FLinearColor::Transparent, 8.f));
        Style.SetHovered(BrassRect(1.5f, CursorGold, bActive ? GoldFace : FLinearColor::Transparent, 8.f));
        Style.SetPressed(BrassRect(1.5f, CursorGold, bActive ? GoldFace * .82f : FLinearColor::Transparent, 8.f));
        Style.SetNormalPadding(FMargin(6, 2)).SetPressedPadding(FMargin(6, 2));
        SectionButtons[Index]->SetStyle(Style);
        auto* Label = SectionLabels[Index].Get();
        Label->SetColorAndOpacity(FSlateColor(bActive ? FLinearColor(.055f, .029f, .013f) : Ivory));
        Label->SetShadowColorAndOpacity(bActive ? FLinearColor::Transparent : FLinearColor(0, 0, 0, .9f));
        auto Font = Label->GetFont();
        Font.OutlineSettings.OutlineSize = bActive ? 0 : 1;
        Label->SetFont(Font);
    }
    const ESlateVisibility InventoryPage = SelectedSection == 0 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed;
    InventoryLayout->SetVisibility(InventoryPage);
    BrowserHost->SetVisibility(InventoryPage); SurvivorPanel->SetVisibility(InventoryPage); RightHost->SetVisibility(InventoryPage);
    MenuBackdrop->SetBrushColor(SelectedSection == 0 ? FLinearColor::Transparent : FLinearColor(.015f, .025f, .035f, .55f));
    SkillsPanel->SetVisibility(SelectedSection == 1 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    CompanyPanel->SetVisibility(SelectedSection == 2 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    TamesPanel->SetVisibility(SelectedSection == 3 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    JournalPanel->SetVisibility(SelectedSection == 4 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
}

void UEWInventoryWidget::RefreshCrafting()
{
    if (!CraftingBox || !ItemsScroll) return;
    ApplySectionVisibility();
    ItemPreview->GetParent()->SetVisibility(ESlateVisibility::Collapsed);
    UEWCraftingRecipe* Previous = GetShownRecipe();
    TArray<TObjectPtr<UEWCraftingRecipe>> Recipes;
    bool bAnyRecipe = false;
    if (BoundInventory) for (auto* Recipe : BoundInventory->GetAvailableRecipes())
        if (Recipe && Recipe->Output)
        {
            bAnyRecipe = true;
            if (RecipeFilter.IsEmpty() || ItemNameOf(Recipe->Output).Contains(RecipeFilter, ESearchCase::IgnoreCase)) Recipes.Add(Recipe);
        }
    if (Recipes != DisplayedRecipes || RecipeCards.Num() != Recipes.Num())
    {
        CraftingBox->ClearChildren();
        RecipeCards.Reset();
        HoveredRecipeIndex = INDEX_NONE;
        DisplayedRecipes = MoveTemp(Recipes);
        const int32 PreviousIndex = DisplayedRecipes.IndexOfByKey(Previous);
        SelectedRecipeIndex = PreviousIndex != INDEX_NONE ? PreviousIndex
            : FMath::Clamp(SelectedRecipeIndex, 0, DisplayedRecipes.Num() - 1);
        if (!DisplayedRecipes.Contains(InspectedRecipe)) InspectedRecipe = nullptr;
    }
    if (DisplayedRecipes.IsEmpty())
    {
        bCraftingOpen = false;
        InspectedRecipe = nullptr;
        UpdateSelection();
        CraftingBox->ClearChildren();
        auto* Empty = WidgetTree->ConstructWidget<UTextBlock>();
        StyleText(Empty, 17);
        Empty->SetText(FText::FromString(bAnyRecipe ? TEXT("No recipes match this search.") : TEXT("No recipes learned.")));
        CraftingBox->AddChildToVerticalBox(Empty)->SetPadding(FMargin(6));
        UpdateCraftActions();
        return;
    }

    SelectedRecipeIndex = FMath::Clamp(SelectedRecipeIndex, 0, DisplayedRecipes.Num() - 1);
    DetailsPanel->SetVisibility(bCraftingOpen ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    if (!bCraftingOpen) UpdateSelection();
    if (RecipeCards.IsEmpty())
    {
        auto* RecipeGrid = WidgetTree->ConstructWidget<UWrapBox>();
        RecipeGrid->SetInnerSlotPadding(FVector2D(RecipeGridGap, GridGap));
        RecipeGrid->SetExplicitWrapSize(true);
        RecipeGrid->SetWrapSize(CraftingColumns * (RecipeTileWidth + RecipeGridGap));
        CraftingBox->AddChildToVerticalBox(RecipeGrid);
        for (int32 Index = 0; Index < DisplayedRecipes.Num(); ++Index)
        {
            auto* Recipe = DisplayedRecipes[Index].Get();
            FEWRecipeCardView& Card = RecipeCards.AddDefaulted_GetRef();
            Card.Tile = WidgetTree->ConstructWidget<UEWCraftingRecipeTile>(
                UEWCraftingRecipeTile::StaticClass(), FName(*FString::Printf(TEXT("CraftRecipeTile_%d"), Index)));
            Card.Tile->RecipeIndex = Index;
            Card.Tile->SetPadding(FMargin(3));
            Card.Tile->OnInspect.AddDynamic(this, &UEWInventoryWidget::InspectRecipe);
            Card.Tile->OnCraft.AddDynamic(this, &UEWInventoryWidget::CraftRecipe);
            Card.Tile->OnHover.AddDynamic(this, &UEWInventoryWidget::HoverRecipe);
            Card.Faces = WidgetTree->ConstructWidget<UWidgetSwitcher>();
            Card.Tile->SetContent(Card.Faces);

            auto* Row = WidgetTree->ConstructWidget<UVerticalBox>();
            if (auto* Texture = ResolveIcon(Recipe->Output))
            {
                auto* Icon = WidgetTree->ConstructWidget<UImage>();
                Icon->SetBrushFromTexture(Texture);
                auto* Size = WidgetTree->ConstructWidget<USizeBox>();
                Size->SetWidthOverride(47);
                Size->SetHeightOverride(47);
                Size->SetContent(Icon);
                Row->AddChildToVerticalBox(Size)->SetHorizontalAlignment(HAlign_Center);
            }
            auto* Name = WidgetTree->ConstructWidget<UTextBlock>();
            const FText& DisplayName = Recipe->Output->DisplayName;
            // Keep a long compound caption readable at the approved card width.
            Name->SetText(DisplayName.ToString() == TEXT("Gunpowder")
                ? NSLOCTEXT("Elitewake", "GunpowderTileCaption", "Gun-\npowder") : DisplayName);
            Name->SetJustification(ETextJustify::Center);
            Name->SetAutoWrapText(true);
            Name->SetWrapTextAt(RecipeTileWidth - 2.f);
            Name->SetWrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping);
            Name->SetClipping(EWidgetClipping::ClipToBounds);
            StyleText(Name, 13, Ivory, true);
            auto* Caption = WidgetTree->ConstructWidget<USizeBox>();
            Caption->SetHeightOverride(73.f);
            Caption->SetContent(Name);
            Row->AddChildToVerticalBox(Caption);
            Card.Faces->AddChild(Row);

            Card.Scroll = WidgetTree->ConstructWidget<UScrollBox>();
            StyleInventoryScroll(Card.Scroll);
            Card.Scroll->SetScrollbarThickness(FVector2D(3.f, 3.f));
            Card.Scroll->SetScrollbarPadding(FMargin(0));
            Card.Scroll->SetConsumeMouseWheel(EConsumeMouseWheel::Always);
            auto* Requirements = WidgetTree->ConstructWidget<UVerticalBox>();
            Card.Scroll->AddChild(Requirements);
            for (const auto& Cost : RecipeCosts(*Recipe))
            {
                auto* MaterialRow = WidgetTree->ConstructWidget<UVerticalBox>();
                auto* Icon = WidgetTree->ConstructWidget<UImage>();
                Icon->SetBrushFromTexture(ResolveIcon(Cost.Key));
                auto* IconSize = WidgetTree->ConstructWidget<USizeBox>();
                IconSize->SetWidthOverride(23);
                IconSize->SetHeightOverride(23);
                IconSize->SetContent(Icon);
                MaterialRow->AddChildToVerticalBox(IconSize)->SetHorizontalAlignment(HAlign_Center);
                auto* MaterialLabel = WidgetTree->ConstructWidget<UTextBlock>();
                MaterialLabel->SetAutoWrapText(true);
                StyleText(MaterialLabel, 13);
                MaterialRow->AddChildToVerticalBox(MaterialLabel);
                Requirements->AddChildToVerticalBox(MaterialRow)->SetPadding(FMargin(0, 0, 0, 6));
                Card.Materials.Add(Cost.Key, MaterialLabel);
                Card.Icons.Add(Cost.Key, Icon);
            }
            Card.Summary = WidgetTree->ConstructWidget<UTextBlock>();
            Card.Summary->SetAutoWrapText(true);
            StyleText(Card.Summary, 13, MutedGold);
            Requirements->AddChildToVerticalBox(Card.Summary);
            Card.Faces->AddChild(Card.Scroll);
            auto* TileSize = WidgetTree->ConstructWidget<USizeBox>();
            TileSize->SetWidthOverride(RecipeTileWidth);
            TileSize->SetHeightOverride(133);
            TileSize->SetContent(Card.Tile);
            RecipeGrid->AddChildToWrapBox(TileSize);
        }
    }
    UpdateRecipeCards();
    UpdateCraftActions();
}

void UEWInventoryWidget::UpdateRecipeCards()
{
    MaterialImages.Reset();
    if (!BoundInventory) return;
    for (int32 Index = 0; Index < RecipeCards.Num(); ++Index)
    {
        auto& Card = RecipeCards[Index];
        auto* Recipe = DisplayedRecipes[Index].Get();
        const bool bSelected = bCraftingOpen && SelectedRecipeIndex == Index;
        Card.Tile->SetBrush(BrassRect(bSelected || HoveredRecipeIndex == Index ? 2.5f : SlotStroke,
            bSelected || HoveredRecipeIndex == Index ? CursorGold : MutedGold));
        Card.Faces->SetActiveWidgetIndex(bSelected && InspectedRecipe == Recipe ? 1 : 0);
        if (!bSelected) continue;
        const auto Costs = RecipeCosts(*Recipe);
        for (const auto& Label : Card.Materials)
        {
            const int32 Owned = BoundInventory->GetItemCount(Label.Key);
            const int64 Required = Costs.FindRef(Label.Key);
            Label.Value->SetText(FText::Format(NSLOCTEXT("Elitewake", "RecipeCardMaterial", "{0}\nNeed {2}\nHave {1}"),
                Label.Key->DisplayName, Owned, Required));
            Label.Value->SetColorAndOpacity(FSlateColor(Owned >= Required ? Ivory : FLinearColor(1.f, .57f, .46f)));
        }
        Card.Summary->SetText(FText::Format(NSLOCTEXT("Elitewake", "RecipeCardSummary", "{0}s {1}\n{2}"),
            FText::AsNumber(Recipe->CraftSeconds),
            Recipe->bNeedsFire ? NSLOCTEXT("Elitewake", "CraftAtFire", "Lit campfire") : NSLOCTEXT("Elitewake", "CraftByHand", "Hand"),
            CraftReadinessText(bCraftRequestPending || CraftSecondsLeft > 0.f ? EEWCraftResult::Busy : BoundInventory->GetCraftReadiness(Recipe))));
        if (bSelected) MaterialImages = Card.Icons;
    }
}

void UEWInventoryWidget::UpdateCraftActions()
{
    CraftActions->ClearChildren();
    CraftActions->SetVisibility(ESlateVisibility::Collapsed);
    CraftButton = nullptr;
    CraftBar = nullptr;
    CraftBarText = nullptr;
    if (!bCraftingOpen) return;

    auto* Recipe = DisplayedRecipes[SelectedRecipeIndex].Get();
    const auto Readiness = bCraftRequestPending || CraftSecondsLeft > 0.f ? EEWCraftResult::Busy : BoundInventory->GetCraftReadiness(Recipe);
    ShownCraftReadiness = Readiness;
    auto* Actions = WidgetTree->ConstructWidget<UHorizontalBox>();
    CraftStatus = WidgetTree->ConstructWidget<UTextBlock>();
    CraftStatus->SetAutoWrapText(true);
    CraftStatus->SetText(FText::Format(NSLOCTEXT("Elitewake", "CraftStatusWithInspect", "{0} · {1}\nR / X inspect"),
        Recipe->Output->DisplayName, CraftReadinessText(Readiness)));
    StyleText(CraftStatus, 17, MutedGold);
    auto* StatusSlot = Actions->AddChildToHorizontalBox(CraftStatus);
    StatusSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    StatusSlot->SetVerticalAlignment(VAlign_Center);
    CraftButton = WidgetTree->ConstructWidget<UEWInventoryActionButton>();
    StyleInventoryButton(CraftButton);
    auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
    Label->SetText(NSLOCTEXT("Elitewake", "CraftOne", "Craft one (Enter/A)"));
    StyleInventoryHeading(Label, 17, Readiness == EEWCraftResult::Success ? Ivory : MutedGold);
    Label->SetVisibility(ESlateVisibility::HitTestInvisible);
    CraftButton->SetIsEnabled(Readiness == EEWCraftResult::Success);
    CraftButton->OnClicked.AddDynamic(this, &UEWInventoryWidget::PerformCraft);
    auto* CraftFace = WidgetTree->ConstructWidget<UOverlay>();
    auto* ButtonSlot = CraftFace->AddChildToOverlay(CraftButton);
    ButtonSlot->SetHorizontalAlignment(HAlign_Fill);
    ButtonSlot->SetVerticalAlignment(VAlign_Fill);
    auto* CaptionSlot = CraftFace->AddChildToOverlay(Label);
    CaptionSlot->SetPadding(FMargin(18, 8));
    CaptionSlot->SetHorizontalAlignment(HAlign_Center);
    CaptionSlot->SetVerticalAlignment(VAlign_Center);
    Actions->AddChildToHorizontalBox(CraftFace)->SetPadding(FMargin(10, 0, 5, 0));
    CraftActions->AddChildToVerticalBox(Actions);
    CraftActions->SetVisibility(ESlateVisibility::Visible);

    if (Recipe->CraftSeconds > .02f || CraftSecondsLeft > 0.f)
    {
        CraftBar = WidgetTree->ConstructWidget<UProgressBar>();
        CraftBar->SetFillColorAndOpacity(FLinearColor(.9f, .7f, .25f));
        CraftBar->SetPercent(GetCraftProgress());
        auto* CraftBarSize = WidgetTree->ConstructWidget<USizeBox>();
        CraftBarSize->SetHeightOverride(5);
        CraftBarSize->SetContent(CraftBar);
        CraftActions->AddChildToVerticalBox(CraftBarSize)->SetPadding(FMargin(0, 4, 0, 2));
        CraftBarText = WidgetTree->ConstructWidget<UTextBlock>();
        StyleText(CraftBarText, 15, MutedGold);
        CraftBarText->SetText(CraftSecondsLeft > 0.f ? FText::Format(NSLOCTEXT("Elitewake", "CraftTimeLeft", "Crafting... {0} s"), FMath::CeilToInt(CraftSecondsLeft))
            : FText::Format(NSLOCTEXT("Elitewake", "CraftTime", "Takes {0} s"), FMath::RoundToInt(Recipe->CraftSeconds)));
        CraftActions->AddChildToVerticalBox(CraftBarText)->SetPadding(FMargin(14, 0, 0, 0));
    }
}

UBorder* UEWInventoryWidget::MakeSlotTile(UEWItemDefinition* Item, const FString& Corner, float Freshness, UImage*& Image, UProgressBar*& FreshBar, const FString& Weight, const FString& EmptyLabel)
{
    Image = nullptr; FreshBar = nullptr;
    auto* Tile = WidgetTree->ConstructWidget<UBorder>();
    Tile->SetPadding(FMargin(6, 3));
    Tile->SetBrush(BrassRect(SlotStroke));
    if (!Item)
    {
        if (!EmptyLabel.IsEmpty())
        {
            auto* SlotName = WidgetTree->ConstructWidget<UTextBlock>(); SlotName->SetText(FText::FromString(EmptyLabel)); SlotName->SetJustification(ETextJustify::Center);
            StyleText(SlotName, 14);
            auto* Contents = WidgetTree->ConstructWidget<UVerticalBox>();
            auto* IconSpace = WidgetTree->ConstructWidget<USizeBox>();
            IconSpace->SetHeightOverride(42);
            Contents->AddChildToVerticalBox(IconSpace);
            Contents->AddChildToVerticalBox(SlotName)->SetPadding(FMargin(0, 2, 0, 1));
            Tile->SetContent(Contents);
        }
        return Tile;
    }
    auto* Contents = WidgetTree->ConstructWidget<UVerticalBox>();
    Tile->SetContent(Contents);
    auto* ArtRow = WidgetTree->ConstructWidget<UHorizontalBox>();
    Contents->AddChildToVerticalBox(ArtRow);
    Image = WidgetTree->ConstructWidget<UImage>(); Image->SetBrushFromTexture(ResolveIcon(Item));
    auto* IconSize = WidgetTree->ConstructWidget<USizeBox>(); IconSize->SetWidthOverride(42); IconSize->SetHeightOverride(42);
    IconSize->SetContent(Image);
    auto* IconSlot = ArtRow->AddChildToHorizontalBox(IconSize);
    IconSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    IconSlot->SetHorizontalAlignment(HAlign_Center);
    if (!Corner.IsEmpty())
    {
        auto* Count = WidgetTree->ConstructWidget<UTextBlock>();
        Count->SetText(FText::FromString(Corner));
        StyleText(Count, 13);
        ArtRow->AddChildToHorizontalBox(Count)->SetVerticalAlignment(VAlign_Top);
    }

    auto* Name = WidgetTree->ConstructWidget<UTextBlock>();
    Name->SetText(!EmptyLabel.IsEmpty() ? FText::FromString(EmptyLabel)
        : Item->DisplayName.IsEmpty() ? FText::FromName(Item->ItemId) : Item->DisplayName);
    StyleText(Name, 14);
    Name->SetJustification(ETextJustify::Center);
    Name->SetClipping(EWidgetClipping::ClipToBounds);
    Name->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
    Contents->AddChildToVerticalBox(Name)->SetPadding(FMargin(0, 2, 0, 1));
    if (!Weight.IsEmpty()) Tile->SetToolTipText(FText::Format(NSLOCTEXT("Elitewake", "InventoryTileWeight", "{0} · {1}"), Item->DisplayName, FText::FromString(Weight)));
    if (Freshness >= 0.f)
    {
        FreshBar = WidgetTree->ConstructWidget<UProgressBar>();
        FreshBar->SetPercent(Freshness); FreshBar->SetFillColorAndOpacity(FLinearColor(.25f,.8f,.35f));
        auto* BarSize = WidgetTree->ConstructWidget<USizeBox>(); BarSize->SetHeightOverride(4); BarSize->SetContent(FreshBar);
        Contents->AddChildToVerticalBox(BarSize);
    }
    return Tile;
}

UBorder* UEWInventoryWidget::AddToGrid(UWrapBox* Grid, UBorder* Tile)
{
    // The ring around a tile is the controller cursor: clear until the tile is picked, then gold.
    auto* Ring = WidgetTree->ConstructWidget<UBorder>(); Ring->SetPadding(FMargin(1));
    Ring->SetBrushColor(FLinearColor::Transparent);
    Ring->SetContent(Tile);
    auto* Size = WidgetTree->ConstructWidget<USizeBox>();
    const bool bGear = Grid != ItemsBox;
    Size->SetWidthOverride(bGear ? 120.f : SlotTileWidth);
    Size->SetHeightOverride(bGear ? 85.f : SlotTileHeight);
    Size->SetContent(Ring);
    Grid->AddChildToWrapBox(Size);
    return Ring;
}

FText UEWInventoryWidget::GetLevelText() const
{
    return LevelValue ? LevelValue->GetText() : FText::GetEmpty();
}
bool UEWInventoryWidget::IsStatArrowEnabled(int32 StatIndex) const
{
    return AllocArrows.IsValidIndex(StatIndex) && AllocArrows[StatIndex]->GetIsEnabled();
}
float UEWInventoryWidget::GetStatArrowOpacity(int32 StatIndex) const
{
    return AllocArrows.IsValidIndex(StatIndex) ? AllocArrows[StatIndex]->GetRenderOpacity() : 0.f;
}
void UEWInventoryWidget::SetStatFocus(int32 StatIndex)
{
    StatFocus = StatIndex >= 0 && StatIndex < UEWProgressionComponent::StatCount && SelectedSection == 0 ? StatIndex : INDEX_NONE;
    RefreshProgression();
    if (SurvivorScroll && AllocArrows.IsValidIndex(StatFocus)) SurvivorScroll->ScrollWidgetIntoView(AllocArrows[StatFocus], false);
}

void UEWInventoryWidget::NavigateAttributeFocus(int32 Direction)
{
    // Follow the visible row order, skipping the two attributes whose effects are not approved.
    constexpr int32 Order[] = {0, 1, 3, 2};
    int32 At = 0;
    for (int32 Index = 0; Index < 4; ++Index) if (Order[Index] == StatFocus) At = Index;
    SetStatFocus(Order[(At + (Direction > 0 ? 1 : 3)) % 4]);
}
int32 UEWInventoryWidget::GetPendingAttributeTotal() const
{
    int32 Total = 0;
    for (int32 Points : PendingAttributes) Total += Points;
    return Total;
}

void UEWInventoryWidget::SpendStat(int32 StatIndex)
{
    RefreshProgression();
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    if (!Progress || bAttributeRequestPending || bResetConfirmation || !PendingAttributes.IsValidIndex(StatIndex)
        || Progress->GetUnspentPoints() <= GetPendingAttributeTotal()) return;
    AttributeDraftRevision = Progress->GetAttributeRevision();
    if (bCraftingOpen) FocusInventory();
    ++PendingAttributes[StatIndex];
    StatFocus = StatIndex;
    bCraftingOpen = false;
    if (AttributeStatus) AttributeStatus->SetText(NSLOCTEXT("Elitewake", "AttributeDraft", "Pending only. Confirm to save, or cancel to keep your current attributes."));
    RefreshProgression();
}

void UEWInventoryWidget::UndoStat(int32 StatIndex)
{
    if (bAttributeRequestPending || bResetConfirmation || !PendingAttributes.IsValidIndex(StatIndex) || PendingAttributes[StatIndex] <= 0) return;
    --PendingAttributes[StatIndex];
    StatFocus = StatIndex;
    RefreshProgression();
}

void UEWInventoryWidget::CancelAttributeChanges()
{
    PendingAttributes.Init(0, UEWProgressionComponent::StatCount);
    bResetConfirmation = false;
    StatFocus = INDEX_NONE;
    if (AttributeStatus) AttributeStatus->SetText(FText::GetEmpty());
    RefreshProgression();
}

void UEWInventoryWidget::OpenAttributeReset()
{
    RefreshProgression();
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    const auto* Wallet = Character ? Character->GetWalletComponent() : nullptr;
    if (!Progress || bAttributeRequestPending || GetPendingAttributeTotal() > 0) return;
    if (!Wallet || !Wallet->CanAfford(UEWProgressionComponent::AttributeResetCopper))
    {
        AttributeStatus->SetText(NSLOCTEXT("Elitewake", "ResetInsufficient", "You need 5 gold to reset attribute points."));
        RefreshProgression();
        return;
    }
    int32 Spent = 0;
    for (int32 Points : Progress->GetAllStatPoints()) Spent += Points;
    if (Spent <= 0) return;
    AttributeDraftRevision = Progress->GetAttributeRevision();
    bResetConfirmation = true;
    AttributeStatus->SetText(FText::Format(NSLOCTEXT("Elitewake", "ResetAttributeConfirm", "Reset {0} invested attribute points for 5 GOLD? Constellation skills stay unchanged. Confirm or cancel."), Spent));
    SetUserFocus(GetOwningPlayer());
    RefreshProgression();
}

void UEWInventoryWidget::ConfirmAttributeChanges()
{
    if (bAttributeRequestPending || (!bResetConfirmation && GetPendingAttributeTotal() <= 0)) return;
    auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!Controller) return;
    bAttributeRequestPending = true;
    AttributeResponseRevision = -1;
    const bool bReset = bResetConfirmation;
    bResetConfirmation = false;
    AttributeStatus->SetText(NSLOCTEXT("Elitewake", "AttributeSaving", "Saving attribute changes..."));
    RefreshProgression();
    if (bReset) Controller->RequestResetAttributes(AttributeDraftRevision);
    else Controller->RequestCommitAttributes(PendingAttributes, AttributeDraftRevision);
}

void UEWInventoryWidget::ShowAttributeResult(EEWAttributeResult Result, int64 Revision)
{
    PendingAttributes.Init(0, UEWProgressionComponent::StatCount);
    bResetConfirmation = false;
    StatFocus = INDEX_NONE;
    AttributeResponseRevision = Revision;
    bAttributeRequestPending = Result == EEWAttributeResult::Success;
    const TCHAR* Message = TEXT("Attribute changes saved.");
    switch (Result)
    {
    case EEWAttributeResult::Success: break;
    case EEWAttributeResult::Stale: Message = TEXT("Your attributes changed. Review the current values and try again."); break;
    case EEWAttributeResult::NotEnoughGold: Message = TEXT("You need 5 gold. Nothing was charged."); break;
    case EEWAttributeResult::NothingToReset: Message = TEXT("There are no invested attribute points to reset."); break;
    case EEWAttributeResult::NotEnoughPoints: Message = TEXT("Not enough unspent attribute points. Nothing was spent."); break;
    case EEWAttributeResult::SaveFailed: Message = TEXT("Could not save. Return to land and try again. Points and money are unchanged."); break;
    default: Message = TEXT("Attribute changes were not accepted. Nothing was spent."); break;
    }
    if (AttributeStatus) AttributeStatus->SetText(FText::FromString(Message));
    RefreshProgression();
}

void UEWInventoryWidget::RefreshProgression()
{
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    if (!Progress || !LevelValue || !LevelBar || !PointsValue || AllocArrows.Num() != UEWProgressionComponent::StatCount) return;
    const int64 Revision = Progress->GetAttributeRevision();
    if (bAttributeRequestPending && AttributeResponseRevision >= 0 && Revision >= AttributeResponseRevision)
        bAttributeRequestPending = false;
    if (!bAttributeRequestPending && AttributeDraftRevision != Revision)
    {
        if (GetPendingAttributeTotal() > 0 || bResetConfirmation)
        {
            PendingAttributes.Init(0, UEWProgressionComponent::StatCount);
            bResetConfirmation = false;
            if (AttributeStatus) AttributeStatus->SetText(NSLOCTEXT("Elitewake", "AttributeDraftStale", "Your attributes changed. Review the current values and choose again."));
        }
        AttributeDraftRevision = Revision;
    }
    LevelValue->SetText(FText::Format(NSLOCTEXT("Elitewake", "LevelFormat", "LEVEL {0}"), Progress->GetLevel()));
    LevelBar->SetPercent(Progress->IsAtMaxLevel() ? 1.f : FMath::Clamp(float(Progress->GetExperience()) / FMath::Max(1, Progress->GetExperienceForNextLevel()), 0.f, 1.f));
    const int32 Pending = GetPendingAttributeTotal();
    const int32 Points = FMath::Max(0, Progress->GetUnspentPoints() - Pending);
    PointsValue->SetText(Progress->IsAtMaxLevel()
        ? FText::Format(NSLOCTEXT("Elitewake", "MaxLevelPoints", "Highest level reached   ·   {0} unspent stat points"), Points)
        : FText::Format(NSLOCTEXT("Elitewake", "PointsFormat", "Experience {0} / {1}     Stat points to spend: {2}"), Progress->GetExperience(), Progress->GetExperienceForNextLevel(), Points));
    const bool bHasCommitted = Progress->GetAllStatPoints().ContainsByPredicate([](int32 Value) { return Value > 0; });
    if (StatPrompt)
    {
        StatPrompt->SetText(Progress->GetUnspentPoints() > 0 || Pending > 0 || bHasCommitted
            ? NSLOCTEXT("Elitewake", "AttributeDraftKeys", "C / RT selects. Left / Right edits; Enter / A confirms; Esc / B cancels. R / X opens reset.") : FText::GetEmpty());
        StatPrompt->SetVisibility(StatPrompt->GetText().IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    }
    int64 Committed = 0;
    for (int32 Stat = 0; Stat < UEWProgressionComponent::StatCount; ++Stat)
    {
        const auto Which = static_cast<EEWStat>(Stat);
        const int32 Existing = Progress->GetStatPoints(Which);
        Committed += Existing;
        const int32 Draft = GetPendingAttributePoints(Stat);
        AllocValues[Stat]->SetText(FText::AsNumber(Existing + Draft));
        AllocValues[Stat]->SetToolTipText(FText::Format(NSLOCTEXT("Elitewake", "AttributeInvestedDraft", "{0} committed, {1} pending"), Existing, Draft));
        AllocValues[Stat]->SetColorAndOpacity(FSlateColor(Draft > 0 || Stat == StatFocus ? CursorGold : Ivory));
        AllocArrows[Stat]->SetToolTipText(Progress->StatEffect(Which));
        const bool bLive = Points > 0 && !bAttributeRequestPending && !bResetConfirmation;
        AllocArrows[Stat]->SetIsEnabled(bLive);
        AllocMinus[Stat]->SetIsEnabled(Draft > 0 && !bAttributeRequestPending && !bResetConfirmation);
        AllocMinus[Stat]->SetToolTipText(NSLOCTEXT("Elitewake", "AttributeUndoPending", "Undo one pending point. Committed points require the paid reset."));
        AllocArrows[Stat]->SetRenderOpacity(bLive ? 1.f : .83f);
        AllocArrows[Stat]->SetBackgroundColor(Stat == StatFocus ? CursorGold * 1.4f : FLinearColor::White);
    }
    if (AttributeResetButton)
    {
        AttributeResetButton->SetIsEnabled(Committed > 0 && Pending == 0 && !bAttributeRequestPending && !bResetConfirmation);
        const auto* Wallet = Character->GetWalletComponent();
        AttributeResetButton->SetToolTipText(FText::FromString(FString::Printf(TEXT("Refund committed attribute points for 5 gold. Purse: %s. Constellation skills are preserved."),
            *UEWWalletComponent::Format(Wallet ? Wallet->GetCopper() : 0))));
    }
    if (AttributeActions) AttributeActions->SetVisibility(Pending > 0 || bResetConfirmation ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (AttributeConfirmButton) AttributeConfirmButton->SetIsEnabled(!bAttributeRequestPending);
    if (AttributeCancelButton) AttributeCancelButton->SetIsEnabled(!bAttributeRequestPending);
    if (AttributeStatus) AttributeStatus->SetVisibility(AttributeStatus->GetText().IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
}

void UEWInventoryWidget::PerformCraft()
{
    if (!DisplayedRecipes.IsValidIndex(SelectedRecipeIndex)) return;
    if (!IsCraftActionEnabled()) { UpdateCraftActions(); return; }
    if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer()))
    {
        bCraftRequestPending = true;
        UpdateRecipeCards();
        UpdateCraftActions();
        Controller->RequestCraft(DisplayedRecipes[SelectedRecipeIndex]);
    }
}
bool UEWInventoryWidget::IsCraftActionEnabled() const
{
    return bCraftingOpen && CraftButton && CraftButton->GetIsEnabled() && CraftSecondsLeft <= 0.f && !bCraftRequestPending;
}
void UEWInventoryWidget::ShowCraftStarted(UEWCraftingRecipe* Recipe, float Seconds)
{
    bCraftRequestPending = false;
    CraftSecondsTotal = CraftSecondsLeft = FMath::Max(0.f, Seconds);
    if (EquipmentResultText && Recipe && Recipe->Output && Seconds > .02f)
        EquipmentResultText->SetText(FText::Format(NSLOCTEXT("Elitewake", "CraftingNow", "Crafting {0}..."), Recipe->Output->DisplayName));
    RefreshCrafting();
}
void UEWInventoryWidget::HoverRecipe(int32 Index)
{
    HoveredRecipeIndex = Index;
    UpdateRecipeCards();
}

UHorizontalBox* UEWInventoryWidget::MakeItemRow(UEWItemDefinition* Item, UWidget* Label, UImage*& Image)
{
    auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
    Image = nullptr;
    if (Item) if (auto* Texture = ResolveIcon(Item))
    {
        Image = WidgetTree->ConstructWidget<UImage>(); Image->SetBrushFromTexture(Texture);
        auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(64); Size->SetHeightOverride(64);
        Size->SetContent(Image);
        auto* ImageSlot = Row->AddChildToHorizontalBox(Size);
        ImageSlot->SetPadding(FMargin(0,0,8,0)); ImageSlot->SetVerticalAlignment(VAlign_Center);
    }
    auto* LabelSlot=Row->AddChildToHorizontalBox(Label); LabelSlot->SetVerticalAlignment(VAlign_Center);
    LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    return Row;
}
UTexture2D* UEWInventoryWidget::GetDisplayedInventoryIcon(UEWItemDefinition* Item) const
{
    const auto* Image = InventoryImages.Find(Item);
    return Image && *Image ? Cast<UTexture2D>((*Image)->GetBrush().GetResourceObject()) : nullptr;
}
UTexture2D* UEWInventoryWidget::GetDisplayedMaterialIcon(UEWItemDefinition* Item) const
{
    const auto* Image = MaterialImages.Find(Item);
    return bCraftingOpen && Image && *Image ? Cast<UTexture2D>((*Image)->GetBrush().GetResourceObject()) : nullptr;
}
void UEWInventoryWidget::ShowCraftResult(EEWCraftResult Result)
{
    bCraftRequestPending = false;
    CraftSecondsLeft = CraftSecondsTotal = 0.f;
    FString Message;
    switch (Result)
    {
        case EEWCraftResult::Success: Message=TEXT("Item crafted"); break;
        case EEWCraftResult::MissingIngredients: Message=TEXT("Not enough materials"); break;
        case EEWCraftResult::InventoryFull: Message=TEXT("Make room in your inventory"); break;
        case EEWCraftResult::NeedsFire: Message=TEXT("Cook it by a lit campfire"); break;
        case EEWCraftResult::Locked: Message=TEXT("Recipe is not unlocked"); break;
        default: Message=TEXT("Crafting could not be completed"); break;
    }
    if (EquipmentResultText) EquipmentResultText->SetText(FText::FromString(Message));
    if (bCraftingOpen) RefreshCrafting();
}

void UEWInventoryWidget::RefreshSummary()
{
    UEWInventoryComponent* Inventory = BoundInventory.Get();
    if (!Inventory || !SummaryText) return;
    float MaxWeight = 0.0f;
	if (const AEWCharacter* Character = Cast<AEWCharacter>(GetOwningPlayerPawn()))
	{
		if (const UEWSurvivalComponent* Survival = Character->GetSurvivalComponent())
		{
			MaxWeight = Survival->GetMaxCarryWeight();
		}
	}
    const float Carried = Inventory->GetTotalWeight() + (BoundEquipment ? BoundEquipment->GetTotalWeight() : 0.f);
	SummaryText->SetText(FText::Format(NSLOCTEXT("Elitewake", "InventorySlotCount", "Slots {0} / {1}"),
		Inventory->GetUsedSlotCount(), Inventory->GetMaxSlotCount()));
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Survival = Character ? Character->GetSurvivalComponent() : nullptr;
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    if (Survival && TileValues.Num() == 6)
    {
        const float Max[] = {Survival->GetMaxHealth(), Survival->GetMaxStamina(), UEWSurvivalComponent::MaxBreathSeconds};
        const float Now[] = {Survival->GetHealth(), Survival->GetStamina(), Survival->GetBreathSeconds()};
        for (int32 i = 0; i < 3; ++i)
        {
            TileValues[i]->SetText(FText::FromString(i < 2 ? FString::Printf(TEXT("%.0f / %.0f"), Now[i], Max[i])
                : FString::Printf(TEXT("%.0f / %.0f s"), Now[i], Max[i])));
            TileBars[i]->SetPercent(Max[i] > 0.f ? FMath::Clamp(Now[i] / Max[i], 0.f, 1.f) : 0.f);
        }
        const float ClimateResist = Progress ? FMath::Min(.6f, Progress->GetStatPoints(EEWStat::Fortitude) * Progress->ResistPerFortitude) : 0.f;
        TileValues[3]->SetText(FText::FromString(FString::Printf(TEXT("%.0f%% climate protection"), ClimateResist * 100.f)));
        TileBars[3]->SetPercent(ClimateResist / .6f);
        TileValues[4]->SetText(FText::FromString(FString::Printf(TEXT("%.1f / %.0f kg"), Carried, MaxWeight)));
        TileBars[4]->SetPercent(MaxWeight > 0.f ? FMath::Clamp(Carried / MaxWeight, 0.f, 1.f) : 0.f);
        TileValues[5]->SetText(FText::FromString(TEXT("\u2014")));
        if (ClimateValue && HumidityBar)
        {
            const FEWClimate C = Survival->GetClimate();
            FString State = Survival->IsFreezing() ? TEXT("  Freezing") : Survival->IsOverheating() ? TEXT("  Overheating")
                : Survival->GetTargetBodyTemperature() < Survival->GetBodyTemperature() - .2f ? TEXT("  Cooling")
                : Survival->GetTargetBodyTemperature() > Survival->GetBodyTemperature() + .2f ? TEXT("  Warming") : TEXT("");
            ClimateValue->SetText(FText::FromString(FString::Printf(TEXT("%s   ·   Air %.0f\u00B0C   ·   Humidity %.0f%%   ·   Body %.1f\u00B0C%s"),
                *AEWClimateRegion::RegionName(C.Region).ToString(), C.AirTemperature, C.Humidity, Survival->GetBodyTemperature(), *State)));
            HumidityBar->SetPercent(FMath::Clamp(C.Humidity / 100.f, 0.f, 1.f));
            if (SubtitleText) SubtitleText->SetText(FText::Format(NSLOCTEXT("Elitewake", "SurvivorSubtitle", "Survivor  \u00B7  {0}"), AEWClimateRegion::RegionName(C.Region)));
        }
    }
    if (NameText)
    {
        const APlayerState* State = GetOwningPlayerState();
        const FString Name = State ? State->GetPlayerName() : FString();
        NameText->SetText(FText::FromString(Name.IsEmpty() ? TEXT("Survivor") : Name));
    }
    if (ArmorText)
    {
        // What the worn armor adds up to (owner, November 8): damage stopped, warmth, and the overheating it brings.
        const AEWCharacter* Me = Cast<AEWCharacter>(GetOwningPlayerPawn());
        const float Stop = Me ? Me->GetArmorReduction() : 0.f, Heat = Me ? Me->GetOverheatMultiplier() : 1.f;
        const float Warm = Me ? Me->GetClothingInsulation() : 0.f;
        ArmorText->SetText(FText::FromString(Stop <= 0.f && Heat <= 1.f && Warm <= 0.f ? FString(TEXT("Armor  \u2014"))
            : FString::Printf(TEXT("Armor  %d%% damage stopped   Cold protection %d%%   Overheating x%.2f"),
                FMath::RoundToInt(Stop * 100.f), FMath::RoundToInt(FMath::Min(Warm, 1.f) * 100.f), Heat)));
    }
    RefreshProgression();

}

void UEWInventoryWidget::Select(int32 Index)
{
    if (SelectionCount() == 0) return;
    Index = FMath::Clamp(Index, 0, SelectionCount()-1);
    // Picking an item takes the cursor back from the crafting list.
    const bool bLeftCrafting = bCraftingOpen;
    if (bLeftCrafting) { bCraftingOpen = false; InspectedRecipe = nullptr; RecipeScrollAxis = 0.f; bShowingDetails = false; SelectedIndex = Index; RefreshCrafting(); return; }
    if (Index != SelectedIndex) { SelectedIndex = Index; bShowingDetails = false; UpdateSelection(); }
}

void UEWInventoryWidget::UpdateSelection()
{
    for (int32 i=0; i<Rows.Num(); ++i)
    {
        const bool bPicked = i == SelectedIndex;
        Rows[i]->SetBrush(bPicked && !bCraftingOpen ? BrassRect(2.5f, CursorGold) : BrassRect(SlotStroke));
    }
    ItemPreview->GetParent()->SetVisibility(ESlateVisibility::Collapsed);
    if (!DetailsText) return;
    UEWItemDefinition* Item = SelectedItem();
    const bool bEquippable = Item && Item->EquipmentSlot != EEWEquipmentSlot::None;
    FoodActionButton->SetVisibility(bShowingDetails && Item && Item->bFoodConsumptionEnabled ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    EquipmentActionButton->SetVisibility(bShowingDetails && bEquippable ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    EquipmentActionText->SetText(FText::FromString(SelectedEquipmentSlot() == EEWEquipmentSlot::None ? TEXT("Equip") : TEXT("Unequip")));
    if (!Item && SelectedEquipmentSlot() != EEWEquipmentSlot::None)
        DetailsText->SetText(FText::Format(NSLOCTEXT("Elitewake", "EmptyEquipmentSlot", "{0} is empty. Select a suitable item in Inventory, then choose Equip (R / X)."),
            FText::FromString(EquipmentNames[EquipmentOrder(SelectedEquipmentSlot())])));
    else
        DetailsText->SetText(FText::FromString(SelectedIndex == INDEX_NONE ? TEXT("Your inventory is empty.\nGather supplies to begin.") : TEXT("Select an item to view its details.")));
    if (bShowingDetails) ConfirmSelection();
    RefreshHotbarAssignments();
    if (Rows.IsValidIndex(SelectedIndex))
    {
        UScrollBox* Scroll = DisplayedEntries.IsValidIndex(SelectedIndex) ? ItemsScroll.Get() : SurvivorScroll.Get();
        Scroll->ScrollWidgetIntoView(Rows[SelectedIndex], true);
    }
    RevealSelectionAfterFrames = 2;
}

void UEWInventoryWidget::ConfirmSelection()
{
    UEWItemDefinition* Item = SelectedItem();
    if (!Item) return;
    const int32 Quantity = DisplayedEntries.IsValidIndex(SelectedIndex) ? DisplayedEntries[SelectedIndex].Quantity : 1;
    bShowingDetails = true;
    ItemPreview->SetBrushFromTexture(ResolveIcon(Item)); ItemPreview->GetParent()->SetVisibility(ESlateVisibility::HitTestInvisible);
    FoodActionButton->SetVisibility(Item->bFoodConsumptionEnabled ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (auto* ActionLabel = Cast<UTextBlock>(FoodActionButton->GetContent()))
        ActionLabel->SetText(FText::FromString(Item->SurvivalTreatment == EEWSurvivalTreatment::None ? TEXT("Eat (R / X)") : TEXT("Use treatment (R / X)")));
    RefreshHotbarAssignments();
    FString ArmorLines;
    if (Item->ArmorKind != EEWArmorKind::None)
    {
        // Armor (owner, November 8): its category, what it covers and what it does.
        const TCHAR* Kind = Item->EquipmentSlot == EEWEquipmentSlot::Feet ? TEXT("Footwear")
            : Item->ArmorKind == EEWArmorKind::Cloth ? TEXT("Cloth") : Item->ArmorKind == EEWArmorKind::Fur ? TEXT("Fur") : TEXT("Metal");
        const TCHAR* Covers = Item->EquipmentSlot == EEWEquipmentSlot::Head ? TEXT("Helmet: head, face and neck")
            : Item->EquipmentSlot == EEWEquipmentSlot::Chest ? TEXT("Chest: torso, arms and hands (gloves included)")
            : Item->EquipmentSlot == EEWEquipmentSlot::Feet ? TEXT("Boots: feet and lower legs")
            : Item->EquipmentSlot == EEWEquipmentSlot::Legs ? TEXT("Pants: legs; included footwear is covered when boots are equipped") : TEXT("Wearable accessory");
        ArmorLines = FString::Printf(TEXT("\n%s armor   %s\nDamage stopped %.1f%%    Cold protection %s    Overheating +%.1f%%"),
            Kind, Covers, Item->ArmorReduction * 100.f,
            Item->Insulation > 0.f ? *FString::Printf(TEXT("%d%%"), FMath::RoundToInt(Item->Insulation * 100.f)) : TEXT("none"),
            Item->OverheatPenalty * 100.f);
    }
    DetailsText->SetText(FText::FromString(FString::Printf(TEXT("%s\n%s%s\nQuantity %d    Unit weight %.1f kg    Stack limit %d"),
        *Item->DisplayName.ToString(), *Item->Description.ToString(), *ArmorLines, Quantity,
        Item->UnitWeight, Item->MaxStackSize)));
    EquipmentActionButton->SetVisibility(Item->EquipmentSlot != EEWEquipmentSlot::None ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    EquipmentActionText->SetText(FText::FromString(SelectedEquipmentSlot() == EEWEquipmentSlot::None ? TEXT("Equip") : TEXT("Unequip")));
    // Details change the list's available height; reveal the selected row after that layout change.
    if (Rows.IsValidIndex(SelectedIndex))
    {
        UScrollBox* Scroll = DisplayedEntries.IsValidIndex(SelectedIndex) ? ItemsScroll.Get() : SurvivorScroll.Get();
        Scroll->ScrollWidgetIntoView(Rows[SelectedIndex], true, EDescendantScrollDestination::Center);
    }
    RevealSelectionAfterFrames = 2;
}

FReply UEWInventoryWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    auto* OwnerController = Cast<AEWPlayerController>(GetOwningPlayer());
    // Typing in a search box: the letters belong to the box, so none of the menu's keys may act. Enter, Escape or any controller button gives the keyboard back.
    if (IsTypingText())
    {
        if (Key==EKeys::Escape || Key==EKeys::Enter || Key.IsGamepadKey()) SetUserFocus(GetOwningPlayer());
        return FReply::Handled();
    }
    // Holding LB makes the hotbar chord; tapping it alone (no chord used) moves to the previous section when it is let go.
    if (OwnerController && OwnerController->IsHotbarModifierHeld() && Key != EKeys::Gamepad_LeftShoulder) bLbChordUsed = true;
    if (Key==EKeys::Gamepad_LeftShoulder)
    {
        if (!Event.IsRepeat()) { bLbChordUsed = false; if (OwnerController) OwnerController->SetHotbarModifierHeld(true); }
        return FReply::Handled();
    }
    if (Key==EKeys::M || Key==EKeys::Gamepad_Special_Left) { if (!Event.IsRepeat()) if (auto* PC=Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetMapOpen(true); return FReply::Handled(); }
    // Stat points: C, a left-stick press or RT starts choosing; Up/Down or the d-pad pick; Enter or A spends; Escape, B or C again stops.
    if (Key==EKeys::C || Key==EKeys::Gamepad_RightTrigger)
    { if (!Event.IsRepeat() && SelectedSection==0) SetStatFocus(StatFocus==INDEX_NONE ? 0 : INDEX_NONE); return FReply::Handled(); }
    const bool bSectionKey = Key==EKeys::Tab || Key==EKeys::PageUp || Key==EKeys::PageDown || Key==EKeys::Gamepad_RightShoulder || Key==EKeys::Gamepad_LeftTrigger;
    if (bResetConfirmation)
    {
        if ((Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat()) ConfirmAttributeChanges();
        else if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right) CancelAttributeChanges();
        return FReply::Handled();
    }
    if (GetPendingAttributeTotal() > 0 && StatFocus == INDEX_NONE && !bSectionKey)
    {
        if ((Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat()) { ConfirmAttributeChanges(); return FReply::Handled(); }
        if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right) { CancelAttributeChanges(); return FReply::Handled(); }
    }
    if (StatFocus != INDEX_NONE && !bSectionKey)
    {
        if (Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up) NavigateAttributeFocus(-1);
        else if (Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down) NavigateAttributeFocus(1);
        else if (Key==EKeys::Right || Key==EKeys::Gamepad_DPad_Right) { if (!Event.IsRepeat()) SpendStat(StatFocus); }
        else if (Key==EKeys::Left || Key==EKeys::Gamepad_DPad_Left) { if (!Event.IsRepeat()) UndoStat(StatFocus); }
        else if (Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom) { if (!Event.IsRepeat()) ConfirmAttributeChanges(); }
        else if ((Key==EKeys::R || Key==EKeys::Gamepad_FaceButton_Left) && !Event.IsRepeat()) OpenAttributeReset();
        else if (Key==EKeys::Escape || Key==EKeys::Gamepad_FaceButton_Right) CancelAttributeChanges();
        return FReply::Handled();      // while choosing a stat, the other keys do nothing
    }
    // Sections: Tab, PageDown or RB go on; Shift+Tab, PageUp or LT go back (LB goes back when it is tapped).
    const bool bNextSection = Key==EKeys::PageDown || Key==EKeys::Gamepad_RightShoulder || (Key==EKeys::Tab && !Event.IsShiftDown());
    const bool bPreviousSection = Key==EKeys::PageUp || Key==EKeys::Gamepad_LeftTrigger || (Key==EKeys::Tab && Event.IsShiftDown());
    if (bNextSection || bPreviousSection)
    { if (!Event.IsRepeat()) CycleSection(bNextSection ? 1 : -1); return FReply::Handled(); }
    const bool bUpKey = Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up, bDownKey = Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down;
    const bool bLeftKey = Key==EKeys::Left || Key==EKeys::Gamepad_DPad_Left, bRightKey = Key==EKeys::Right || Key==EKeys::Gamepad_DPad_Right;
    if (bTabFocus)
    {
        const bool bAccept = Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom, bBack = Key==EKeys::Escape || Key==EKeys::Gamepad_FaceButton_Right;
        if (!Event.IsRepeat() || bLeftKey || bRightKey) TabFocusInput(bLeftKey ? -1 : bRightKey ? 1 : 0, bDownKey ? 1 : 0, bAccept && !Event.IsRepeat(), bBack && !Event.IsRepeat());
        return FReply::Handled();
    }
    if (IsRecipeInspected() && Event.IsShiftDown() && (bUpKey || bDownKey))
    {
        ScrollRecipeCard(bUpKey ? -36.f : 36.f);
        return FReply::Handled();
    }
    if (bUpKey && AtTopOfSection()) { SetTabFocus(true); return FReply::Handled(); }
    if (SelectedSection >= 1)
    {
        // Skills, Company, Tames and Journal have no item list: each takes the arrows or d-pad its own way, and the rest of the keys only close the menu.
        if (SelectedSection==1 && SkillsPanel)
        {
            if (bUpKey) { if (!SkillsPanel->MoveSelection(FVector2D(0, -1))) { SetTabFocus(true); return FReply::Handled(); } }
            else if (bDownKey) SkillsPanel->MoveSelection(FVector2D(0, 1));
            else if (bLeftKey) SkillsPanel->MoveSelection(FVector2D(-1, 0));
            else if (bRightKey) SkillsPanel->MoveSelection(FVector2D(1, 0));
            else if ((Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat()) SkillsPanel->UnlockSelected();
        }
        if (SelectedSection==2 && CompanyPanel && CompanyPanel->HandleMenuKey(Key)) return FReply::Handled();
        if (SelectedSection==3 && TamesPanel && (bUpKey || bDownKey)) { TamesPanel->MoveSelection(bUpKey ? -1 : 1); return FReply::Handled(); }
        if (SelectedSection==4 && JournalPanel && (bUpKey || bDownKey))
            JournalPanel->ShowPage(FMath::Clamp(JournalPanel->GetSelectedPage() + (bUpKey ? -1 : 1), 0, FMath::Max(0, JournalPanel->GetPageCount()-1)));
        else if (Key==EKeys::I || Key==EKeys::Gamepad_FaceButton_Right || Key==EKeys::Escape)
        { if (!Event.IsRepeat()) if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->SetInventoryOpen(false); }
        return FReply::Handled();
    }
    if (bCraftingOpen && (Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom))
    { if (!Event.IsRepeat()) PerformCraft(); return FReply::Handled(); }
    if (OwnerController) OwnerController->RecordInputDevice(Key);
    if (HotbarPick != INDEX_NONE)
    {
        // Picking a slot: the d-pad or arrows move the cursor, A or Enter assigns (or takes the item off that slot), B, Y or Escape stop.
        const int32 Count = UEWHotbarComponent::SlotCount;
        if (bLeftKey || bUpKey) SetHotbarPick((HotbarPick + Count - 1) % Count);
        else if (bRightKey || bDownKey) SetHotbarPick((HotbarPick + 1) % Count);
        else if ((Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat()) { AssignHotbarSlot(HotbarPick); SetHotbarPick(INDEX_NONE); }
        else if ((Key==EKeys::Escape || Key==EKeys::Gamepad_FaceButton_Right || Key==EKeys::Gamepad_FaceButton_Top) && !Event.IsRepeat()) SetHotbarPick(INDEX_NONE);
        return FReply::Handled();
    }
    if (Key == EKeys::Gamepad_FaceButton_Top && !(OwnerController && OwnerController->IsHotbarModifierHeld()))
    {
        if (!Event.IsRepeat() && !bCraftingOpen) QuickAssignSelectedToHotbar();
        return FReply::Handled();
    }
    const int32 HotbarSlotIndex = AEWPlayerController::HotbarSlotForKey(
        Key, OwnerController && OwnerController->IsHotbarModifierHeld());
    const bool bHotbarChord = OwnerController && OwnerController->IsHotbarModifierHeld();
    if (HotbarSlotIndex!=INDEX_NONE && (bHotbarChord || !Key.IsGamepadKey()))
    {
        if (!Event.IsRepeat()) AssignHotbarSlot(HotbarSlotIndex);
        return FReply::Handled();
    }
    if (Key == EKeys::I || Key == EKeys::Gamepad_FaceButton_Top || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Escape)
    {
        if (!Event.IsRepeat()) if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->SetInventoryOpen(false);
        return FReply::Handled();
    }
    // The cursor moves over the inventory grid, and past its last row on into the crafting list below it.
    if (bLeftKey) { MoveCursor(-1, 0); return FReply::Handled(); }
    if (bRightKey) { MoveCursor(1, 0); return FReply::Handled(); }
    if (bUpKey) { MoveCursor(0, -1); return FReply::Handled(); }
    if (bDownKey) { MoveCursor(0, 1); return FReply::Handled(); }
    if (Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom) { if (!Event.IsRepeat()) ConfirmSelection(); return FReply::Handled(); }
    if (Key == EKeys::R || Key == EKeys::Gamepad_FaceButton_Left)
    {
        if (bCraftingOpen)
        {
            if (!Event.IsRepeat()) InspectRecipe(SelectedRecipeIndex);
            return FReply::Handled();
        }
        if (!Event.IsRepeat())
        {
            if (SelectedItem() && SelectedItem()->bFoodConsumptionEnabled) PerformFoodAction();
            else PerformEquipmentAction();
        }
        return FReply::Handled();
    }
    return FReply::Handled(); // UI owns input while open, including gameplay bindings.
}

void UEWInventoryWidget::QuickAssignSelectedToHotbar()
{
    UEWItemDefinition* Item = SelectedItem();
    auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    auto* Character = Controller ? Cast<AEWCharacter>(Controller->GetPawn()) : nullptr;
    UEWHotbarComponent* Hotbar = Character ? Character->GetHotbarComponent() : nullptr;
    if (!Item || !Controller || !Hotbar) return;

    int32 ExistingSlot = INDEX_NONE;
    int32 EmptySlot = INDEX_NONE;
    const int32 Preferred = FMath::Clamp(Hotbar->GetSelectedSlot(), 0, UEWHotbarComponent::SlotCount - 1);
    for (int32 Offset = 0; Offset < UEWHotbarComponent::SlotCount; ++Offset)
    {
        const int32 SlotIndex = (Preferred + Offset) % UEWHotbarComponent::SlotCount;
        if (Hotbar->GetBoundItem(SlotIndex) == Item) { ExistingSlot = SlotIndex; break; }
        if (EmptySlot == INDEX_NONE && !Hotbar->GetBoundItem(SlotIndex)) EmptySlot = SlotIndex;
    }

    if (ExistingSlot != INDEX_NONE)
    {
        SetHotbarPick(ExistingSlot);      // already on the bar: choose another slot, or take it off this one
        return;
    }
    if (EmptySlot != INDEX_NONE)
    {
        Controller->RequestHotbarBinding(EmptySlot, Item);
        ShowHotbarResult(EEWHotbarResult::Success);
        return;
    }

    SetHotbarPick(Preferred);      // the bar is full: choose the slot to replace
}

void UEWInventoryWidget::SetHotbarPick(int32 SlotIndex)
{
    const bool bCan = SelectedItem() && BoundHotbar && SlotIndex >= 0 && SlotIndex < UEWHotbarComponent::SlotCount;
    if (bCan && !bShowingDetails) ConfirmSelection();      // the slots sit in the item's details
    HotbarPick = bCan ? SlotIndex : INDEX_NONE;
    if (EquipmentResultText && HotbarPick != INDEX_NONE)
        EquipmentResultText->SetText(NSLOCTEXT("Elitewake", "HotbarPick", "Pick a hotbar slot: d-pad moves, A assigns or removes, B cancels."));
    RefreshHotbarAssignments();
}

FReply UEWInventoryWidget::NativeOnKeyUp(const FGeometry& Geometry, const FKeyEvent& Event)
{
    if (Event.GetKey()==EKeys::Gamepad_LeftShoulder)
    {
        if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->SetHotbarModifierHeld(false);
        if (!bLbChordUsed && !IsTypingText()) CycleSection(-1);      // tapped alone: LB goes back a section, as RB goes on
        bLbChordUsed = true;
    }
    return FReply::Handled();
}

void UEWInventoryWidget::SetTabFocus(bool bFocus)
{
    bTabFocus = bFocus; TabCursor = SelectedSection; StatFocus = INDEX_NONE;
    ApplySectionVisibility();
}

bool UEWInventoryWidget::AtTopOfSection() const
{
    switch (SelectedSection)
    {
    case 2: return CompanyPanel && !CompanyPanel->IsConfirmOpen() && CompanyPanel->IsAtFirstMember();
    case 3: return TamesPanel && TamesPanel->GetSelectedTame() <= 0;
    case 4: return JournalPanel && JournalPanel->GetSelectedPage() <= 0;
    default: return false;
    }
}

void UEWInventoryWidget::TabFocusInput(int32 Dx, int32 Dy, bool bAccept, bool bBack)
{
    if (bAccept) { SelectSection(TabCursor); return; }
    if (bBack || Dy > 0) { SetTabFocus(false); return; }
    if (Dx) { TabCursor = FMath::Clamp(TabCursor + Dx, 0, GetSectionCount() - 1); ApplySectionVisibility(); }
}

void UEWInventoryWidget::NavigateStep(int32 Dx, int32 Dy)
{
    if (!Dx && !Dy) return;
    if (bTabFocus) { TabFocusInput(Dx, Dy, false, false); return; }
    if (Dy < 0 && AtTopOfSection()) { SetTabFocus(true); return; }
    if (StatFocus != INDEX_NONE)
    {
        if (Dy) NavigateAttributeFocus(Dy);
        else if (Dx > 0) SpendStat(StatFocus);
        else if (Dx < 0) UndoStat(StatFocus);
        return;
    }
    switch (SelectedSection)
    {
    case 0:
        if (HotbarPick != INDEX_NONE) { const int32 Count = UEWHotbarComponent::SlotCount; SetHotbarPick((HotbarPick + ((Dx + Dy) > 0 ? 1 : Count - 1)) % Count); }
        else MoveCursor(Dx, Dy);
        break;
    case 1: if (SkillsPanel && !SkillsPanel->MoveSelection(FVector2D(Dx, Dy)) && Dy < 0 && !Dx) SetTabFocus(true); break;   // nothing further up: on to the tab bar
    case 2:
        if (CompanyPanel)
        {
            if (Dy) CompanyPanel->HandleMenuKey(Dy < 0 ? EKeys::Up : EKeys::Down);
            if (Dx) CompanyPanel->HandleMenuKey(Dx < 0 ? EKeys::Left : EKeys::Right);
        }
        break;
    case 3: if (TamesPanel && Dy) TamesPanel->MoveSelection(Dy); break;
    case 4:
        if (JournalPanel && Dy) JournalPanel->ShowPage(FMath::Clamp(JournalPanel->GetSelectedPage() + Dy, 0, FMath::Max(0, JournalPanel->GetPageCount() - 1)));
        break;
    default: break;
    }
}

FReply UEWInventoryWidget::NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event)
{
    if (FMath::Abs(Event.GetAnalogValue()) > .2f)
        if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->RecordInputDevice(Event.GetKey());
    // The left stick steps the highlight on every tab, the way the d-pad does: both axes, repeating while held.
    if (Event.GetKey() == EKeys::Gamepad_RightY)
    {
        RecipeScrollAxis = IsRecipeInspected() && FMath::Abs(Event.GetAnalogValue()) >= .2f ? -Event.GetAnalogValue() : 0.f;
    }
    else if (Event.GetKey() == EKeys::Gamepad_LeftY)
    {
        const int32 Direction = FMath::Abs(Event.GetAnalogValue()) >= .5f ? (Event.GetAnalogValue() > 0 ? -1 : 1) : 0;
        if (Direction != AnalogDirection) { AnalogDirection = Direction; AnalogRepeatRemaining = .35f; if (Direction) NavigateStep(0, Direction); }
    }
    else if (Event.GetKey() == EKeys::Gamepad_LeftX)
    {
        const int32 Direction = FMath::Abs(Event.GetAnalogValue()) >= .5f ? (Event.GetAnalogValue() > 0 ? 1 : -1) : 0;
        if (Direction != AnalogHorizontal) { AnalogHorizontal = Direction; AnalogRepeatRemaining = .35f; if (Direction) NavigateStep(Direction, 0); }
    }
    return FReply::Handled();
}

int32 UEWInventoryWidget::RowAt(const FVector2D& Position) const
{
    if (SelectedSection != 0) return INDEX_NONE;
    for (int32 i=0; i<Rows.Num(); ++i)
    {
        // Items scroll inside the inventory list, equipment inside the character panel: a tile scrolled out of its list cannot be hit.
        const UWidget* Clip = i < DisplayedEntries.Num() ? static_cast<const UWidget*>(ItemsScroll) : static_cast<const UWidget*>(SurvivorScroll);
        if (Clip && !Clip->GetCachedGeometry().IsUnderLocation(Position)) continue;
        if (Rows[i]->GetCachedGeometry().IsUnderLocation(Position)) return i;
    }
    return INDEX_NONE;
}

FReply UEWInventoryWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (!Event.GetCursorDelta().IsNearlyZero()) { const int32 Row = RowAt(Event.GetScreenSpacePosition()); if (Row != INDEX_NONE) Select(Row); }
    return Super::NativeOnMouseMove(Geometry, Event);
}

FReply UEWInventoryWidget::NativeOnPreviewMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->RecordInputDevice(Event.GetEffectingButton());
    // A click anywhere but the search boxes hands the keyboard back to the menu.
    if (IsTypingText())
    {
        const FVector2D At = Event.GetScreenSpacePosition();
        const bool bInBox = (SearchBox && SearchBox->GetCachedGeometry().IsUnderLocation(At)) || (RecipeSearchBox && RecipeSearchBox->GetCachedGeometry().IsUnderLocation(At))
            || (CompanyPanel && CompanyPanel->IsPointerOverTextBox(At));
        if (!bInBox) SetUserFocus(GetOwningPlayer());
    }
    return Super::NativeOnPreviewMouseButtonDown(Geometry, Event);
}

FReply UEWInventoryWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() == EKeys::LeftMouseButton)
    {
        const int32 Row = RowAt(Event.GetScreenSpacePosition());
        if (Row != INDEX_NONE) { Select(Row); ConfirmSelection(); return FReply::Handled().SetUserFocus(TakeWidget()); }
    }
    return Super::NativeOnMouseButtonDown(Geometry, Event);
}

void UEWInventoryWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    UpdatePortrait(DeltaTime);
    if (CraftSecondsLeft > 0.f)
    {
        CraftSecondsLeft = FMath::Max(0.f, CraftSecondsLeft - DeltaTime);
        if (CraftBar) CraftBar->SetPercent(GetCraftProgress());
        if (CraftBarText) CraftBarText->SetText(FText::Format(NSLOCTEXT("Elitewake", "CraftTimeLeft", "Crafting... {0} s"), FMath::CeilToInt(CraftSecondsLeft)));
    }
    const auto* OwningCharacter = Cast<AEWCharacter>(GetOwningPlayerPawn());
    UEWHotbarComponent* Hotbar = OwningCharacter ? OwningCharacter->GetHotbarComponent() : nullptr;
    if (Hotbar != BoundHotbar)
    {
        if (BoundHotbar) BoundHotbar->OnHotbarChanged.RemoveDynamic(this,&UEWInventoryWidget::RefreshHotbarAssignments);
        BoundHotbar=Hotbar;
        if (BoundHotbar) BoundHotbar->OnHotbarChanged.AddDynamic(this,&UEWInventoryWidget::RefreshHotbarAssignments);
        RefreshHotbarAssignments();
    }
    if (UEWInventoryComponent* Inventory = ResolveInventory(); Inventory != BoundInventory)
    {
        if (BoundInventory) BoundInventory->OnInventoryChanged.RemoveDynamic(this, &UEWInventoryWidget::RefreshInventory);
        BoundInventory = Inventory;
        if (BoundInventory) BoundInventory->OnInventoryChanged.AddDynamic(this, &UEWInventoryWidget::RefreshInventory);
        DisplayedEntries.Reset(); DisplayedEquipment.Reset(); SelectedIndex = INDEX_NONE; bShowingDetails = false;
        if (!BoundInventory) { ItemsBox->ClearChildren(); Rows.Reset(); RowRings.Reset(); DetailsText->SetText(FText::FromString(TEXT("No item selected"))); }
	RefreshInventory();
    RefreshCrafting();
}
    if (UEWEquipmentComponent* Equipment = ResolveEquipment(); Equipment != BoundEquipment)
    {
        if (BoundEquipment) BoundEquipment->OnEquipmentChanged.RemoveDynamic(this, &UEWInventoryWidget::RefreshInventory);
        BoundEquipment = Equipment;
        if (BoundEquipment) BoundEquipment->OnEquipmentChanged.AddDynamic(this, &UEWInventoryWidget::RefreshInventory);
        RefreshInventory();
    }
    RefreshSummary();
    if (bCraftingOpen && BoundInventory && DisplayedRecipes.IsValidIndex(SelectedRecipeIndex))
    {
        RecipeRefreshRemaining -= DeltaTime;
        if (RecipeRefreshRemaining <= 0.f)
        {
            RecipeRefreshRemaining = .25f;
            UpdateRecipeCards();
            const auto Readiness = bCraftRequestPending || CraftSecondsLeft > 0.f
                ? EEWCraftResult::Busy : BoundInventory->GetCraftReadiness(GetShownRecipe());
            if (Readiness != ShownCraftReadiness) UpdateCraftActions();
        }
    }
    if (HasUserFocus(GetOwningPlayer()) && !IsTypingText() && RecipeScrollAxis != 0.f)
        ScrollRecipeCard(RecipeScrollAxis * DeltaTime * 180.f);
    // Use settled geometry: confirmation may shrink the scroll viewport after the input event.
    if (RevealSelectionAfterFrames > 0 && --RevealSelectionAfterFrames == 0 && Rows.IsValidIndex(SelectedIndex))
    {
        UScrollBox* Scroll = DisplayedEntries.IsValidIndex(SelectedIndex) ? ItemsScroll.Get() : SurvivorScroll.Get();
        Scroll->ScrollWidgetIntoView(Rows[SelectedIndex], false);
    }
    if (!HasUserFocus(GetOwningPlayer()) || IsTypingText()) { AnalogDirection = 0; AnalogHorizontal = 0; RecipeScrollAxis = 0.f; }
    if (AnalogDirection || AnalogHorizontal)
    {
        AnalogRepeatRemaining -= DeltaTime;
        if (AnalogRepeatRemaining <= 0) { NavigateStep(AnalogHorizontal, AnalogDirection); AnalogRepeatRemaining = .18f; }
    }
}

UEWEquipmentComponent* UEWInventoryWidget::ResolveEquipment() const
{
    const AEWCharacter* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    return Character ? Character->GetEquipmentComponent() : nullptr;
}

UEWItemDefinition* UEWInventoryWidget::SelectedItem() const
{
    if (DisplayedEntries.IsValidIndex(SelectedIndex)) return DisplayedEntries[SelectedIndex].ItemDefinition.Get();
    const int32 EquipmentIndex = SelectedIndex - DisplayedEntries.Num();
    return DisplayedEquipment.IsValidIndex(EquipmentIndex) ? DisplayedEquipment[EquipmentIndex].ItemDefinition.Get() : nullptr;
}

UEWItemDefinition* UEWInventoryWidget::GetSelectedItemDefinition() const
{
    return SelectedItem();
}

EEWEquipmentSlot UEWInventoryWidget::SelectedEquipmentSlot() const
{
    const int32 Index = SelectedIndex - DisplayedEntries.Num();
    return DisplayedEquipment.IsValidIndex(Index) ? DisplayedEquipment[Index].Slot : EEWEquipmentSlot::None;
}

UWidget* UEWInventoryWidget::GetEquipmentSlotWidget(EEWEquipmentSlot EquipmentSlot) const
{
    const int32 Index = DisplayedEquipment.IndexOfByPredicate([EquipmentSlot](const FEWEquipmentEntry& Entry) { return Entry.Slot == EquipmentSlot; });
    const int32 Row = DisplayedEntries.Num() + Index;
    return Index != INDEX_NONE && Rows.IsValidIndex(Row) ? Rows[Row].Get() : nullptr;
}

void UEWInventoryWidget::PerformEquipmentAction()
{
    UEWItemDefinition* Item = SelectedItem();
    auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!bShowingDetails || !Item || !Controller) return;
    EquipmentResultText->SetText(FText::FromString(TEXT("Requesting equipment change…")));
    if (SelectedEquipmentSlot() != EEWEquipmentSlot::None) Controller->RequestUnequipItem(SelectedEquipmentSlot());
    else Controller->RequestEquipItem(Item, Item->EquipmentSlot);
}
FText UEWInventoryWidget::GetDisplayedDetails() const
{
    return DetailsText ? DetailsText->GetText() : FText::GetEmpty();
}
bool UEWInventoryWidget::IsFoodActionVisible() const
{
    return FoodActionButton && FoodActionButton->GetVisibility() == ESlateVisibility::Visible;
}
float UEWInventoryWidget::GetDisplayedFoodFreshness() const
{
    const UProgressBar* Bar = RowFreshness.IsValidIndex(SelectedIndex) ? RowFreshness[SelectedIndex].Get() : nullptr;
    return Bar ? Bar->GetPercent() : -1.f;
}
void UEWInventoryWidget::PerformFoodAction()
{
    auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    UEWItemDefinition* Item = SelectedItem();
    if (!bShowingDetails || !Item || !Item->bFoodConsumptionEnabled || !Controller) return;
    EquipmentResultText->SetText(FText::FromString(Item->SurvivalTreatment == EEWSurvivalTreatment::None ? TEXT("Eating…") : TEXT("Preparing treatment…")));
    Controller->RequestConsumeFood(Item);
}
void UEWInventoryWidget::ShowFoodResult(EEWFoodUseResult Result)
{
    FString Message;
    switch (Result)
    {
        case EEWFoodUseResult::Success: Message = TEXT("Berry eaten"); break;
        case EEWFoodUseResult::TreatmentStarted: Message = TEXT("Applying bandage"); break;
        case EEWFoodUseResult::TreatmentApplied: Message = TEXT("Treatment applied"); break;
        case EEWFoodUseResult::TreatmentUnneeded: Message = TEXT("You do not need this treatment"); break;
        case EEWFoodUseResult::NoBenefit: Message = TEXT("Hunger and health are already full"); break;
        case EEWFoodUseResult::NotOwned: Message = TEXT("That food is no longer in your inventory"); break;
        case EEWFoodUseResult::InvalidFood: Message = TEXT("That item cannot be eaten"); break;
        case EEWFoodUseResult::UnavailableSurvivor: Message = TEXT("You cannot eat while dead"); break;
        default: Message = TEXT("Eating could not be completed"); break;
    }
    if (EquipmentResultText) EquipmentResultText->SetText(FText::FromString(Message));
}

void UEWInventoryWidget::ShowEquipmentResult(EEWEquipmentResult Result)
{
    FString Message;
    switch (Result)
    {
        case EEWEquipmentResult::Success: Message = TEXT("Equipment updated"); break;
        case EEWEquipmentResult::InventoryFull: Message = TEXT("Inventory is full — make space before removing or replacing this item"); break;
        case EEWEquipmentResult::NotOwned: Message = TEXT("That item is no longer in your inventory"); break;
        case EEWEquipmentResult::AlreadyEquipped: Message = TEXT("That item is already equipped"); break;
        case EEWEquipmentResult::EmptySlot: Message = TEXT("That slot is already empty"); break;
        case EEWEquipmentResult::InvalidSlot: Message = TEXT("That item does not fit this equipment slot"); break;
        default: Message = TEXT("Equipment change could not be completed"); break;
    }
    if (EquipmentResultText) EquipmentResultText->SetText(FText::FromString(Message));
}

UEWInventoryComponent* UEWInventoryWidget::ResolveInventory() const
{
	if (const AEWCharacter* Character = Cast<AEWCharacter>(GetOwningPlayerPawn()))
	{
		return Character->GetInventoryComponent();
	}
	return nullptr;
}

void UEWInventoryWidget::RefreshHotbarAssignments()
{
    if (!HotbarAssignments) return;
    UEWItemDefinition* Item = SelectedItem();
    if (!(bShowingDetails && Item && BoundHotbar)) HotbarPick = INDEX_NONE;
    HotbarAssignments->SetVisibility(bShowingDetails && Item && BoundHotbar ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    for (int32 i=0; i<HotbarButtons.Num(); ++i)
    {
        const bool bBound = Item && BoundHotbar && BoundHotbar->GetBoundItem(i)==Item;
        const bool bPicked = HotbarPick == i;
        HotbarButtonLabels[i]->SetText(FText::FromString(bPicked ? FString::Printf(TEXT("[%d]%s"),i+1,bBound ? TEXT(" ✓") : TEXT("")) : FString::Printf(TEXT("%d%s"),i+1,bBound ? TEXT(" ✓") : TEXT(""))));
        HotbarButtons[i]->SetBackgroundColor(bPicked ? FLinearColor(1.f, .85f, .35f, 1.f) : FLinearColor::White);
        HotbarButtons[i]->SetToolTipText(FText::FromString(bBound
            ? FString::Printf(TEXT("Remove this shortcut from slot %d"),i+1)
            : FString::Printf(TEXT("Assign selected item to slot %d"),i+1)));
    }
}
void UEWInventoryWidget::AssignHotbarSlot(int32 SlotIndex)
{
    UEWItemDefinition* Item = SelectedItem();
    auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    if (!bShowingDetails || !Item || !BoundHotbar || !Controller) return;
    EquipmentResultText->SetText(FText::FromString(TEXT("Updating hotbar…")));
    Controller->RequestHotbarBinding(SlotIndex,BoundHotbar->GetBoundItem(SlotIndex)==Item ? nullptr : Item);
}
void UEWInventoryWidget::ShowHotbarResult(EEWHotbarResult Result)
{
    if (EquipmentResultText) EquipmentResultText->SetText(UEWHotbarWidget::ResultText(Result));
}

UTexture2D* UEWInventoryWidget::ResolveIcon(UEWItemDefinition* Item)
{
    if (!Item) return nullptr;
    if (auto* Texture=Item->Icon.LoadSynchronous()) return Texture;
    if (Item->FoodKind == EEWFoodKind::BerryDish)
        if (auto* Texture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/Elitewake/UI/Inventory/T_InventoryBerryDish.T_InventoryBerryDish")))
            return Texture;
    int32 Kind=8;
    if (Item->GatheringTool==EEWGatheringTool::Hatchet) Kind=5;
    else if (Item->GatheringTool==EEWGatheringTool::Pickaxe) Kind=6;
    else if (Item->FoodKind==EEWFoodKind::Berry) Kind=7;
    else if (Item->Category==EEWItemCategory::Clothing) Kind=9;
    if (!FallbackIcons.Contains(Kind)) FallbackIcons.Add(Kind,EWHudIcon::Make(Kind,false));
    return FallbackIcons[Kind];
}
