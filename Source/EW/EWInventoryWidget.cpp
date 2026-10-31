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
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "EWHotbarWidget.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWCraftingRecipe.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Components/WrapBox.h"
#include "EWHudIcon.h"
#include "Components/WrapBoxSlot.h"
#include "Engine/Texture2D.h"
#include "EWSurvivalComponent.h"
#include "EWProgressionComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/Button.h"
#include "Components/ProgressBar.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "InputCoreTypes.h"
#include "Styling/SlateColor.h"

namespace
{
	constexpr float PortraitWidth = 260.f, PortraitHeight = 412.f;      // the survivor picture in the viewer; the capture is 340 x 540
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

void UEWInventoryWidget::ClosePortrait()
{
    if (PortraitCapture) PortraitCapture->Destroy();
    PortraitCapture = nullptr;
    PortraitTarget = nullptr;
}

void UEWInventoryWidget::UpdatePortrait(float DeltaTime)
{
    auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    UWorld* World = GetWorld();
    const bool bShown = RightHost && RightHost->GetVisibility() == ESlateVisibility::Visible && PortraitImage;
    if (!bShown || !Character || !World) return;
    if (!PortraitCapture)
    {
        PortraitTarget = NewObject<UTextureRenderTarget2D>(this);
        PortraitTarget->RenderTargetFormat = RTF_RGBA8;
        PortraitTarget->InitAutoFormat(340, 540);
        PortraitTarget->UpdateResourceImmediate(true);
        FActorSpawnParameters Params;
        Params.ObjectFlags |= RF_Transient;
        PortraitCapture = World->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
        if (!PortraitCapture) return;
        PortraitCapture->SetReplicates(false);
        auto* Camera = PortraitCapture->GetCaptureComponent2D();
        Camera->TextureTarget = PortraitTarget;
        Camera->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
        Camera->bCaptureEveryFrame = false;
        Camera->bCaptureOnMovement = false;
        Camera->FOVAngle = 30.f;
        Camera->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
        Camera->ShowFlags.SetAtmosphere(false);
        Camera->ShowFlags.SetFog(false);
        Camera->ShowFlags.SetBloom(false);
        FSlateBrush Brush; Brush.SetResourceObject(PortraitTarget); Brush.ImageSize = FVector2D(PortraitWidth, PortraitHeight); Brush.DrawAs = ESlateBrushDrawType::Image;
        PortraitImage->SetBrush(Brush);
        PortraitImage->SetColorAndOpacity(FLinearColor::White);
        PortraitClock = 10.f;
    }
    PortraitClock += DeltaTime;
    if (PortraitClock < .15f) return;
    PortraitClock = 0.f;
    // In front of the survivor, a little above the waist, looking at the chest: the whole figure fits the 190 x 300 frame.
    auto* Camera = PortraitCapture->GetCaptureComponent2D();
    Camera->ShowOnlyActors.Reset();
    Camera->ShowOnlyActors.Add(Character);
    TArray<AActor*> Attached;
    Character->GetAttachedActors(Attached);
    for (AActor* Held : Attached) Camera->ShowOnlyActors.Add(Held);
    const FVector Body = Character->GetActorLocation();
    const FVector Facing = Character->GetActorForwardVector();
    const FVector Front = FVector(Facing.X, Facing.Y, 0.f).GetSafeNormal();
    const FVector Eye = Body + Front * 250.f + FVector(0.f, 0.f, 12.f);
    PortraitCapture->SetActorLocationAndRotation(Eye, (Body + FVector(0.f, 0.f, 5.f) - Eye).Rotation());
    Camera->CaptureScene();
}

void UEWInventoryWidget::NativeDestruct()
{
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
	Panel->SetBrushColor(FLinearColor(0.015f, 0.025f, 0.035f, 0.55f));
	Panel->SetPadding(FMargin(20.0f));
	Panel->SetHorizontalAlignment(HAlign_Fill);
	Panel->SetVerticalAlignment(VAlign_Fill);
	WidgetTree->RootWidget = Panel;

	UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("InventoryContent"));
	Panel->SetContent(Content);

	// Top navigation (owner, October 25): INVENTORY, SKILLS, COMPANY, TAMES, JOURNAL. The open tab is light, the rest dark translucent grey.
	auto* Tabs = WidgetTree->ConstructWidget<UHorizontalBox>();
	Content->AddChildToVerticalBox(Tabs);
	const TCHAR* Sections[] = {TEXT("INVENTORY"), TEXT("SKILLS"), TEXT("COMPANY"), TEXT("TAMES"), TEXT("JOURNAL")};
	for (int32 Index = 0; Index < 5; ++Index)
	{
		auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
		Button->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::SelectSection);
		auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(Sections[Index]));
		auto Font = Label->GetFont(); Font.Size = 14; Font.LetterSpacing = 140; Label->SetFont(Font);
		Label->SetJustification(ETextJustify::Center); Button->SetContent(Label);
		auto* NavSlot = Tabs->AddChildToHorizontalBox(Button); NavSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		NavSlot->SetPadding(FMargin(0, 0, 4, 0)); SectionButtons.Add(Button); SectionLabels.Add(Label);
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

	// Left: the inventory panel, and the crafting section directly beneath it.
	auto* Browser = WidgetTree->ConstructWidget<UVerticalBox>(); BrowserPanel = Browser;
	auto* BrowserBorder = WidgetTree->ConstructWidget<UBorder>(); BrowserBorder->SetPadding(FMargin(14));
	BrowserBorder->SetBrushColor(FLinearColor(.03f, .036f, .042f, .78f)); BrowserBorder->SetContent(Browser);
	BrowserHost = BrowserBorder;
	FillSlot(BrowserBorder, 1.35f, FMargin(0, 12, 12, 0));
	// A section's heading, its search box and (for the inventory) a small sort button.
	auto Heading = [&](UVerticalBox* Into, const TCHAR* Title, UEditableTextBox*& Search, bool bSort)
	{
		auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
		auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(Title));
		auto Font = Label->GetFont(); Font.Size = 17; Font.LetterSpacing = 200; Label->SetFont(Font);
		Label->SetColorAndOpacity(FSlateColor(FLinearColor(.88f, .86f, .8f)));
		Row->AddChildToHorizontalBox(Label)->SetVerticalAlignment(VAlign_Center);
		Search = WidgetTree->ConstructWidget<UEditableTextBox>(); Search->SetHintText(NSLOCTEXT("Elitewake", "SearchHint", "Search"));
		Search->OnTextCommitted.AddDynamic(this, &UEWInventoryWidget::OnSearchCommitted);
		auto* SearchSlot = Row->AddChildToHorizontalBox(Search); SearchSlot->SetPadding(FMargin(16, 0, bSort ? 6 : 0, 0));
		SearchSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); SearchSlot->SetVerticalAlignment(VAlign_Center);
		if (bSort)
		{
			// The small action icon: sorts the grid by name, or back to the order things arrived.
			auto* Sort = WidgetTree->ConstructWidget<UEWInventoryActionButton>(); Sort->OnClicked.AddDynamic(this, &UEWInventoryWidget::ToggleSort);
			auto* Glyph = WidgetTree->ConstructWidget<UTextBlock>(); Glyph->SetText(FText::FromString(TEXT("A-Z"))); Glyph->SetJustification(ETextJustify::Center);
			auto GlyphFont = Glyph->GetFont(); GlyphFont.Size = 11; Glyph->SetFont(GlyphFont); Sort->SetContent(Glyph);
			Sort->SetBackgroundColor(FLinearColor(.07f, .085f, .1f)); SortButton = Sort;
			auto* SortSize = WidgetTree->ConstructWidget<USizeBox>(); SortSize->SetWidthOverride(44); SortSize->SetContent(Sort);
			Row->AddChildToHorizontalBox(SortSize)->SetVerticalAlignment(VAlign_Center);
		}
		Into->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 0, 0, 8));
	};
	UEditableTextBox* InventorySearchBox = nullptr; UEditableTextBox* CraftSearchBox = nullptr;
	Heading(Browser, TEXT("INVENTORY"), InventorySearchBox, true); SearchBox = InventorySearchBox;
	SearchBox->OnTextChanged.AddDynamic(this, &UEWInventoryWidget::OnInventorySearch);
	SummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventorySummary"));
	SummaryText->SetColorAndOpacity(FSlateColor(FLinearColor(.7f, .76f, .82f)));
	{ auto SummaryFont = SummaryText->GetFont(); SummaryFont.Size = 12; SummaryText->SetFont(SummaryFont); }
	Browser->AddChildToVerticalBox(SummaryText)->SetPadding(FMargin(0, 0, 0, 6));
	ItemsBox = WidgetTree->ConstructWidget<UWrapBox>(); ItemsBox->SetInnerSlotPadding(FVector2D(4, 4));
	ItemsScroll = WidgetTree->ConstructWidget<UScrollBox>(); ItemsScroll->AddChild(ItemsBox);
	Browser->AddChildToVerticalBox(ItemsScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	Heading(Browser, TEXT("CRAFTING"), CraftSearchBox, false); RecipeSearchBox = CraftSearchBox;
	RecipeSearchBox->OnTextChanged.AddDynamic(this, &UEWInventoryWidget::OnRecipeSearch);
	if (auto* CraftHeadingSlot = Cast<UVerticalBoxSlot>(RecipeSearchBox->GetParent() ? RecipeSearchBox->GetParent()->Slot : nullptr)) CraftHeadingSlot->SetPadding(FMargin(0, 12, 0, 8));
	CraftingBox = WidgetTree->ConstructWidget<UVerticalBox>();
	CraftScroll = WidgetTree->ConstructWidget<UScrollBox>(); CraftScroll->AddChild(CraftingBox);
	Browser->AddChildToVerticalBox(CraftScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	// Centre: the character, equipment, world, stats and the level-up arrows.
	auto* SurvivorBorder = WidgetTree->ConstructWidget<UBorder>();
	SurvivorPanel = SurvivorBorder;
	SurvivorBorder->SetPadding(FMargin(16)); SurvivorBorder->SetBrushColor(FLinearColor(.03f, .036f, .042f, .78f));
	FillSlot(SurvivorBorder, 1.25f, FMargin(0, 12, 12, 0));
	SurvivorScroll = WidgetTree->ConstructWidget<UScrollBox>(); SurvivorBorder->SetContent(SurvivorScroll);
	auto* SurvivorBody = WidgetTree->ConstructWidget<UVerticalBox>(); SurvivorScroll->AddChild(SurvivorBody);
	BuildCharacterPanel(SurvivorBody);

	// Right: the character viewer, and under it the details of whatever is picked.
	auto* RightColumn = WidgetTree->ConstructWidget<UVerticalBox>();
	FillSlot(RightColumn, 1.f, FMargin(0, 12, 0, 0));
	RightHost = RightColumn;
	auto* ViewerBorder = WidgetTree->ConstructWidget<UBorder>(); ViewerBorder->SetPadding(FMargin(10));
	ViewerBorder->SetBrushColor(FLinearColor(.02f, .026f, .032f, .85f));
	ViewerPanel = ViewerBorder;
	PortraitImage = WidgetTree->ConstructWidget<UImage>(); PortraitImage->SetColorAndOpacity(FLinearColor(1.f, 1.f, 1.f, 0.f));
	auto* PortraitSize = WidgetTree->ConstructWidget<USizeBox>(); PortraitSize->SetWidthOverride(PortraitWidth); PortraitSize->SetHeightOverride(PortraitHeight); PortraitSize->SetContent(PortraitImage);
	ViewerBorder->SetContent(PortraitSize); ViewerBorder->SetHorizontalAlignment(HAlign_Center);
	RightColumn->AddChildToVerticalBox(ViewerBorder)->SetPadding(FMargin(0, 0, 0, 10));
	auto* DetailBorder = WidgetTree->ConstructWidget<UBorder>();
	DetailsPanel = DetailBorder; DetailBorder->SetPadding(FMargin(16)); DetailBorder->SetBrushColor(FLinearColor(.035f, .045f, .055f, .95f));
	RightColumn->AddChildToVerticalBox(DetailBorder)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	auto* DetailScroll = WidgetTree->ConstructWidget<UScrollBox>(); DetailBorder->SetContent(DetailScroll);
	auto* DetailPanel = WidgetTree->ConstructWidget<UVerticalBox>(); DetailScroll->AddChild(DetailPanel);
	ItemPreview = WidgetTree->ConstructWidget<UImage>();
	auto* PreviewSize = WidgetTree->ConstructWidget<USizeBox>();
	PreviewSize->SetWidthOverride(96); PreviewSize->SetHeightOverride(96); PreviewSize->SetContent(ItemPreview);
	DetailPanel->AddChildToVerticalBox(PreviewSize)->SetHorizontalAlignment(HAlign_Center);
	ItemPreview->GetParent()->SetVisibility(ESlateVisibility::Collapsed);
	RecipeDetailsBox = WidgetTree->ConstructWidget<UVerticalBox>();
	DetailPanel->AddChildToVerticalBox(RecipeDetailsBox);
	RecipeDetailsBox->SetVisibility(ESlateVisibility::Collapsed);
	DetailsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryDetails"));
	DetailsText->SetAutoWrapText(true);
	auto DetailsFont = DetailsText->GetFont(); DetailsFont.Size = 15; DetailsText->SetFont(DetailsFont);
	DetailPanel->AddChildToVerticalBox(DetailsText)->SetPadding(FMargin(0, 12));
	EquipmentActionButton = WidgetTree->ConstructWidget<UEWInventoryActionButton>(UEWInventoryActionButton::StaticClass(), TEXT("EquipmentAction"));
	EquipmentActionText = WidgetTree->ConstructWidget<UTextBlock>();
	EquipmentActionButton->SetContent(EquipmentActionText);
	EquipmentActionButton->OnClicked.AddDynamic(this, &UEWInventoryWidget::PerformEquipmentAction);
	DetailPanel->AddChildToVerticalBox(EquipmentActionButton);
	FoodActionButton = WidgetTree->ConstructWidget<UEWInventoryActionButton>(UEWInventoryActionButton::StaticClass(), TEXT("FoodAction"));
	auto* FoodLabel = WidgetTree->ConstructWidget<UTextBlock>();
	FoodLabel->SetText(FText::FromString(TEXT("Eat (R / X)")));
	FoodActionButton->SetContent(FoodLabel);
	FoodActionButton->OnClicked.AddDynamic(this, &UEWInventoryWidget::PerformFoodAction);
	DetailPanel->AddChildToVerticalBox(FoodActionButton);
	EquipmentResultText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("EquipmentResult"));
	EquipmentResultText->SetAutoWrapText(true);
	DetailPanel->AddChildToVerticalBox(EquipmentResultText);

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
		auto* ButtonSlot = Buttons->AddChildToHorizontalBox(Button);
		ButtonSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); ButtonSlot->SetPadding(FMargin(2));
		HotbarButtons.Add(Button); HotbarButtonLabels.Add(Text);
	}
}

void UEWInventoryWidget::BuildCharacterPanel(UVerticalBox* Into)
{
	auto Heading = [&](const TCHAR* Title, float Above)
	{
		auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(Title));
		auto Font = Label->GetFont(); Font.Size = 14; Font.LetterSpacing = 200; Label->SetFont(Font);
		Label->SetColorAndOpacity(FSlateColor(FLinearColor(.88f, .86f, .8f)));
		Into->AddChildToVerticalBox(Label)->SetPadding(FMargin(0, Above, 0, 6));
	};
	auto Line = [&](int32 Size, const FLinearColor& Colour)
	{
		auto* Text = WidgetTree->ConstructWidget<UTextBlock>(); Text->SetAutoWrapText(true); Text->SetColorAndOpacity(FSlateColor(Colour));
		auto Font = Text->GetFont(); Font.Size = Size; Text->SetFont(Font); return Text;
	};
	// Who they are: name, a line under it, level and experience.
	NameText = Line(26, FLinearColor::White); Into->AddChildToVerticalBox(NameText);
	SubtitleText = Line(14, FLinearColor(.7f, .76f, .82f)); Into->AddChildToVerticalBox(SubtitleText)->SetPadding(FMargin(0, 0, 0, 10));
	LevelValue = Line(20, FLinearColor(.95f, .88f, .6f)); Into->AddChildToVerticalBox(LevelValue)->SetPadding(FMargin(0, 0, 0, 4));
	LevelBar = WidgetTree->ConstructWidget<UProgressBar>(); LevelBar->SetFillColorAndOpacity(FLinearColor(.45f, .78f, .95f));
	auto* LevelBarSize = WidgetTree->ConstructWidget<USizeBox>(); LevelBarSize->SetHeightOverride(8); LevelBarSize->SetContent(LevelBar);
	Into->AddChildToVerticalBox(LevelBarSize)->SetPadding(FMargin(0, 0, 0, 4));
	PointsValue = Line(13, FLinearColor(.75f, .8f, .86f)); Into->AddChildToVerticalBox(PointsValue);

	Heading(TEXT("EQUIPMENT"), 18);
	EquippedBox = WidgetTree->ConstructWidget<UWrapBox>(); EquippedBox->SetInnerSlotPadding(FVector2D(4, 4));
	Into->AddChildToVerticalBox(EquippedBox);
	ArmorText = Line(13, FLinearColor(.75f, .8f, .86f)); Into->AddChildToVerticalBox(ArmorText)->SetPadding(FMargin(0, 8, 0, 0));

	Heading(TEXT("WORLD"), 18);
	ClimateValue = Line(14, FLinearColor::White); Into->AddChildToVerticalBox(ClimateValue)->SetPadding(FMargin(0, 0, 0, 4));
	HumidityBar = WidgetTree->ConstructWidget<UProgressBar>(); HumidityBar->SetFillColorAndOpacity(FLinearColor(.35f, .7f, .75f));
	auto* HumiditySize = WidgetTree->ConstructWidget<USizeBox>(); HumiditySize->SetHeightOverride(6); HumiditySize->SetContent(HumidityBar);
	Into->AddChildToVerticalBox(HumiditySize);

	// Character stats: two columns, a large white icon, a small label and the value.
	Heading(TEXT("CHARACTER STATS"), 20);
	auto* Grid = WidgetTree->ConstructWidget<UUniformGridPanel>(); Grid->SetSlotPadding(FMargin(3));
	Into->AddChildToVerticalBox(Grid);
	struct FStatTile { const TCHAR* Name; int32 Icon; };
	// Icon kinds are EWHudIcon silhouettes; -1 draws the short text in its place.
	const FStatTile Tiles[] = {{TEXT("HEALTH"), 0}, {TEXT("STAMINA"), 1}, {TEXT("FOOD"), 2}, {TEXT("WATER"), 3}, {TEXT("OXYGEN"), -1}, {TEXT("FORTITUDE"), 4}, {TEXT("WEIGHT"), 8}, {TEXT("INTELLIGENCE"), -2}};
	for (int32 Index = 0; Index < UE_ARRAY_COUNT(Tiles); ++Index)
	{
		auto* Cell = WidgetTree->ConstructWidget<UBorder>(); Cell->SetPadding(FMargin(10, 8)); Cell->SetBrushColor(FLinearColor(.045f, .055f, .066f, .9f));
		auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>(); Cell->SetContent(Row);
		auto* IconSize = WidgetTree->ConstructWidget<USizeBox>(); IconSize->SetWidthOverride(44); IconSize->SetHeightOverride(44);
		if (Tiles[Index].Icon >= 0)
		{
			const int32 Key = 200 + Tiles[Index].Icon;
			if (!FallbackIcons.Contains(Key)) FallbackIcons.Add(Key, EWHudIcon::Make(Tiles[Index].Icon, false));
			auto* Image = WidgetTree->ConstructWidget<UImage>(); Image->SetBrushFromTexture(FallbackIcons[Key]); Image->SetColorAndOpacity(FLinearColor::White);
			IconSize->SetContent(Image);
		}
		else
		{
			auto* Glyph = Line(Tiles[Index].Icon == -1 ? 22 : 17, FLinearColor::White); Glyph->SetText(FText::FromString(Tiles[Index].Icon == -1 ? TEXT("O2") : TEXT("INT")));
			Glyph->SetJustification(ETextJustify::Center); Glyph->SetAutoWrapText(false);
			auto* GlyphBox = WidgetTree->ConstructWidget<UBorder>(); GlyphBox->SetBrushColor(FLinearColor(0, 0, 0, 0)); GlyphBox->SetHorizontalAlignment(HAlign_Center); GlyphBox->SetVerticalAlignment(VAlign_Center);
			GlyphBox->SetContent(Glyph); IconSize->SetContent(GlyphBox);
		}
		Row->AddChildToHorizontalBox(IconSize)->SetPadding(FMargin(0, 0, 10, 0));
		auto* Words = WidgetTree->ConstructWidget<UVerticalBox>(); Row->AddChildToHorizontalBox(Words)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		auto* Name = Line(10, FLinearColor(.6f, .66f, .72f)); Name->SetText(FText::FromString(Tiles[Index].Name)); Name->SetAutoWrapText(false); Words->AddChildToVerticalBox(Name);
		auto* Value = Line(16, FLinearColor::White); Value->SetAutoWrapText(false); Words->AddChildToVerticalBox(Value);
		UProgressBar* Bar = nullptr;
		if (Index < 4)
		{
			static const FLinearColor Fill[] = {FLinearColor(.72f, .12f, .1f), FLinearColor(.86f, .68f, .12f), FLinearColor(.78f, .42f, .14f), FLinearColor(.18f, .46f, .8f)};
			Bar = WidgetTree->ConstructWidget<UProgressBar>(); Bar->SetFillColorAndOpacity(Fill[Index]);
			auto* BarSize = WidgetTree->ConstructWidget<USizeBox>(); BarSize->SetHeightOverride(5); BarSize->SetContent(Bar);
			Words->AddChildToVerticalBox(BarSize)->SetPadding(FMargin(0, 3, 0, 0));
		}
		if (auto* GridSlot = Grid->AddChildToUniformGrid(Cell, Index / 2, Index % 2)) { GridSlot->SetHorizontalAlignment(HAlign_Fill); GridSlot->SetVerticalAlignment(VAlign_Fill); }
		TileValues.Add(Value); TileBars.Add(Bar);
	}

	// Stat points (owner, October 22 and 25): faint and dead until a point can be spent; then C, a left-stick click or RT starts picking a stat.
	Heading(TEXT("STAT POINTS"), 20);
	StatPrompt = Line(13, FLinearColor(.95f, .85f, .45f)); Into->AddChildToVerticalBox(StatPrompt)->SetPadding(FMargin(0, 0, 0, 8));
	for (int32 Stat = 0; Stat < UEWProgressionComponent::StatCount; ++Stat)
	{
		auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
		auto* Label = Line(15, FLinearColor::White);
		Row->AddChildToHorizontalBox(Label)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		auto* Arrow = WidgetTree->ConstructWidget<UEWRecipeButton>(); Arrow->Initialize(Stat);
		Arrow->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::SpendStat);
		auto* Glyph = WidgetTree->ConstructWidget<UTextBlock>(); Glyph->SetText(FText::FromString(TEXT("▲"))); Glyph->SetJustification(ETextJustify::Center);
		{ auto F = Glyph->GetFont(); F.Size = 18; Glyph->SetFont(F); }
		Arrow->SetContent(Glyph);
		auto* ArrowSize = WidgetTree->ConstructWidget<USizeBox>(); ArrowSize->SetWidthOverride(44); ArrowSize->SetHeightOverride(40); ArrowSize->SetContent(Arrow);
		auto* ArrowSlot = Row->AddChildToHorizontalBox(ArrowSize); ArrowSlot->SetVerticalAlignment(VAlign_Center); ArrowSlot->SetPadding(FMargin(8, 0, 0, 0));
		Into->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 0, 0, 6));
		AllocValues.Add(Label); AllocArrows.Add(Arrow);
	}
}

namespace
{
	constexpr float SlotTileSize = 92.f, RecipeTileWidth = 88.f, GridGap = 4.f;
	const FLinearColor CursorGold(1.f, .85f, .35f, 1.f);
	const FLinearColor NoRing(0.f, 0.f, 0.f, 0.f);

	FString ItemNameOf(const UEWItemDefinition* Item)
	{
		return !Item ? FString() : (Item->DisplayName.IsEmpty() ? Item->ItemId.ToString() : Item->DisplayName.ToString());
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
        ItemsBox->ClearChildren(); EquippedBox->ClearChildren(); Rows.Reset(); RowRings.Reset(); RowFreshness.Reset(); DisplayedEntries.Reset(); DisplayedEquipment.Reset();
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
    DisplayedEquipment.Sort([](const FEWEquipmentEntry& A, const FEWEquipmentEntry& B) { return A.Slot < B.Slot; });
    int32 Match = INDEX_NONE, Ordinal = 0;
    for (int32 i = 0; i < DisplayedEntries.Num(); ++i)
        if (PreviousSlot == EEWEquipmentSlot::None && DisplayedEntries[i].ItemDefinition == PreviousItem && Ordinal++ == PreviousOrdinal) { Match = i; break; }
    if (PreviousSlot != EEWEquipmentSlot::None)
        for (int32 i=0; i<DisplayedEquipment.Num(); ++i) if (DisplayedEquipment[i].Slot == PreviousSlot) { Match = DisplayedEntries.Num()+i; break; }
    SelectedIndex = SelectionCount() == 0 ? INDEX_NONE : (Match != INDEX_NONE ? Match : FMath::Clamp(SelectedIndex, 0, SelectionCount()-1));
    if (PreviousItem && SelectedItem() != PreviousItem) bShowingDetails = false;
    ItemsBox->ClearChildren();
    EquippedBox->ClearChildren();
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
    // The equipment slots: worn items are tiles that can be picked, bare slots are named and empty. DisplayedEquipment is in slot order, as this loop is.
    static const EEWEquipmentSlot WornSlots[] = {EEWEquipmentSlot::Head, EEWEquipmentSlot::Chest, EEWEquipmentSlot::Hands, EEWEquipmentSlot::Legs, EEWEquipmentSlot::Feet, EEWEquipmentSlot::MainHand, EEWEquipmentSlot::OffHand};
    static const TCHAR* WornNames[] = {TEXT("HEAD"), TEXT("CHEST"), TEXT("HANDS"), TEXT("LEGS"), TEXT("FEET"), TEXT("MAIN HAND"), TEXT("OFF HAND")};
    for (int32 SlotIndex = 0; SlotIndex < UE_ARRAY_COUNT(WornSlots); ++SlotIndex)
    {
        const FEWEquipmentEntry* Worn = DisplayedEquipment.FindByPredicate([&](const FEWEquipmentEntry& E) { return E.Slot == WornSlots[SlotIndex]; });
        UImage* ItemImage = nullptr; UProgressBar* NoBar = nullptr;
        if (!Worn) { AddToGrid(EquippedBox, MakeSlotTile(nullptr, FString(), -1.f, ItemImage, NoBar, FString(), WornNames[SlotIndex])); continue; }
        UBorder* Tile = MakeSlotTile(Worn->ItemDefinition, FString(), -1.f, ItemImage, NoBar, FString::Printf(TEXT("%.1f kg"), Worn->ItemDefinition->UnitWeight));
        if (ItemImage) InventoryImages.Add(Worn->ItemDefinition, ItemImage);
        UBorder* Ring = AddToGrid(EquippedBox, Tile);
        Rows.Add(Tile); RowRings.Add(Ring); RowFreshness.Add(nullptr);
    }
    if (SelectionCount() == 0) bShowingDetails = false;
    UpdateSelection();
    RefreshCrafting();
}

void UEWInventoryWidget::ResetToInventoryPage()
{
    SelectedSection = 0; bCraftingOpen = false; StatFocus = INDEX_NONE; HotbarPick = INDEX_NONE; SelectedRecipeIndex = 0; bShowingDetails = false;
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
    if (SortButton) SortButton->SetBackgroundColor(bSortByName ? FLinearColor(.5f, .45f, .2f) : FLinearColor(.07f, .085f, .1f));
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
    if (DisplayedRecipes.IsEmpty()) return;
    bCraftingOpen = true; bShowingDetails = false; HotbarPick = INDEX_NONE;
    RefreshCrafting();
    SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::FocusInventory()
{
    bCraftingOpen = false; bShowingDetails = false;
    RefreshCrafting();
    SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::SelectSection(int32 Index)
{
    if (!SectionButtons.IsValidIndex(Index)) return;
    SelectedSection = Index; TabCursor = Index; bTabFocus = false; bCraftingOpen = false; bShowingDetails = false; StatFocus = INDEX_NONE; HotbarPick = INDEX_NONE;
    RefreshCrafting(); SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::SelectRecipe(int32 Index)
{
    SelectedRecipeIndex = Index; SelectedSection = 0; bCraftingOpen = true; bShowingDetails = false; HotbarPick = INDEX_NONE;
    RefreshCrafting();
}

int32 UEWInventoryWidget::ItemColumns() const
{
    const float Width = ItemsScroll ? ItemsScroll->GetCachedGeometry().GetLocalSize().X : 0.f;
    return Width < 120.f ? 6 : FMath::Max(1, FMath::FloorToInt((Width - 20.f) / (SlotTileSize + GridGap)));
}
int32 UEWInventoryWidget::RecipeColumns() const
{
    const float Width = CraftScroll ? CraftScroll->GetCachedGeometry().GetLocalSize().X : 0.f;
    return Width < 120.f ? 6 : FMath::Max(1, FMath::FloorToInt((Width - 20.f) / (RecipeTileWidth + GridGap)));
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
        if (SelectedIndex + Step < ItemCount) { if (ItemCount > 0 && Step < 0) Select(ItemCount - 1); }
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
        SectionButtons[Index]->SetBackgroundColor(bCursor ? FLinearColor(1.f, .85f, .35f) : bActive ? FLinearColor(.82f, .84f, .86f) : FLinearColor(.07f, .08f, .09f, .85f));
        if (SectionLabels.IsValidIndex(Index)) SectionLabels[Index]->SetColorAndOpacity(FSlateColor(bActive || bCursor ? FLinearColor(.05f, .06f, .07f) : FLinearColor(.82f, .84f, .86f)));
    }
    const ESlateVisibility InventoryPage = SelectedSection == 0 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed;
    BrowserHost->SetVisibility(InventoryPage); SurvivorPanel->SetVisibility(InventoryPage); RightHost->SetVisibility(InventoryPage);
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
    RecipeDetailsBox->SetVisibility(bCraftingOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    DetailsText->SetVisibility(bCraftingOpen ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    if (bCraftingOpen)
    {
        EquipmentActionButton->SetVisibility(ESlateVisibility::Collapsed);
        FoodActionButton->SetVisibility(ESlateVisibility::Collapsed);
        HotbarAssignments->SetVisibility(ESlateVisibility::Collapsed);
    }
    else UpdateSelection();
    CraftingBox->ClearChildren(); RecipeDetailsBox->ClearChildren(); CraftButton=nullptr; DisplayedRecipes.Reset(); MaterialImages.Reset();
    bool bAnyRecipe = false;
    if (BoundInventory) for (auto* Recipe : BoundInventory->GetAvailableRecipes())
        if (Recipe && Recipe->Output)
        {
            bAnyRecipe = true;
            if (RecipeFilter.IsEmpty() || ItemNameOf(Recipe->Output).Contains(RecipeFilter, ESearchCase::IgnoreCase)) DisplayedRecipes.Add(Recipe);
        }
    if (DisplayedRecipes.IsEmpty())
    {
        if (bCraftingOpen) { bCraftingOpen = false; RecipeDetailsBox->SetVisibility(ESlateVisibility::Collapsed); DetailsText->SetVisibility(ESlateVisibility::Visible); UpdateSelection(); }
        auto* Empty = WidgetTree->ConstructWidget<UTextBlock>();
        Empty->SetText(FText::FromString(bAnyRecipe ? TEXT("No recipe matches that search.") : TEXT("Recipes unlock after the innkeeper introduction.")));
        Empty->SetColorAndOpacity(FSlateColor(FLinearColor(.6f, .66f, .72f)));
        CraftingBox->AddChildToVerticalBox(Empty); return;
    }
    SelectedRecipeIndex = FMath::Clamp(SelectedRecipeIndex, 0, DisplayedRecipes.Num()-1);
    auto* RecipeGrid = WidgetTree->ConstructWidget<UWrapBox>(); RecipeGrid->SetInnerSlotPadding(FVector2D(GridGap, GridGap));
    CraftingBox->AddChildToVerticalBox(RecipeGrid);
    UWidget* SelectedTile = nullptr;
    for (int32 Index=0; Index<DisplayedRecipes.Num(); ++Index)
    {
        auto* Recipe = DisplayedRecipes[Index].Get();
        const bool bPicked = Index == SelectedRecipeIndex;
        auto* Ring = WidgetTree->ConstructWidget<UBorder>(); Ring->SetPadding(FMargin(2));
        Ring->SetBrushColor(bPicked && bCraftingOpen ? CursorGold : NoRing);
        auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
        Button->SetBackgroundColor(bPicked ? FLinearColor(.2f, .22f, .25f, 1.f) : FLinearColor(.05f, .06f, .075f, 1.f));
        Button->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::SelectRecipe);
        Button->OnRecipeHovered.AddDynamic(this, &UEWInventoryWidget::HoverRecipe);
        Button->EnableHover();
        auto* Row = WidgetTree->ConstructWidget<UVerticalBox>();
        if (auto* Texture = ResolveIcon(Recipe->Output))
        {
            auto* Icon = WidgetTree->ConstructWidget<UImage>(); Icon->SetBrushFromTexture(Texture);
            auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(46); Size->SetHeightOverride(46);
            Size->SetContent(Icon); Row->AddChildToVerticalBox(Size)->SetHorizontalAlignment(HAlign_Center);
        }
        auto* Name = WidgetTree->ConstructWidget<UTextBlock>();
        Name->SetText(Recipe->Output->DisplayName);
        Name->SetAutoWrapText(true); Name->SetJustification(ETextJustify::Center); auto Font=Name->GetFont(); Font.Size=10; Name->SetFont(Font);
        Row->AddChildToVerticalBox(Name); Button->SetContent(Row); Ring->SetContent(Button);
        auto* TileSize=WidgetTree->ConstructWidget<USizeBox>(); TileSize->SetWidthOverride(RecipeTileWidth); TileSize->SetMinDesiredHeight(84); TileSize->SetContent(Ring);
        RecipeGrid->AddChildToWrapBox(TileSize);
        if (bPicked) SelectedTile = TileSize;
    }
    if (bCraftingOpen && SelectedTile) CraftScroll->ScrollWidgetIntoView(SelectedTile, false);
    auto* Recipe = DisplayedRecipes[SelectedRecipeIndex].Get();
    auto* Heading=WidgetTree->ConstructWidget<UTextBlock>();
    Heading->SetText(Recipe->Output->DisplayName);
    Heading->SetAutoWrapText(true); auto HeadingFont=Heading->GetFont(); HeadingFont.Size=21; Heading->SetFont(HeadingFont);
    RecipeDetailsBox->AddChildToVerticalBox(Heading)->SetPadding(FMargin(0,0,0,12));
    if (auto* Texture = ResolveIcon(Recipe->Output))
    {
        auto* Preview = WidgetTree->ConstructWidget<UImage>(); Preview->SetBrushFromTexture(Texture);
        auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(112); Size->SetHeightOverride(112);
        Size->SetContent(Preview); RecipeDetailsBox->AddChildToVerticalBox(Size)->SetHorizontalAlignment(HAlign_Center);
    }
    MaterialImages.Reset();
    FString Details = TEXT("Inventory crafting · Unlocked");
    auto* MaterialsHeading=WidgetTree->ConstructWidget<UTextBlock>();
    MaterialsHeading->SetText(FText::FromString(TEXT("REQUIRED MATERIALS")));
    RecipeDetailsBox->AddChildToVerticalBox(MaterialsHeading)->SetPadding(FMargin(0,14,0,8));
    for (const auto& Cost : Recipe->Ingredients) if (Cost.Item)
    {
        auto* MaterialLabel = WidgetTree->ConstructWidget<UTextBlock>();
        MaterialLabel->SetText(FText::FromString(FString::Printf(TEXT("%s: %d / %d"), *Cost.Item->DisplayName.ToString(),
            BoundInventory->GetItemCount(Cost.Item), Cost.Quantity)));
        MaterialLabel->SetAutoWrapText(true);
        auto MaterialFont=MaterialLabel->GetFont(); MaterialFont.Size=16; MaterialLabel->SetFont(MaterialFont);
        MaterialLabel->SetColorAndOpacity(FSlateColor(BoundInventory->GetItemCount(Cost.Item)>=Cost.Quantity
            ? FLinearColor(.45f,.85f,.55f) : FLinearColor(1.f,.4f,.35f)));
        UImage* MaterialImage = nullptr;
        RecipeDetailsBox->AddChildToVerticalBox(MakeItemRow(Cost.Item, MaterialLabel, MaterialImage));
        if (MaterialImage) MaterialImages.Add(Cost.Item, MaterialImage);
    }
    CraftingDetails = WidgetTree->ConstructWidget<UTextBlock>(); CraftingDetails->SetText(FText::FromString(Details));
    CraftingDetails->SetAutoWrapText(true); auto InfoFont=CraftingDetails->GetFont(); InfoFont.Size=16; CraftingDetails->SetFont(InfoFont);
    RecipeDetailsBox->AddChildToVerticalBox(CraftingDetails);
    CraftButton = WidgetTree->ConstructWidget<UEWInventoryActionButton>();
    auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(TEXT("Craft one (Enter / A)")));
    CraftButton->SetContent(Label); CraftButton->OnClicked.AddDynamic(this, &UEWInventoryWidget::PerformCraft);
    const EEWCraftResult Readiness = BoundInventory->GetCraftReadiness(Recipe);
    CraftButton->SetIsEnabled(Readiness==EEWCraftResult::Success);
    CraftButton->SetToolTipText(FText::FromString(Readiness==EEWCraftResult::MissingIngredients ? TEXT("Not enough materials")
        : Readiness==EEWCraftResult::InventoryFull ? TEXT("Make room in your inventory")
        : Readiness==EEWCraftResult::Success ? TEXT("Craft one item") : TEXT("Recipe unavailable")));
    if (Readiness!=EEWCraftResult::Success)
        CraftingDetails->SetText(FText::FromString(Details + TEXT("\n") + (Readiness==EEWCraftResult::MissingIngredients ? TEXT("Not enough materials")
            : Readiness==EEWCraftResult::InventoryFull ? TEXT("Make room in your inventory") : TEXT("Recipe unavailable"))));
    RecipeDetailsBox->AddChildToVerticalBox(CraftButton);
    // The work in progress: a bar filling over the recipe's time.
    CraftBar = WidgetTree->ConstructWidget<UProgressBar>(); CraftBar->SetFillColorAndOpacity(FLinearColor(.9f,.7f,.25f));
    auto* CraftBarSize = WidgetTree->ConstructWidget<USizeBox>(); CraftBarSize->SetHeightOverride(10); CraftBarSize->SetContent(CraftBar);
    RecipeDetailsBox->AddChildToVerticalBox(CraftBarSize)->SetPadding(FMargin(0,8,0,2));
    CraftBarText = WidgetTree->ConstructWidget<UTextBlock>(); { auto F = CraftBarText->GetFont(); F.Size = 14; CraftBarText->SetFont(F); }
    RecipeDetailsBox->AddChildToVerticalBox(CraftBarText);
    CraftBar->SetPercent(GetCraftProgress());
    if (Recipe->CraftSeconds > .02f) CraftBarText->SetText(CraftSecondsLeft > 0.f ? FText::Format(NSLOCTEXT("Elitewake", "CraftTimeLeft", "Crafting... {0} s"), FMath::CeilToInt(CraftSecondsLeft))
        : FText::Format(NSLOCTEXT("Elitewake", "CraftTime", "Takes {0} s"), FMath::RoundToInt(Recipe->CraftSeconds)));
}
UBorder* UEWInventoryWidget::MakeSlotTile(UEWItemDefinition* Item, const FString& Corner, float Freshness, UImage*& Image, UProgressBar*& FreshBar, const FString& Weight, const FString& EmptyLabel)
{
    Image = nullptr; FreshBar = nullptr;
    auto* Tile = WidgetTree->ConstructWidget<UBorder>();
    Tile->SetPadding(FMargin(3));
    Tile->SetBrushColor(Item ? FLinearColor(.045f,.06f,.075f,1) : FLinearColor(.025f,.032f,.042f,.55f));
    if (!Item)
    {
        if (!EmptyLabel.IsEmpty())
        {
            auto* SlotName = WidgetTree->ConstructWidget<UTextBlock>(); SlotName->SetText(FText::FromString(EmptyLabel)); SlotName->SetJustification(ETextJustify::Center);
            SlotName->SetColorAndOpacity(FSlateColor(FLinearColor(.42f, .46f, .5f))); auto SlotFont = SlotName->GetFont(); SlotFont.Size = 10; SlotName->SetFont(SlotFont);
            Tile->SetHorizontalAlignment(HAlign_Center); Tile->SetVerticalAlignment(VAlign_Center); Tile->SetContent(SlotName);
        }
        return Tile;
    }
    auto* Layers = WidgetTree->ConstructWidget<UOverlay>();
    Tile->SetContent(Layers);
    Image = WidgetTree->ConstructWidget<UImage>(); Image->SetBrushFromTexture(ResolveIcon(Item));
    auto* IconSize = WidgetTree->ConstructWidget<USizeBox>(); IconSize->SetWidthOverride(54); IconSize->SetHeightOverride(54);
    IconSize->SetContent(Image);
    auto* IconSlot = Layers->AddChildToOverlay(IconSize);
    IconSlot->SetHorizontalAlignment(HAlign_Center); IconSlot->SetVerticalAlignment(VAlign_Top); IconSlot->SetPadding(FMargin(0,4,0,0));
    // The quantity, top right.
    auto* Count = WidgetTree->ConstructWidget<UTextBlock>(); Count->SetText(FText::FromString(Corner));
    auto CountFont = Count->GetFont(); CountFont.Size = 12; Count->SetFont(CountFont);
    Count->SetShadowOffset(FVector2D(1,1)); Count->SetShadowColorAndOpacity(FLinearColor(0,0,0,.9f));
    auto* CountSlot = Layers->AddChildToOverlay(Count);
    CountSlot->SetHorizontalAlignment(HAlign_Right); CountSlot->SetVerticalAlignment(VAlign_Top);
    // Along the bottom: the name, trailing off if it is long, and the weight of the stack.
    auto* Bottom = WidgetTree->ConstructWidget<UHorizontalBox>();
    auto* Name = WidgetTree->ConstructWidget<UTextBlock>();
    Name->SetText(Item->DisplayName.IsEmpty() ? FText::FromName(Item->ItemId) : Item->DisplayName);
    auto NameFont = Name->GetFont(); NameFont.Size = 9; Name->SetFont(NameFont);
    Name->SetJustification(ETextJustify::Left); Name->SetClipping(EWidgetClipping::ClipToBounds);
    Name->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
    Bottom->AddChildToHorizontalBox(Name)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    if (!Weight.IsEmpty())
    {
        auto* WeightText = WidgetTree->ConstructWidget<UTextBlock>(); WeightText->SetText(FText::FromString(Weight));
        WeightText->SetColorAndOpacity(FSlateColor(FLinearColor(.62f, .68f, .74f))); auto WeightFont = WeightText->GetFont(); WeightFont.Size = 9; WeightText->SetFont(WeightFont);
        Bottom->AddChildToHorizontalBox(WeightText)->SetPadding(FMargin(4, 0, 0, 0));
    }
    auto* BottomSlot = Layers->AddChildToOverlay(Bottom);
    BottomSlot->SetHorizontalAlignment(HAlign_Fill); BottomSlot->SetVerticalAlignment(VAlign_Bottom);
    BottomSlot->SetPadding(FMargin(0,0,0,Freshness >= 0.f ? 6 : 0));
    if (Freshness >= 0.f)
    {
        FreshBar = WidgetTree->ConstructWidget<UProgressBar>();
        FreshBar->SetPercent(Freshness); FreshBar->SetFillColorAndOpacity(FLinearColor(.25f,.8f,.35f));
        auto* BarSize = WidgetTree->ConstructWidget<USizeBox>(); BarSize->SetHeightOverride(4); BarSize->SetContent(FreshBar);
        auto* BarSlot = Layers->AddChildToOverlay(BarSize);
        BarSlot->SetHorizontalAlignment(HAlign_Fill); BarSlot->SetVerticalAlignment(VAlign_Bottom);
    }
    return Tile;
}

UBorder* UEWInventoryWidget::AddToGrid(UWrapBox* Grid, UBorder* Tile)
{
    // The ring around a tile is the controller cursor: clear until the tile is picked, then gold.
    auto* Ring = WidgetTree->ConstructWidget<UBorder>(); Ring->SetPadding(FMargin(3)); Ring->SetBrushColor(NoRing);
    Ring->SetContent(Tile);
    auto* Size = WidgetTree->ConstructWidget<USizeBox>();
    Size->SetWidthOverride(SlotTileSize); Size->SetHeightOverride(SlotTileSize); Size->SetContent(Ring);
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
}
void UEWInventoryWidget::SpendStat(int32 StatIndex)
{
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    if (!Progress || Progress->GetUnspentPoints() <= 0 || StatIndex < 0 || StatIndex >= UEWProgressionComponent::StatCount) return;
    if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->RequestSpendStatPoint(static_cast<EEWStat>(StatIndex));
}
void UEWInventoryWidget::RefreshProgression()
{
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    if (!Progress || !LevelValue || !LevelBar || !PointsValue || AllocArrows.Num() != UEWProgressionComponent::StatCount) return;
    LevelValue->SetText(FText::Format(NSLOCTEXT("Elitewake", "LevelFormat", "LEVEL {0}"), Progress->GetLevel()));
    LevelBar->SetPercent(Progress->IsAtMaxLevel() ? 1.f : FMath::Clamp(float(Progress->GetExperience()) / FMath::Max(1, Progress->GetExperienceForNextLevel()), 0.f, 1.f));
    const int32 Points = Progress->GetUnspentPoints();
    PointsValue->SetText(Progress->IsAtMaxLevel() ? NSLOCTEXT("Elitewake", "MaxLevel", "Highest level reached")
        : FText::Format(NSLOCTEXT("Elitewake", "PointsFormat", "Experience {0} / {1}     Stat points to spend: {2}"), Progress->GetExperience(), Progress->GetExperienceForNextLevel(), Points));
    if (StatPrompt)
    {
        StatPrompt->SetText(Points > 0
            ? FText::Format(NSLOCTEXT("Elitewake", "StatPromptReady", "{0} point(s) to spend. Click an arrow, or press C, left-stick click or RT, pick a stat with Up/Down or the d-pad, then Enter or A."), Points)
            : NSLOCTEXT("Elitewake", "StatPromptNone", "You earn a point at each level. C, left-stick click or RT picks a stat once you have one."));
        StatPrompt->SetColorAndOpacity(FSlateColor(Points > 0 ? FLinearColor(.95f, .85f, .45f) : FLinearColor(.55f, .6f, .66f)));
    }
    for (int32 Stat = 0; Stat < UEWProgressionComponent::StatCount; ++Stat)
    {
        const EEWStat Which = static_cast<EEWStat>(Stat);
        AllocValues[Stat]->SetText(FText::Format(NSLOCTEXT("Elitewake", "StatRow", "{0}{1}  {2}\n{3}"), FText::FromString(Stat == StatFocus ? TEXT("\u25BA ") : TEXT("")),
            UEWProgressionComponent::StatName(Which), Progress->GetStatPoints(Which), Progress->StatEffect(Which)));
        AllocValues[Stat]->SetColorAndOpacity(FSlateColor(Stat == StatFocus ? FLinearColor(1.f, .85f, .35f) : FLinearColor::White));
        const bool bLive = Points > 0;
        AllocArrows[Stat]->SetIsEnabled(bLive);
        AllocArrows[Stat]->SetRenderOpacity(bLive ? 1.f : .25f);
        AllocArrows[Stat]->SetBackgroundColor(Stat == StatFocus ? FLinearColor(1.f, .85f, .35f) : (bLive ? FLinearColor(.2f, .6f, .35f) : FLinearColor(.1f, .12f, .14f)));
    }
}

void UEWInventoryWidget::PerformCraft()
{
    if (!DisplayedRecipes.IsValidIndex(SelectedRecipeIndex) || !IsCraftActionEnabled()) return;
    if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->RequestCraft(DisplayedRecipes[SelectedRecipeIndex]);
}
bool UEWInventoryWidget::IsCraftActionEnabled() const
{
    return bCraftingOpen && CraftButton && CraftButton->GetIsEnabled() && CraftSecondsLeft <= 0.f;
}
void UEWInventoryWidget::ShowCraftStarted(UEWCraftingRecipe* Recipe, float Seconds)
{
    CraftSecondsTotal = CraftSecondsLeft = FMath::Max(0.f, Seconds);
    if (EquipmentResultText && Recipe && Recipe->Output && Seconds > .02f)
        EquipmentResultText->SetText(FText::Format(NSLOCTEXT("Elitewake", "CraftingNow", "Crafting {0}..."), Recipe->Output->DisplayName));
    RefreshCrafting();
}
void UEWInventoryWidget::HoverRecipe(int32 Index)
{
    if ((!bCraftingOpen || Index != SelectedRecipeIndex) && CraftSecondsLeft <= 0.f) SelectRecipe(Index);
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
    CraftSecondsLeft = CraftSecondsTotal = 0.f;
    FString Message;
    switch (Result)
    {
        case EEWCraftResult::Success: Message=TEXT("Item crafted"); break;
        case EEWCraftResult::MissingIngredients: Message=TEXT("Not enough materials"); break;
        case EEWCraftResult::InventoryFull: Message=TEXT("Make room in your inventory"); break;
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
	SummaryText->SetText(FText::FromString(FString::Printf(TEXT("Slots %d / %d     Weight %.1f / %.1f kg"),
		Inventory->GetUsedSlotCount(), Inventory->GetMaxSlotCount(), Carried, MaxWeight)));
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Survival = Character ? Character->GetSurvivalComponent() : nullptr;
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    if (Survival && TileValues.Num() == 8)
    {
        const float Max[] = {Survival->GetMaxHealth(), Survival->GetMaxStamina(), 100.f, 100.f};
        const float Now[] = {Survival->GetHealth(), Survival->GetStamina(), Survival->GetHunger(), Survival->GetHydration()};
        for (int32 i = 0; i < 4; ++i)
        {
            TileValues[i]->SetText(FText::FromString(i < 2 ? FString::Printf(TEXT("%.0f / %.0f"), Now[i], Max[i]) : FString::Printf(TEXT("%.0f%%"), Now[i])));
            if (TileBars[i]) TileBars[i]->SetPercent(Max[i] > 0.f ? FMath::Clamp(Now[i] / Max[i], 0.f, 1.f) : 0.f);
        }
        // Oxygen and intelligence are not mechanics yet; their tiles hold the place the layout gives them.
        TileValues[4]->SetText(FText::FromString(TEXT("\u2014")));
        TileValues[5]->SetText(Progress ? FText::Format(NSLOCTEXT("Elitewake", "FortitudeTile", "{0} pts"), Progress->GetStatPoints(EEWStat::Fortitude)) : FText::FromString(TEXT("\u2014")));
        TileValues[6]->SetText(FText::FromString(FString::Printf(TEXT("%.1f / %.0f kg"), Carried, MaxWeight)));
        TileValues[7]->SetText(FText::FromString(TEXT("\u2014")));
        if (ClimateValue && HumidityBar)
        {
            const FEWClimate C = Survival->GetClimate();
            FString State = Survival->IsFreezing() ? TEXT("  Freezing") : Survival->IsOverheating() ? TEXT("  Overheating")
                : Survival->GetTargetBodyTemperature() < Survival->GetBodyTemperature() - .2f ? TEXT("  Cooling")
                : Survival->GetTargetBodyTemperature() > Survival->GetBodyTemperature() + .2f ? TEXT("  Warming") : TEXT("");
            ClimateValue->SetText(FText::FromString(FString::Printf(TEXT("%s  %.0f\u00B0C   Humidity %.0f%%\nBody %.1f\u00B0C%s\nCharacter age  not tracked yet"),
                *AEWClimateRegion::RegionName(C.Region).ToString(), Survival->GetFeltTemperature(), C.Humidity, Survival->GetBodyTemperature(), *State)));
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
    if (ArmorText) ArmorText->SetText(FText::FromString(TEXT("Armor  \u2014")));
    RefreshProgression();

}

void UEWInventoryWidget::Select(int32 Index)
{
    if (SelectionCount() == 0) return;
    Index = FMath::Clamp(Index, 0, SelectionCount()-1);
    // Picking an item takes the cursor back from the crafting list.
    const bool bLeftCrafting = bCraftingOpen;
    if (bLeftCrafting) { bCraftingOpen = false; bShowingDetails = false; SelectedIndex = Index; RefreshCrafting(); return; }
    if (Index != SelectedIndex) { SelectedIndex = Index; bShowingDetails = false; UpdateSelection(); }
}

void UEWInventoryWidget::UpdateSelection()
{
    for (int32 i=0; i<Rows.Num(); ++i)
    {
        const bool bPicked = i == SelectedIndex;
        Rows[i]->SetBrushColor(bPicked ? FLinearColor(.2f,.23f,.27f,1) : FLinearColor(.045f,.06f,.075f,1));
        if (RowRings.IsValidIndex(i)) RowRings[i]->SetBrushColor(bPicked && !bCraftingOpen ? CursorGold : NoRing);     // the controller cursor
    }
    ItemPreview->GetParent()->SetVisibility(ESlateVisibility::Collapsed);
    if (!DetailsText) return;
    UEWItemDefinition* Item = SelectedItem();
    const bool bEquippable = Item && Item->EquipmentSlot != EEWEquipmentSlot::None;
    FoodActionButton->SetVisibility(bShowingDetails && Item && Item->bFoodConsumptionEnabled ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    EquipmentActionButton->SetVisibility(bShowingDetails && bEquippable ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    EquipmentActionText->SetText(FText::FromString(SelectedEquipmentSlot() == EEWEquipmentSlot::None ? TEXT("Equip") : TEXT("Unequip")));
    DetailsText->SetText(FText::FromString(SelectedIndex == INDEX_NONE ? TEXT("Your inventory is empty.\nGather supplies to begin.") : TEXT("Select an item to view its details.")));
    if (bShowingDetails) ConfirmSelection();
    RefreshHotbarAssignments();
    if (Rows.IsValidIndex(SelectedIndex)) ItemsScroll->ScrollWidgetIntoView(Rows[SelectedIndex], true);
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
    RefreshHotbarAssignments();
    DetailsText->SetText(FText::FromString(FString::Printf(TEXT("%s\n%s\nQuantity %d    Unit weight %.1f kg    Stack limit %d"),
        *Item->DisplayName.ToString(), *Item->Description.ToString(), Quantity,
        Item->UnitWeight, Item->MaxStackSize)));
    EquipmentActionButton->SetVisibility(Item->EquipmentSlot != EEWEquipmentSlot::None ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    EquipmentActionText->SetText(FText::FromString(SelectedEquipmentSlot() == EEWEquipmentSlot::None ? TEXT("Equip") : TEXT("Unequip")));
    // Details change the list's available height; reveal the selected row after that layout change.
    if (Rows.IsValidIndex(SelectedIndex)) ItemsScroll->ScrollWidgetIntoView(Rows[SelectedIndex], true, EDescendantScrollDestination::Center);
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
    if (StatFocus != INDEX_NONE && !bSectionKey)
    {
        if (Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up) SetStatFocus((StatFocus + UEWProgressionComponent::StatCount - 1) % UEWProgressionComponent::StatCount);
        else if (Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down) SetStatFocus((StatFocus + 1) % UEWProgressionComponent::StatCount);
        else if (Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom) { if (!Event.IsRepeat()) SpendStat(StatFocus); }
        else if (Key==EKeys::Escape || Key==EKeys::Gamepad_FaceButton_Right) SetStatFocus(INDEX_NONE);
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
    if (Key == EKeys::Enter || Key == EKeys::Gamepad_FaceButton_Bottom) { ConfirmSelection(); return FReply::Handled(); }
    if (Key == EKeys::R || Key == EKeys::Gamepad_FaceButton_Left)
    {
        if (bCraftingOpen) return FReply::Handled();
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
        if (Dy) SetStatFocus((StatFocus + (Dy > 0 ? 1 : UEWProgressionComponent::StatCount - 1)) % UEWProgressionComponent::StatCount);
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
    if (Event.GetKey() == EKeys::Gamepad_LeftY)
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
    // Use settled geometry: confirmation may shrink the scroll viewport after the input event.
    if (RevealSelectionAfterFrames > 0 && --RevealSelectionAfterFrames == 0 && Rows.IsValidIndex(SelectedIndex))
    {
        if (SelectedIndex == Rows.Num()-1) ItemsScroll->ScrollToEnd();
        else ItemsScroll->ScrollWidgetIntoView(Rows[SelectedIndex], false);
    }
    if (!HasUserFocus(GetOwningPlayer()) || IsTypingText()) { AnalogDirection = 0; AnalogHorizontal = 0; }
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
    EquipmentResultText->SetText(FText::FromString(TEXT("Eating…")));
    Controller->RequestConsumeFood(Item);
}
void UEWInventoryWidget::ShowFoodResult(EEWFoodUseResult Result)
{
    FString Message;
    switch (Result)
    {
        case EEWFoodUseResult::Success: Message = TEXT("Berry eaten"); break;
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
    int32 Kind=8;
    if (Item->GatheringTool==EEWGatheringTool::Hatchet) Kind=5;
    else if (Item->GatheringTool==EEWGatheringTool::Pickaxe) Kind=6;
    else if (Item->FoodKind==EEWFoodKind::Berry) Kind=7;
    else if (Item->Category==EEWItemCategory::Clothing) Kind=9;
    if (!FallbackIcons.Contains(Kind)) FallbackIcons.Add(Kind,EWHudIcon::Make(Kind,false));
    return FallbackIcons[Kind];
}

FLinearColor UEWInventoryWidget::ProbePortraitPixel(FVector2D Uv) const
{
    if (!PortraitTarget) return FLinearColor::Black;
    const int32 X = FMath::Clamp(int32(Uv.X * PortraitTarget->SizeX), 0, PortraitTarget->SizeX - 1), Y = FMath::Clamp(int32(Uv.Y * PortraitTarget->SizeY), 0, PortraitTarget->SizeY - 1);
    return UKismetRenderingLibrary::ReadRenderTargetPixel(const_cast<UEWInventoryWidget*>(this), PortraitTarget, X, Y);
}
