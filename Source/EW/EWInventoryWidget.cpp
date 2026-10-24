// Copyright Elite Game Labs. All Rights Reserved.

#include "EWInventoryWidget.h"
#include "EWCompanyWidget.h"
#include "EWJournalWidget.h"
#include "EWSkillTreeWidget.h"
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

	RefreshInventory();
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
    const bool bShown = SurvivorPanel && SurvivorPanel->GetVisibility() == ESlateVisibility::Visible && PortraitImage;
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
        FSlateBrush Brush; Brush.SetResourceObject(PortraitTarget); Brush.ImageSize = FVector2D(170, 270); Brush.DrawAs = ESlateBrushDrawType::Image;
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
    AnalogDirection = 0;
	Super::NativeDestruct();
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

	UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryTitle"));
	Title->SetText(FText::FromString(TEXT("SURVIVOR")));
	Title->SetColorAndOpacity(FSlateColor(FLinearColor(.85f,.87f,.9f)));
	FSlateFontInfo TitleFont = Title->GetFont();
	TitleFont.Size = 22;
	Title->SetFont(TitleFont);
	Content->AddChildToVerticalBox(Title)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 12.0f));

	SummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventorySummary"));
	SummaryText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
	Content->AddChildToVerticalBox(SummaryText)->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 18.0f));
    auto* Tabs = WidgetTree->ConstructWidget<UHorizontalBox>();
    Content->AddChildToVerticalBox(Tabs);
    const TCHAR* Sections[]={TEXT("INVENTORY"),TEXT("CRAFTING"),TEXT("BUILDING"),TEXT("SKILLS"),TEXT("COMPANY"),TEXT("TAMES"),TEXT("JOURNAL")};
    for (int32 Index=0; Index<7; ++Index)
    {
        auto* Button=WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
        Button->OnRecipePressed.AddDynamic(this,&UEWInventoryWidget::SelectSection);
        auto* Label=WidgetTree->ConstructWidget<UTextBlock>(); Label->SetText(FText::FromString(Sections[Index]));
        auto Font=Label->GetFont(); Font.Size=14; Label->SetFont(Font);
        Label->SetJustification(ETextJustify::Center); Button->SetContent(Label);
        auto* NavSlot=Tabs->AddChildToHorizontalBox(Button); NavSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        NavSlot->SetPadding(FMargin(0,0,4,0)); SectionButtons.Add(Button);
    }
    InventoryTab=SectionButtons[0]; CraftingTab=SectionButtons[1];
    auto* Body = WidgetTree->ConstructWidget<UHorizontalBox>();
    Content->AddChildToVerticalBox(Body)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    CompanyPanel=CreateWidget<UEWCompanyWidget>(GetOwningPlayer());
    Body->AddChildToHorizontalBox(CompanyPanel)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    CompanyPanel->SetVisibility(ESlateVisibility::Collapsed);
    JournalPanel=CreateWidget<UEWJournalWidget>(GetOwningPlayer());
    Body->AddChildToHorizontalBox(JournalPanel)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    JournalPanel->SetVisibility(ESlateVisibility::Collapsed);
    SkillsPanel=CreateWidget<UEWSkillTreeWidget>(GetOwningPlayer());
    Body->AddChildToHorizontalBox(SkillsPanel)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    SkillsPanel->SetVisibility(ESlateVisibility::Collapsed);
    auto* Browser = WidgetTree->ConstructWidget<UVerticalBox>(); BrowserPanel=Browser;
    auto* BrowserSlot = Body->AddChildToHorizontalBox(Browser);
    auto BrowserSize=FSlateChildSize(ESlateSizeRule::Fill); BrowserSize.Value=1.f;
    BrowserSlot->SetSize(BrowserSize); BrowserSlot->SetPadding(FMargin(0,12,16,0));
    auto* SurvivorBorder=WidgetTree->ConstructWidget<UBorder>();
    SurvivorPanel=SurvivorBorder;
    SurvivorBorder->SetPadding(FMargin(16)); SurvivorBorder->SetBrushColor(FLinearColor(.025f,.035f,.045f,.8f));
    auto* SurvivorSlot=Body->AddChildToHorizontalBox(SurvivorBorder);
    auto SurvivorSize=FSlateChildSize(ESlateSizeRule::Fill); SurvivorSize.Value=1.3f;
    SurvivorSlot->SetSize(SurvivorSize); SurvivorSlot->SetPadding(FMargin(0,12,16,0));
    auto* SurvivorScroll=WidgetTree->ConstructWidget<UScrollBox>(); SurvivorBorder->SetContent(SurvivorScroll);
    auto* SurvivorBody=WidgetTree->ConstructWidget<UVerticalBox>(); SurvivorScroll->AddChild(SurvivorBody);
    auto* SurvivorTitle=WidgetTree->ConstructWidget<UTextBlock>(); SurvivorTitle->SetText(FText::FromString(TEXT("SURVIVOR")));
    SurvivorBody->AddChildToVerticalBox(SurvivorTitle)->SetPadding(FMargin(0,0,0,18));
    // The survivor on the left, their numbers beside them on the right.
    auto* SurvivorColumns=WidgetTree->ConstructWidget<UHorizontalBox>(); SurvivorBody->AddChildToVerticalBox(SurvivorColumns);
    PortraitImage=WidgetTree->ConstructWidget<UImage>(); PortraitImage->SetColorAndOpacity(FLinearColor(1.f,1.f,1.f,0.f));
    auto* PortraitSize=WidgetTree->ConstructWidget<USizeBox>(); PortraitSize->SetWidthOverride(170); PortraitSize->SetHeightOverride(270); PortraitSize->SetContent(PortraitImage);
    auto* PortraitSlot=SurvivorColumns->AddChildToHorizontalBox(PortraitSize); PortraitSlot->SetVerticalAlignment(VAlign_Top); PortraitSlot->SetPadding(FMargin(0,0,14,0));
    auto* StatsColumn=WidgetTree->ConstructWidget<UVerticalBox>(); SurvivorColumns->AddChildToHorizontalBox(StatsColumn)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    Content->RemoveChild(SummaryText); StatsColumn->AddChildToVerticalBox(SummaryText);
    SummaryText->SetAutoWrapText(true); auto SummaryFont=SummaryText->GetFont(); SummaryFont.Size=16; SummaryText->SetFont(SummaryFont);
    BuildStatRows(StatsColumn);
    SectionMessage=WidgetTree->ConstructWidget<UTextBlock>(); SectionMessage->SetAutoWrapText(true); SectionMessage->SetFont(SummaryFont);
    SurvivorBody->AddChildToVerticalBox(SectionMessage)->SetPadding(FMargin(0,20,0,0));
    auto* DetailBorder = WidgetTree->ConstructWidget<UBorder>();
    DetailsPanel=DetailBorder; DetailBorder->SetPadding(FMargin(16)); DetailBorder->SetBrushColor(FLinearColor(.035f,.045f,.055f,.95f));
    auto* DetailSlot = Body->AddChildToHorizontalBox(DetailBorder);
    DetailSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); DetailSlot->SetPadding(FMargin(0,12,0,0));
    auto* DetailScroll=WidgetTree->ConstructWidget<UScrollBox>(); DetailBorder->SetContent(DetailScroll);
    auto* DetailPanel = WidgetTree->ConstructWidget<UVerticalBox>(); DetailScroll->AddChild(DetailPanel);
    ItemPreview=WidgetTree->ConstructWidget<UImage>();
    auto* PreviewSize=WidgetTree->ConstructWidget<USizeBox>();
    PreviewSize->SetWidthOverride(112); PreviewSize->SetHeightOverride(112); PreviewSize->SetContent(ItemPreview);
    DetailPanel->AddChildToVerticalBox(PreviewSize)->SetHorizontalAlignment(HAlign_Center);
    ItemPreview->GetParent()->SetVisibility(ESlateVisibility::Collapsed);
    RecipeDetailsBox = WidgetTree->ConstructWidget<UVerticalBox>();
    DetailPanel->AddChildToVerticalBox(RecipeDetailsBox);
    RecipeDetailsBox->SetVisibility(ESlateVisibility::Collapsed);
    auto* InventoryHeading=WidgetTree->ConstructWidget<UTextBlock>(); InventoryHeading->SetText(FText::FromString(TEXT("INVENTORY")));
    Browser->AddChildToVerticalBox(InventoryHeading)->SetPadding(FMargin(0,0,0,8));
    ItemsBox=WidgetTree->ConstructWidget<UWrapBox>(); ItemsBox->SetInnerSlotPadding(FVector2D(6,6));
    auto* Grids=WidgetTree->ConstructWidget<UVerticalBox>(); Grids->AddChildToVerticalBox(ItemsBox);
    EquippedHeading=WidgetTree->ConstructWidget<UTextBlock>(); EquippedHeading->SetText(FText::FromString(TEXT("EQUIPPED")));
    Grids->AddChildToVerticalBox(EquippedHeading)->SetPadding(FMargin(0,12,0,6));
    EquippedBox=WidgetTree->ConstructWidget<UWrapBox>(); EquippedBox->SetInnerSlotPadding(FVector2D(6,6));
    Grids->AddChildToVerticalBox(EquippedBox);
    ItemsScroll=WidgetTree->ConstructWidget<UScrollBox>(); ItemsScroll->AddChild(Grids);
    Browser->AddChildToVerticalBox(ItemsScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    auto* CraftHeading=WidgetTree->ConstructWidget<UTextBlock>(); CraftHeading->SetText(FText::FromString(TEXT("CRAFTING")));
    Browser->AddChildToVerticalBox(CraftHeading)->SetPadding(FMargin(0,16,0,8));
    CraftingBox=WidgetTree->ConstructWidget<UVerticalBox>();
    CraftScroll=WidgetTree->ConstructWidget<UScrollBox>(); CraftScroll->AddChild(CraftingBox);
    Browser->AddChildToVerticalBox(CraftScroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    DetailsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("InventoryDetails"));
    DetailsText->SetAutoWrapText(true);
    auto DetailsFont=DetailsText->GetFont(); DetailsFont.Size=16; DetailsText->SetFont(DetailsFont);
    DetailPanel->AddChildToVerticalBox(DetailsText)->SetPadding(FMargin(0,12));
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
    DetailPanel->AddChildToVerticalBox(HotbarAssignments)->SetPadding(FMargin(0,8));
    auto* Label = WidgetTree->ConstructWidget<UTextBlock>();
    Label->SetText(FText::FromString(TEXT("Hotbar assignment")));
    HotbarAssignments->AddChildToVerticalBox(Label);
    auto* Buttons = WidgetTree->ConstructWidget<UHorizontalBox>();
    HotbarAssignments->AddChildToVerticalBox(Buttons);
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
    {
        auto* Button = WidgetTree->ConstructWidget<UEWHotbarSlotButton>();
        Button->InitializeSlot(i);
        Button->OnSlotPressed.AddDynamic(this,&UEWInventoryWidget::AssignHotbarSlot);
        auto* Text = WidgetTree->ConstructWidget<UTextBlock>();
        Button->SetContent(Text);
        auto* ButtonSlot = Buttons->AddChildToHorizontalBox(Button);
        ButtonSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); ButtonSlot->SetPadding(FMargin(2));
        HotbarButtons.Add(Button); HotbarButtonLabels.Add(Text);
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
        ItemsBox->ClearChildren(); EquippedBox->ClearChildren(); Rows.Reset(); RowFreshness.Reset(); DisplayedEntries.Reset(); DisplayedEquipment.Reset();
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
    DisplayedEquipment = BoundEquipment ? BoundEquipment->GetEquipmentEntries() : TArray<FEWEquipmentEntry>();
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
    RowFreshness.Reset();
    for (const FEWInventoryEntry& Entry : DisplayedEntries)
    {
        float Freshness = -1.f;
        if (Entry.ItemDefinition->FoodKind == EEWFoodKind::Berry && Entry.ItemDefinition->FreshLifetimeSeconds > 0.f)
            Freshness = FMath::Clamp(1.f - Entry.FoodAgeSeconds / Entry.ItemDefinition->FreshLifetimeSeconds, 0.f, 1.f);
        UImage* ItemImage = nullptr; UProgressBar* FreshBar = nullptr;
        // Counts only for things that stack; a lone tool needs none.
        const FString Count = Entry.ItemDefinition->MaxStackSize > 1 ? FString::Printf(TEXT("x%d"), Entry.Quantity) : FString();
        UBorder* Tile = MakeSlotTile(Entry.ItemDefinition, Count, Freshness, ItemImage, FreshBar);
        if (ItemImage) InventoryImages.Add(Entry.ItemDefinition, ItemImage);
        AddToGrid(ItemsBox, Tile);
        Rows.Add(Tile); RowFreshness.Add(FreshBar);
    }
    // The rest of the survivor's slots, empty, so the grid shows how much room is left.
    for (int32 Empty = Inventory->GetMaxSlotCount() - DisplayedEntries.Num(); Empty > 0; --Empty)
    {
        UImage* None = nullptr; UProgressBar* NoBar = nullptr;
        AddToGrid(ItemsBox, MakeSlotTile(nullptr, FString(), -1.f, None, NoBar));
    }
    for (const FEWEquipmentEntry& Entry : DisplayedEquipment)
    {
        UImage* ItemImage = nullptr; UProgressBar* NoBar = nullptr;
        UBorder* Tile = MakeSlotTile(Entry.ItemDefinition, FString::Printf(TEXT("%.1f kg"), Entry.ItemDefinition->UnitWeight), -1.f, ItemImage, NoBar);
        if (ItemImage) InventoryImages.Add(Entry.ItemDefinition, ItemImage);
        AddToGrid(EquippedBox, Tile);
        Rows.Add(Tile); RowFreshness.Add(nullptr);
    }
    EquippedHeading->SetVisibility(DisplayedEquipment.Num() ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (SelectionCount() == 0) bShowingDetails = false;
    UpdateSelection();
    RefreshCrafting();
}

void UEWInventoryWidget::ToggleCrafting()
{
    bCraftingOpen = !bCraftingOpen; SelectedSection=bCraftingOpen ? 1 : 0;
    bShowingDetails = false;
    RefreshCrafting();
    SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::ShowInventoryTab() { SelectSection(0); }
void UEWInventoryWidget::ShowCraftingTab() { SelectSection(1); }
void UEWInventoryWidget::SelectSection(int32 Index)
{
    if (!SectionButtons.IsValidIndex(Index)) return;
    SelectedSection=Index; bCraftingOpen=Index==1; bShowingDetails=false; StatFocus=INDEX_NONE;
    RefreshCrafting(); SetUserFocus(GetOwningPlayer());
}
void UEWInventoryWidget::SelectRecipe(int32 Index)
{
    SelectedRecipeIndex = Index; SelectedSection=1; bCraftingOpen=true; bShowingDetails=false;
    RefreshCrafting();
}
void UEWInventoryWidget::RefreshCrafting()
{
    if (!CraftingBox || !ItemsScroll) return;
    for (int32 Index=0; Index<SectionButtons.Num(); ++Index)
        SectionButtons[Index]->SetBackgroundColor(Index==SelectedSection ? FLinearColor(.5f,.52f,.55f) : FLinearColor(.055f,.065f,.075f));
    const bool BrowserVisible=SelectedSection<2;
    CompanyPanel->SetVisibility(SelectedSection==4 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    JournalPanel->SetVisibility(SelectedSection==6 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    SkillsPanel->SetVisibility(SelectedSection==3 ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    SurvivorPanel->SetVisibility(SelectedSection==4 || SelectedSection==6 ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    BrowserPanel->SetVisibility(BrowserVisible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    DetailsPanel->SetVisibility(BrowserVisible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    const TCHAR* Messages[]={TEXT(""),TEXT(""),TEXT("BUILDING\nUse the Builder's Plan to place unlocked structures."),TEXT(""),TEXT("COMPANY\nCompany membership and shared permissions will appear here."),TEXT("TAMES\nYour claimed animals will appear here."),TEXT("")};
    SectionMessage->SetText(FText::FromString(Messages[SelectedSection]));
    SectionMessage->SetVisibility(BrowserVisible || SelectedSection==4 || SelectedSection==3 ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    ItemPreview->GetParent()->SetVisibility(ESlateVisibility::Collapsed);
    RecipeDetailsBox->SetVisibility(bCraftingOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    DetailsText->SetVisibility(bCraftingOpen ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    if (bCraftingOpen || !BrowserVisible)
    {
        EquipmentActionButton->SetVisibility(ESlateVisibility::Collapsed);
        FoodActionButton->SetVisibility(ESlateVisibility::Collapsed);
        HotbarAssignments->SetVisibility(ESlateVisibility::Collapsed);
    }
    else UpdateSelection();
    CraftingBox->ClearChildren(); RecipeDetailsBox->ClearChildren(); CraftButton=nullptr; DisplayedRecipes.Reset(); MaterialImages.Reset();
    if (BoundInventory) for (auto* Recipe : BoundInventory->GetAvailableRecipes())
        if (Recipe && Recipe->Output) DisplayedRecipes.Add(Recipe);
    if (DisplayedRecipes.IsEmpty())
    {
        auto* Empty = WidgetTree->ConstructWidget<UTextBlock>();
        Empty->SetText(FText::FromString(TEXT("Recipes unlock after the innkeeper introduction.")));
        CraftingBox->AddChildToVerticalBox(Empty); return;
    }
    SelectedRecipeIndex = FMath::Clamp(SelectedRecipeIndex, 0, DisplayedRecipes.Num()-1);
    auto* RecipeGrid = WidgetTree->ConstructWidget<UWrapBox>(); RecipeGrid->SetInnerSlotPadding(FVector2D(8,8));
    CraftingBox->AddChildToVerticalBox(RecipeGrid);
    for (int32 Index=0; Index<DisplayedRecipes.Num(); ++Index)
    {
        auto* Recipe = DisplayedRecipes[Index].Get();
        auto* Button = WidgetTree->ConstructWidget<UEWRecipeButton>(); Button->Initialize(Index);
        Button->SetBackgroundColor(Index==SelectedRecipeIndex ? FLinearColor(.4f,.43f,.47f,1.f) : FLinearColor(.07f,.085f,.1f,1.f));
        Button->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::SelectRecipe);
        Button->OnRecipeHovered.AddDynamic(this, &UEWInventoryWidget::HoverRecipe);
        Button->EnableHover();
        auto* Row = WidgetTree->ConstructWidget<UVerticalBox>();
        if (auto* Texture = ResolveIcon(Recipe->Output))
        {
            auto* Icon = WidgetTree->ConstructWidget<UImage>(); Icon->SetBrushFromTexture(Texture);
            auto* Size = WidgetTree->ConstructWidget<USizeBox>(); Size->SetWidthOverride(64); Size->SetHeightOverride(64);
            Size->SetContent(Icon); Row->AddChildToVerticalBox(Size)->SetHorizontalAlignment(HAlign_Center);
        }
        auto* Name = WidgetTree->ConstructWidget<UTextBlock>();
        Name->SetText(FText::FromString((Index==SelectedRecipeIndex ? TEXT("► ") : TEXT("")) + Recipe->Output->DisplayName.ToString()));
        Name->SetAutoWrapText(true); auto Font=Name->GetFont(); Font.Size=15; Name->SetFont(Font);
        Row->AddChildToVerticalBox(Name); Button->SetContent(Row);
        auto* TileSize=WidgetTree->ConstructWidget<USizeBox>(); TileSize->SetWidthOverride(116); TileSize->SetMinDesiredHeight(124); TileSize->SetContent(Button);
        RecipeGrid->AddChildToWrapBox(TileSize);
    }
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
UBorder* UEWInventoryWidget::MakeSlotTile(UEWItemDefinition* Item, const FString& Corner, float Freshness, UImage*& Image, UProgressBar*& FreshBar)
{
    Image = nullptr; FreshBar = nullptr;
    auto* Tile = WidgetTree->ConstructWidget<UBorder>();
    Tile->SetPadding(FMargin(4));
    Tile->SetBrushColor(Item ? FLinearColor(.04f,.055f,.07f,1) : FLinearColor(.025f,.032f,.042f,.55f));
    if (!Item) return Tile;
    auto* Layers = WidgetTree->ConstructWidget<UOverlay>();
    Tile->SetContent(Layers);
    Image = WidgetTree->ConstructWidget<UImage>(); Image->SetBrushFromTexture(ResolveIcon(Item));
    auto* IconSize = WidgetTree->ConstructWidget<USizeBox>(); IconSize->SetWidthOverride(70); IconSize->SetHeightOverride(70);
    IconSize->SetContent(Image);
    auto* IconSlot = Layers->AddChildToOverlay(IconSize);
    IconSlot->SetHorizontalAlignment(HAlign_Center); IconSlot->SetVerticalAlignment(VAlign_Top); IconSlot->SetPadding(FMargin(0,2,0,0));
    auto* Count = WidgetTree->ConstructWidget<UTextBlock>(); Count->SetText(FText::FromString(Corner));
    auto CountFont = Count->GetFont(); CountFont.Size = 13; Count->SetFont(CountFont);
    Count->SetShadowOffset(FVector2D(1,1)); Count->SetShadowColorAndOpacity(FLinearColor(0,0,0,.9f));
    auto* CountSlot = Layers->AddChildToOverlay(Count);
    CountSlot->SetHorizontalAlignment(HAlign_Right); CountSlot->SetVerticalAlignment(VAlign_Top);
    auto* Name = WidgetTree->ConstructWidget<UTextBlock>();
    Name->SetText(Item->DisplayName.IsEmpty() ? FText::FromName(Item->ItemId) : Item->DisplayName);
    auto NameFont = Name->GetFont(); NameFont.Size = 10; Name->SetFont(NameFont);
    // Left-aligned: a centred name too long for the tile would lose both ends instead of trailing off.
    Name->SetJustification(ETextJustify::Left); Name->SetClipping(EWidgetClipping::ClipToBounds);
    Name->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
    auto* NameSlot = Layers->AddChildToOverlay(Name);
    NameSlot->SetHorizontalAlignment(HAlign_Fill); NameSlot->SetVerticalAlignment(VAlign_Bottom);
    NameSlot->SetPadding(FMargin(0,0,0,Freshness >= 0.f ? 6 : 0));
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

void UEWInventoryWidget::AddToGrid(UWrapBox* Grid, UBorder* Tile)
{
    auto* Size = WidgetTree->ConstructWidget<USizeBox>();
    Size->SetWidthOverride(104); Size->SetHeightOverride(104); Size->SetContent(Tile);
    Grid->AddChildToWrapBox(Size);
}

void UEWInventoryWidget::BuildStatRows(UVerticalBox* Into)
{
    static const TCHAR* Art[] = {
        TEXT("/Game/Elitewake/UI/HUD/T_Health_Matte_v2.T_Health_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Stamina_Matte_v2.T_Stamina_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Hunger_Matte_v2.T_Hunger_Matte_v2"),
        TEXT("/Game/Elitewake/UI/HUD/T_Hydration_Matte_v2.T_Hydration_Matte_v2")};
    static const FLinearColor Fill[] = {FLinearColor(.72f,.12f,.1f), FLinearColor(.86f,.68f,.12f), FLinearColor(.78f,.42f,.14f), FLinearColor(.18f,.46f,.8f)};
    for (int32 i = 0; i < UE_ARRAY_COUNT(Art); ++i)
    {
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        if (UTexture2D* Icon = LoadObject<UTexture2D>(nullptr, Art[i]))
        {
            auto* Image = WidgetTree->ConstructWidget<UImage>(); Image->SetBrushFromTexture(Icon);
            auto* IconSize = WidgetTree->ConstructWidget<USizeBox>(); IconSize->SetWidthOverride(44); IconSize->SetHeightOverride(44);
            IconSize->SetContent(Image);
            auto* IconSlot = Row->AddChildToHorizontalBox(IconSize); IconSlot->SetVerticalAlignment(VAlign_Center); IconSlot->SetPadding(FMargin(0,0,12,0));
        }
        auto* Column = WidgetTree->ConstructWidget<UVerticalBox>();
        auto* Value = WidgetTree->ConstructWidget<UTextBlock>();
        auto Font = Value->GetFont(); Font.Size = 15; Value->SetFont(Font);
        Column->AddChildToVerticalBox(Value)->SetPadding(FMargin(0,0,0,4));
        auto* Bar = WidgetTree->ConstructWidget<UProgressBar>(); Bar->SetFillColorAndOpacity(Fill[i]);
        auto* BarSize = WidgetTree->ConstructWidget<USizeBox>(); BarSize->SetHeightOverride(8); BarSize->SetContent(Bar);
        Column->AddChildToVerticalBox(BarSize);
        auto* ColumnSlot = Row->AddChildToHorizontalBox(Column);
        ColumnSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); ColumnSlot->SetVerticalAlignment(VAlign_Center);
        Into->AddChildToVerticalBox(Row)->SetPadding(FMargin(0,16,0,0));
        StatValues.Add(Value); StatBars.Add(Bar);
    }
    // Climate (owner: humidity belongs in the Character interface): region, air, body, and humidity as a bar.
    auto* Column = WidgetTree->ConstructWidget<UVerticalBox>();
    ClimateValue = WidgetTree->ConstructWidget<UTextBlock>();
    auto Font = ClimateValue->GetFont(); Font.Size = 15; ClimateValue->SetFont(Font); ClimateValue->SetAutoWrapText(true);
    Column->AddChildToVerticalBox(ClimateValue)->SetPadding(FMargin(0,0,0,4));
    HumidityBar = WidgetTree->ConstructWidget<UProgressBar>(); HumidityBar->SetFillColorAndOpacity(FLinearColor(.35f,.7f,.75f));
    auto* BarSize = WidgetTree->ConstructWidget<USizeBox>(); BarSize->SetHeightOverride(8); BarSize->SetContent(HumidityBar);
    Column->AddChildToVerticalBox(BarSize);
    Into->AddChildToVerticalBox(Column)->SetPadding(FMargin(0,20,0,0));

    // Level and stat points (owner, October 22): shown beside the survivor even before a point is earned; each stat's arrow is faint and dead until a point can be spent.
    auto* Level = WidgetTree->ConstructWidget<UVerticalBox>();
    LevelValue = WidgetTree->ConstructWidget<UTextBlock>(); { auto F = LevelValue->GetFont(); F.Size = 20; LevelValue->SetFont(F); }
    Level->AddChildToVerticalBox(LevelValue)->SetPadding(FMargin(0,0,0,4));
    LevelBar = WidgetTree->ConstructWidget<UProgressBar>(); LevelBar->SetFillColorAndOpacity(FLinearColor(.45f,.78f,.95f));
    auto* LevelBarSize = WidgetTree->ConstructWidget<USizeBox>(); LevelBarSize->SetHeightOverride(8); LevelBarSize->SetContent(LevelBar);
    Level->AddChildToVerticalBox(LevelBarSize)->SetPadding(FMargin(0,0,0,6));
    PointsValue = WidgetTree->ConstructWidget<UTextBlock>(); PointsValue->SetAutoWrapText(true); { auto F = PointsValue->GetFont(); F.Size = 15; PointsValue->SetFont(F); }
    Level->AddChildToVerticalBox(PointsValue)->SetPadding(FMargin(0,0,0,8));
    for (int32 Stat = 0; Stat < UEWProgressionComponent::StatCount; ++Stat)
    {
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetAutoWrapText(true); { auto F = Label->GetFont(); F.Size = 15; Label->SetFont(F); }
        Row->AddChildToHorizontalBox(Label)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        auto* Arrow = WidgetTree->ConstructWidget<UEWRecipeButton>(); Arrow->Initialize(Stat);
        Arrow->OnRecipePressed.AddDynamic(this, &UEWInventoryWidget::SpendStat);
        auto* Glyph = WidgetTree->ConstructWidget<UTextBlock>(); Glyph->SetText(FText::FromString(TEXT("\u25B2"))); Glyph->SetJustification(ETextJustify::Center);
        { auto F = Glyph->GetFont(); F.Size = 18; Glyph->SetFont(F); }
        Arrow->SetContent(Glyph);
        auto* ArrowSize = WidgetTree->ConstructWidget<USizeBox>(); ArrowSize->SetWidthOverride(44); ArrowSize->SetHeightOverride(40); ArrowSize->SetContent(Arrow);
        auto* ArrowSlot = Row->AddChildToHorizontalBox(ArrowSize); ArrowSlot->SetVerticalAlignment(VAlign_Center); ArrowSlot->SetPadding(FMargin(8,0,0,0));
        Level->AddChildToVerticalBox(Row)->SetPadding(FMargin(0,0,0,6));
        AllocValues.Add(Label); AllocArrows.Add(Arrow);
    }
    auto* Hint = WidgetTree->ConstructWidget<UTextBlock>(); Hint->SetAutoWrapText(true); Hint->SetColorAndOpacity(FSlateColor(FLinearColor(.65f,.7f,.75f)));
    Hint->SetText(NSLOCTEXT("Elitewake", "StatHint", "C or left stick click: pick a stat with Up/Down or the d-pad, Enter or A raises it. One point per level."));
    { auto F = Hint->GetFont(); F.Size = 12; Hint->SetFont(F); }
    Level->AddChildToVerticalBox(Hint);
    Into->AddChildToVerticalBox(Level)->SetPadding(FMargin(0,24,0,0));
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
    StatFocus = StatIndex >= 0 && StatIndex < UEWProgressionComponent::StatCount && SelectedSection != 4 && SelectedSection != 6 ? StatIndex : INDEX_NONE;
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
    for (int32 Stat = 0; Stat < UEWProgressionComponent::StatCount; ++Stat)
    {
        const EEWStat Which = static_cast<EEWStat>(Stat);
        AllocValues[Stat]->SetText(FText::Format(NSLOCTEXT("Elitewake", "StatRow", "{0}{1}  {2}\n{3}"), FText::FromString(Stat == StatFocus ? TEXT("\u25BA ") : TEXT("")),
            UEWProgressionComponent::StatName(Which), Progress->GetStatPoints(Which), Progress->StatEffect(Which)));
        const bool bLive = Points > 0;
        AllocArrows[Stat]->SetIsEnabled(bLive);
        AllocArrows[Stat]->SetRenderOpacity(bLive ? 1.f : .25f);
        AllocArrows[Stat]->SetBackgroundColor(bLive ? FLinearColor(.2f,.6f,.35f) : FLinearColor(.1f,.12f,.14f));
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
    if (bCraftingOpen && Index != SelectedRecipeIndex && CraftSecondsLeft <= 0.f) SelectRecipe(Index);
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

	SummaryText->SetText(FText::FromString(FString::Printf(TEXT("Slots %d / %d     Weight %.1f / %.1f kg"),
		Inventory->GetUsedSlotCount(), Inventory->GetMaxSlotCount(), Inventory->GetTotalWeight() + (BoundEquipment ? BoundEquipment->GetTotalWeight() : 0.f), MaxWeight)));
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Survival = Character ? Character->GetSurvivalComponent() : nullptr;
    if (Survival && StatValues.Num() == 4)
    {
        const float Max[] = {Survival->GetMaxHealth(), Survival->GetMaxStamina(), 100.f, 100.f};
        const float Now[] = {Survival->GetHealth(), Survival->GetStamina(), Survival->GetHunger(), Survival->GetHydration()};
        const TCHAR* Names[] = {TEXT("Health"), TEXT("Stamina"), TEXT("Hunger"), TEXT("Hydration")};
        for (int32 i = 0; i < 4; ++i)
        {
            StatValues[i]->SetText(FText::FromString(i < 2 ? FString::Printf(TEXT("%s  %.0f / %.0f"), Names[i], Now[i], Max[i])
                                                           : FString::Printf(TEXT("%s  %.0f%%"), Names[i], Now[i])));
            StatBars[i]->SetPercent(Max[i] > 0.f ? FMath::Clamp(Now[i] / Max[i], 0.f, 1.f) : 0.f);
        }
        if (ClimateValue && HumidityBar)
        {
            const FEWClimate C = Survival->GetClimate();
            FString State = Survival->IsFreezing() ? TEXT("  Freezing") : Survival->IsOverheating() ? TEXT("  Overheating")
                : Survival->GetTargetBodyTemperature() < Survival->GetBodyTemperature() - .2f ? TEXT("  Cooling")
                : Survival->GetTargetBodyTemperature() > Survival->GetBodyTemperature() + .2f ? TEXT("  Warming") : TEXT("");
            ClimateValue->SetText(FText::FromString(FString::Printf(TEXT("%s  %.0f\u00B0C   Humidity %.0f%%\nBody %.1f\u00B0C%s"),
                *AEWClimateRegion::RegionName(C.Region).ToString(), Survival->GetFeltTemperature(), C.Humidity, Survival->GetBodyTemperature(), *State)));
            HumidityBar->SetPercent(FMath::Clamp(C.Humidity / 100.f, 0.f, 1.f));
        }
    }
    RefreshProgression();

}

void UEWInventoryWidget::Select(int32 Index)
{
    if (bCraftingOpen)
    {
        SelectRecipe(FMath::Clamp(SelectedRecipeIndex + (Index > SelectedIndex ? 1 : -1), 0, FMath::Max(0, DisplayedRecipes.Num()-1)));
        return;
    }
    if (SelectionCount() == 0) return;
    Index = FMath::Clamp(Index, 0, SelectionCount()-1);
    if (Index != SelectedIndex) { SelectedIndex = Index; bShowingDetails = false; UpdateSelection(); }
}

void UEWInventoryWidget::UpdateSelection()
{
    for (int32 i=0; i<Rows.Num(); ++i)
        Rows[i]->SetBrushColor(i == SelectedIndex ? FLinearColor(.25f,.28f,.32f,1) : FLinearColor(.04f,.055f,.07f,1));
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
    if (Key==EKeys::M || Key==EKeys::Gamepad_Special_Left) { if (!Event.IsRepeat()) if (auto* PC=Cast<AEWPlayerController>(GetOwningPlayer())) PC->SetMapOpen(true); return FReply::Handled(); }
    // Stat points: C or a left-stick press starts choosing; Up/Down or the d-pad pick; Enter or A spends; Escape, B or C again stops.
    if (Key==EKeys::C || Key==EKeys::Gamepad_LeftThumbstick)
    { if (!Event.IsRepeat()) SetStatFocus(StatFocus==INDEX_NONE ? 0 : INDEX_NONE); return FReply::Handled(); }
    const bool bSectionKey = Key==EKeys::Tab || Key==EKeys::PageUp || Key==EKeys::PageDown || Key==EKeys::Gamepad_RightShoulder || Key==EKeys::Gamepad_LeftTrigger;
    if (StatFocus != INDEX_NONE && !bSectionKey)
    {
        if (Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up) SetStatFocus((StatFocus + UEWProgressionComponent::StatCount - 1) % UEWProgressionComponent::StatCount);
        else if (Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down) SetStatFocus((StatFocus + 1) % UEWProgressionComponent::StatCount);
        else if (Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom) { if (!Event.IsRepeat()) SpendStat(StatFocus); }
        else if (Key==EKeys::Escape || Key==EKeys::Gamepad_FaceButton_Right) SetStatFocus(INDEX_NONE);
        return FReply::Handled();      // while choosing a stat, the other keys do nothing
    }
    const bool bNextSection = Key==EKeys::PageDown || Key==EKeys::Gamepad_RightShoulder || (Key==EKeys::Tab && !Event.IsShiftDown());
    const bool bPreviousSection = Key==EKeys::PageUp || Key==EKeys::Gamepad_LeftTrigger || (Key==EKeys::Tab && Event.IsShiftDown());
    if (bNextSection || bPreviousSection)
    { if (!Event.IsRepeat()) CycleSection(bNextSection ? 1 : -1); return FReply::Handled(); }
    if (SelectedSection >= 2)
    {
        // Building, Skills, Company, Tames and Journal have no item list: the arrows page the Journal or move among the stars, and the rest of the keys only close the menu.
        if (SelectedSection==3 && SkillsPanel)
        {
            if (Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up) SkillsPanel->MoveSelection(FVector2D(0, -1));
            else if (Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down) SkillsPanel->MoveSelection(FVector2D(0, 1));
            else if (Key==EKeys::Left || Key==EKeys::Gamepad_DPad_Left) SkillsPanel->MoveSelection(FVector2D(-1, 0));
            else if (Key==EKeys::Right || Key==EKeys::Gamepad_DPad_Right) SkillsPanel->MoveSelection(FVector2D(1, 0));
            else if ((Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat()) SkillsPanel->UnlockSelected();
        }
        if (SelectedSection==6 && JournalPanel && (Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up || Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down))
            JournalPanel->ShowPage(FMath::Clamp(JournalPanel->GetSelectedPage() + ((Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up) ? -1 : 1), 0, FMath::Max(0, JournalPanel->GetPageCount()-1)));
        else if (Key==EKeys::I || Key==EKeys::Gamepad_FaceButton_Right || Key==EKeys::Escape)
        { if (!Event.IsRepeat()) if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->SetInventoryOpen(false); }
        return FReply::Handled();
    }
    if (bCraftingOpen && (Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up || Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down))
    { SelectRecipe(FMath::Clamp(SelectedRecipeIndex + ((Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up) ? -1 : 1),0,FMath::Max(0,DisplayedRecipes.Num()-1))); return FReply::Handled(); }
    if (bCraftingOpen && (Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom))
    { if (!Event.IsRepeat()) PerformCraft(); return FReply::Handled(); }
    auto* OwnerController = Cast<AEWPlayerController>(GetOwningPlayer());
    if (OwnerController) OwnerController->RecordInputDevice(Key);
    if (HotbarPick != INDEX_NONE)
    {
        // Picking a slot: the d-pad or arrows move the cursor, A or Enter assigns (or takes the item off that slot), B, Y or Escape stop.
        const int32 Count = UEWHotbarComponent::SlotCount;
        if (Key==EKeys::Left || Key==EKeys::Gamepad_DPad_Left || Key==EKeys::Up || Key==EKeys::Gamepad_DPad_Up) SetHotbarPick((HotbarPick + Count - 1) % Count);
        else if (Key==EKeys::Right || Key==EKeys::Gamepad_DPad_Right || Key==EKeys::Down || Key==EKeys::Gamepad_DPad_Down) SetHotbarPick((HotbarPick + 1) % Count);
        else if ((Key==EKeys::Enter || Key==EKeys::Gamepad_FaceButton_Bottom) && !Event.IsRepeat()) { AssignHotbarSlot(HotbarPick); SetHotbarPick(INDEX_NONE); }
        else if ((Key==EKeys::Escape || Key==EKeys::Gamepad_FaceButton_Right || Key==EKeys::Gamepad_FaceButton_Top) && !Event.IsRepeat()) SetHotbarPick(INDEX_NONE);
        return FReply::Handled();
    }
    if (Key == EKeys::Gamepad_FaceButton_Top && !(OwnerController && OwnerController->IsHotbarModifierHeld()))
    {
        if (!Event.IsRepeat()) QuickAssignSelectedToHotbar();
        return FReply::Handled();
    }
    if (Key==EKeys::Gamepad_LeftShoulder)
    {
        if (OwnerController) OwnerController->SetHotbarModifierHeld(true);
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
    if (Key == EKeys::Left || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up) { Select(SelectedIndex-1); return FReply::Handled(); }
    if (Key == EKeys::Right || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down) { Select(SelectedIndex+1); return FReply::Handled(); }
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
        if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->SetHotbarModifierHeld(false);
    return FReply::Handled();
}

FReply UEWInventoryWidget::NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event)
{
    if (FMath::Abs(Event.GetAnalogValue()) > .2f)
        if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->RecordInputDevice(Event.GetKey());
    if (Event.GetKey() == EKeys::Gamepad_LeftY)
    {
        const int32 Direction = FMath::Abs(Event.GetAnalogValue()) >= .5f ? (Event.GetAnalogValue() > 0 ? -1 : 1) : 0;
        if (Direction != AnalogDirection) { AnalogDirection = Direction; AnalogRepeatRemaining = .35f; if (Direction) Select(SelectedIndex+Direction); }
    }
    return FReply::Handled();
}

int32 UEWInventoryWidget::RowAt(const FVector2D& Position) const
{
    if (!ItemsScroll->GetCachedGeometry().IsUnderLocation(Position)) return INDEX_NONE;
    for (int32 i=0; i<Rows.Num(); ++i) if (Rows[i]->GetCachedGeometry().IsUnderLocation(Position)) return i;
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
    return Super::NativeOnPreviewMouseButtonDown(Geometry, Event);
}

FReply UEWInventoryWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() == EKeys::LeftMouseButton)
    {
        const int32 Row = RowAt(Event.GetScreenSpacePosition());
        if (Row != INDEX_NONE) { if (bCraftingOpen || SelectedSection!=0) SelectSection(0); Select(Row); ConfirmSelection(); return FReply::Handled().SetUserFocus(TakeWidget()); }
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
        if (!BoundInventory) { ItemsBox->ClearChildren(); Rows.Reset(); DetailsText->SetText(FText::FromString(TEXT("No item selected"))); }
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
    if (!HasUserFocus(GetOwningPlayer())) AnalogDirection = 0;
    if (AnalogDirection)
    {
        AnalogRepeatRemaining -= DeltaTime;
        if (AnalogRepeatRemaining <= 0) { Select(SelectedIndex+AnalogDirection); AnalogRepeatRemaining = .18f; }
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
