#include "EWHotbarWidget.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Border.h"
#include "Components/VerticalBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/ProgressBar.h"
#include "EWInventoryComponent.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Styling/CoreStyle.h"
#include "EWHudIcon.h"
#include "EWControllerIcons.h"
#include "Components/RichTextBlock.h"
#include "World/EWBuildComponent.h"

void UEWHotbarSlotButton::InitializeSlot(int32 NewSlotIndex)
{
    SlotIndex = NewSlotIndex;
    OnClicked.AddUniqueDynamic(this, &UEWHotbarSlotButton::EmitSlot);
}
void UEWHotbarSlotButton::EmitSlot() { OnSlotPressed.Broadcast(SlotIndex); }

TSharedRef<SWidget> UEWHotbarWidget::RebuildWidget()
{
    BuildWidgetTree();
    return Super::RebuildWidget();
}

void UEWHotbarWidget::NativeConstruct()
{
    Super::NativeConstruct();
    SetVisibility(ESlateVisibility::HitTestInvisible);
    LastDisplay.Reset();
}

void UEWHotbarWidget::BuildWidgetTree()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;
    for (int32 Kind=5;Kind<=11;++Kind) FallbackIcons.Add(EWHudIcon::Make(Kind,Kind>=10));
    auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
    WidgetTree->RootWidget = Canvas;
    auto* Slots = WidgetTree->ConstructWidget<UHorizontalBox>();
    SlotPanel=Slots;Slots->SetRenderTransformPivot(FVector2D(.5f,1.f));
    auto* CanvasSlot = Canvas->AddChildToCanvas(Slots);
    CanvasSlot->SetAnchors(FAnchors(.5f,1.f));
    CanvasSlot->SetAlignment(FVector2D(.5f,1.f));
    CanvasSlot->SetOffsets(FMargin(0,-18,608,80));
    Status = WidgetTree->ConstructWidget<UTextBlock>();
    auto Font = Status->GetFont(); Font.Size = 16; Status->SetFont(Font);
    Status->SetAutoWrapText(true);Status->SetJustification(ETextJustify::Center);
    auto* StatusSlot=Canvas->AddChildToCanvas(Status);
    StatusSlot->SetAnchors(FAnchors(.5f,1.f));StatusSlot->SetAlignment(FVector2D(.5f,1.f));
    StatusSlot->SetOffsets(FMargin(0,-112,608,52));
    ModifierHint = WidgetTree->ConstructWidget<UTextBlock>();
    ModifierHint->SetText(FText::FromString(TEXT("LB")));
    ModifierHint->SetJustification(ETextJustify::Center);
    Font.Size = 12; ModifierHint->SetFont(Font);
    ModifierHint->SetColorAndOpacity(FLinearColor(.94f,.96f,1.f));
    ModifierHint->SetShadowOffset(FVector2D(1,1));
    ModifierHint->SetShadowColorAndOpacity(FLinearColor::Black);
    auto* ModifierSlot = Canvas->AddChildToCanvas(ModifierHint);
    ModifierSlot->SetAnchors(FAnchors(.5f,1.f)); ModifierSlot->SetAlignment(FVector2D(.5f,1.f));
    ModifierSlot->SetOffsets(FMargin(36,-120,42,18));
    ModifierIcon = WidgetTree->ConstructWidget<UImage>();
    auto* ModifierIconSlot = Canvas->AddChildToCanvas(ModifierIcon);
    ModifierIconSlot->SetAnchors(FAnchors(.5f,1.f)); ModifierIconSlot->SetAlignment(FVector2D(.5f,1.f));
    ModifierIconSlot->SetOffsets(FMargin(36,-114,64,34));
    ModifierIcon->SetVisibility(ESlateVisibility::Collapsed);
    BuildHint = WidgetTree->ConstructWidget<URichTextBlock>();
    FTextBlockStyle HintStyle = FTextBlockStyle::GetDefault();
    HintStyle.SetFont(FCoreStyle::GetDefaultFontStyle("Regular", 18));    // CLAUDE.md 9.2: secondary labels at least 18
    HintStyle.SetColorAndOpacity(FLinearColor(.93f,.89f,.8f));
    HintStyle.SetShadowOffset(FVector2D(1,1)); HintStyle.SetShadowColorAndOpacity(FLinearColor::Black);
    BuildHint->SetDefaultTextStyle(HintStyle);
    BuildHint->SetDecorators({UEWButtonIconDecorator::StaticClass()});
    auto* HintSlot = Canvas->AddChildToCanvas(BuildHint);
    HintSlot->SetAnchors(FAnchors(.5f,1.f)); HintSlot->SetAlignment(FVector2D(0.f,1.f));
    HintSlot->SetAutoSize(true); HintSlot->SetPosition(FVector2D(318,-24));   // just right of the eight slots
    BuildHint->SetVisibility(ESlateVisibility::Collapsed);
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
    {
        auto* Box=WidgetTree->ConstructWidget<USizeBox>();Box->SetWidthOverride(72);Box->SetHeightOverride(76);
        Slots->AddChildToHorizontalBox(Box)->SetPadding(FMargin(2,0));
        auto* Cell = WidgetTree->ConstructWidget<UBorder>();
        FSlateBrush Frame=*FCoreStyle::Get().GetBrush("WhiteBrush");
        Frame.DrawAs=ESlateBrushDrawType::Border;Frame.Margin=FMargin(.04f);
        Frame.DrawAs=ESlateBrushDrawType::Image;Frame.SetResourceObject(FallbackIcons[5]);
        Cell->SetBrush(Frame);Cell->SetBrushColor(FLinearColor(.84f,.87f,.9f,1.f));
        Cell->SetPadding(FMargin(3));Box->SetContent(Cell);
        auto* CellContent = WidgetTree->ConstructWidget<UCanvasPanel>();Cell->SetContent(CellContent);
        auto* Icon=WidgetTree->ConstructWidget<UImage>();
        auto* IconSlot=CellContent->AddChildToCanvas(Icon);IconSlot->SetOffsets(FMargin(6,8,54,54));
        Icons.Add(Icon);
        auto* Label = WidgetTree->ConstructWidget<UTextBlock>();Font.Size=14;Label->SetFont(Font);
        Label->SetJustification(ETextJustify::Center);
        auto* LabelSlot=CellContent->AddChildToCanvas(Label);LabelSlot->SetOffsets(FMargin(1,51,32,18));
        Labels.Add(Label);
        auto* Key=WidgetTree->ConstructWidget<UTextBlock>();Key->SetFont(Font);
        Key->SetShadowOffset(FVector2D(1,1));Key->SetShadowColorAndOpacity(FLinearColor::Black);
        Key->SetText(FText::AsNumber(i+1));CellContent->AddChildToCanvas(Key)->SetOffsets(FMargin(2,0,18,18));
        KeyHints.Add(Key);
        auto* KeyIcon=WidgetTree->ConstructWidget<UImage>();
        CellContent->AddChildToCanvas(KeyIcon)->SetOffsets(FMargin(-4,-6,32,32));   // at 26 px the D-pad arm vanishes
        KeyIcon->SetVisibility(ESlateVisibility::Collapsed);KeyIcons.Add(KeyIcon);
        auto* Quantity=WidgetTree->ConstructWidget<UTextBlock>();Quantity->SetFont(Font);Quantity->SetShadowOffset(FVector2D(1,1));Quantity->SetShadowColorAndOpacity(FLinearColor::Black);Quantity->SetJustification(ETextJustify::Right);
        CellContent->AddChildToCanvas(Quantity)->SetOffsets(FMargin(30,51,34,18));Quantities.Add(Quantity);
        auto* Selected=WidgetTree->ConstructWidget<UTextBlock>();Selected->SetFont(Font);
        Selected->SetText(FText::FromString(TEXT("▲")));Selected->SetJustification(ETextJustify::Center);
        CellContent->AddChildToCanvas(Selected)->SetOffsets(FMargin(23,-16,20,18));SelectionMarkers.Add(Selected);
        auto* Freshness = WidgetTree->ConstructWidget<UProgressBar>();
        Freshness->SetFillColorAndOpacity(FLinearColor(.25f,.8f,.35f));
        CellContent->AddChildToCanvas(Freshness)->SetOffsets(FMargin(2,65,62,3));
        FreshnessBars.Add(Freshness);Cells.Add(Cell);
    }
}

void UEWHotbarWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    // Keep readable physical sizes in low-resolution or small editor viewports.
    const float Dpi=UWidgetLayoutLibrary::GetViewportScale(this);
    const float ReadableScale=FMath::Max(1.f,.8f/FMath::Max(Dpi,.01f));
    if (SlotPanel) SlotPanel->SetRenderScale(FVector2D(ReadableScale));
    if (Status) { Status->SetRenderTransformPivot(FVector2D(.5f,1.f));Status->SetRenderScale(FVector2D(ReadableScale)); }

    const auto* Pawn = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer());
    const bool bController = Controller && Controller->UsesControllerPrompts();
    UEWHotbarComponent* Hotbar = Pawn ? Pawn->GetHotbarComponent() : nullptr;
    if (PreviousHotbar.Get() != Hotbar)
    {
        PreviousHotbar = Hotbar; MessageRemaining = 0; LastDisplay.Reset();
    }
    if (MessageRemaining > 0.f) MessageRemaining = FMath::Max(0.f,MessageRemaining-DeltaTime);
    if (MessageRemaining == 0.f) Status->SetText(FText::GetEmpty());
    FString Display;
    for (int32 i=0; i<UEWHotbarComponent::SlotCount; ++i)
    {
        UEWItemDefinition* Item = Hotbar ? Hotbar->GetBoundItem(i) : nullptr;
        const float Freshness = Pawn ? Pawn->GetInventoryComponent()->GetFoodFreshness(Item) : -1.f;
        Display += FString::Printf(TEXT("%d:%s:%d:%.4f;"),i,*GetPathNameSafe(Item),Hotbar ? Hotbar->GetOwnedQuantity(Item) : 0,Freshness);
    }
    Display += FString::FromInt(Hotbar ? Hotbar->GetSelectedSlot() : INDEX_NONE);
    // The pad's own buttons (owner, November 1): LB+X on an Xbox pad is L1+Square on a PlayStation pad.
    const EEWGamepadFamily Family = Controller ? Controller->GetPromptFamily() : EEWGamepadFamily::Unknown;
    const auto* Build = Controller ? Controller->GetBuildComponent() : nullptr;
    const bool bShowBuildHint = Pawn && !Pawn->IsDead() && Build && Build->GetMode() == EEWBuildMode::Off && Build->IsOnFoot()
        && !Controller->IsInventoryOpen() && !Controller->IsMapOpen() && !Controller->IsOptionsMenuOpen();
    Display += bController ? TEXT(":PAD") : TEXT(":KEYBOARD");
    Display += FString::Printf(TEXT(":%d:%d"), int32(Family), bShowBuildHint ? 1 : 0);
    if (Display == LastDisplay) return;
    LastDisplay = Display;
    static const FKey GamepadKeys[] = {EKeys::Gamepad_DPad_Left, EKeys::Gamepad_DPad_Up, EKeys::Gamepad_DPad_Right, EKeys::Gamepad_DPad_Down,
        EKeys::Gamepad_FaceButton_Left, EKeys::Gamepad_FaceButton_Top, EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Bottom};
    ShownFamily = 0;
    static const FText GamepadHints[] = {
        FText::FromString(TEXT("←")), FText::FromString(TEXT("↑")),
        FText::FromString(TEXT("→")), FText::FromString(TEXT("↓")),
        FText::FromString(TEXT("X")), FText::FromString(TEXT("Y")),
        FText::FromString(TEXT("B")), FText::FromString(TEXT("A"))};   // with LB (owner, November 1)
    for (int32 i=0; i<Labels.Num(); ++i)
    {
        UTexture2D* KeyTexture = bController ? FEWControllerIcons::IconFor(GamepadKeys[i], Family) : nullptr;
        if (KeyTexture) { KeyIcons[i]->SetBrushFromTexture(KeyTexture); ShownFamily = int32(Family); }
        KeyIcons[i]->SetVisibility(KeyTexture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
        // Without an icon (an unknown pad), the short arrow or letter stays: a word would not fit the corner.
        KeyHints[i]->SetText(bController ? GamepadHints[i] : FText::AsNumber(i+1));
        KeyHints[i]->SetVisibility(KeyTexture ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
        const auto* Item = Hotbar ? Hotbar->GetBoundItem(i) : nullptr;
        const int32 Quantity = Hotbar ? Hotbar->GetOwnedQuantity(Item) : 0;
        const float Freshness = Pawn ? Pawn->GetInventoryComponent()->GetFoodFreshness(Item) : -1.f;
        FreshnessBars[i]->SetVisibility(Freshness >= 0.f ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        FreshnessBars[i]->SetPercent(FMath::Max(0.f, Freshness));
        const bool Selected=Hotbar && Hotbar->GetSelectedSlot()==i;
        UTexture2D* Texture=Item ? Item->Icon.LoadSynchronous() : nullptr;
        const bool AuthoredIcon=Texture!=nullptr;
        if (Item && !Texture)
        {
            int32 Kind=8;
            if (Item->GatheringTool==EEWGatheringTool::Hatchet) Kind=5;
            else if (Item->GatheringTool==EEWGatheringTool::Pickaxe) Kind=6;
            else if (Item->FoodKind==EEWFoodKind::Berry) Kind=7;
            else if (Item->Category==EEWItemCategory::Clothing) Kind=9;
            Texture=FallbackIcons[Kind-5];
        }
        Icons[i]->SetBrushFromTexture(Texture);
        Icons[i]->SetVisibility(Texture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
        Icons[i]->SetOpacity(Quantity>0 ? 1.f : .35f);
        // Identify placeholder silhouettes until per-item artwork is authored.
        Labels[i]->SetText(Item && !AuthoredIcon ? FText::FromString(Item->DisplayName.ToString().Left(3)) : FText::GetEmpty());
        Labels[i]->SetColorAndOpacity(FSlateColor(Quantity>0 ? FLinearColor::White : FLinearColor(.5f,.5f,.5f)));
        Quantities[i]->SetText(Item ? FText::AsNumber(Quantity) : FText::GetEmpty());
        SelectionMarkers[i]->SetVisibility(Selected ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
        Cells[i]->SetBrushFromTexture(FallbackIcons[Selected ? 6 : 5]);
        Cells[i]->SetBrushColor(Selected ? FLinearColor(.97f,.98f,1.f,1.f) : FLinearColor(.84f,.87f,.9f,1.f));
        Cells[i]->SetToolTipText(Item ? Item->DisplayName : FText::FromString(TEXT("Empty slot")));

    }
    UTexture2D* ModifierTexture = bController ? FEWControllerIcons::IconFor(EKeys::Gamepad_LeftShoulder, Family) : nullptr;
    if (ModifierTexture) ModifierIcon->SetBrushFromTexture(ModifierTexture);
    ModifierIcon->SetVisibility(ModifierTexture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (ModifierHint) ModifierHint->SetVisibility(bController && !ModifierTexture ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    const FString Hint = bShowBuildHint ? BuildHintText(bController) : FString();
    BuildHintPlain = FText::FromString(FEWControllerIcons::Expand(Hint, Family, false));
    BuildHint->SetText(FText::FromString(FEWControllerIcons::Expand(Hint, Family, true)));
    BuildHint->SetVisibility(bShowBuildHint ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
}

FString UEWHotbarWidget::BuildHintText(bool bController)
{
    // Owner, November 1 (CLAUDE.md 6.5): B on the keyboard; hold LB (L1) and press D-pad Right on a controller.
    return bController ? FString::Printf(TEXT("Build: hold %s + %s"), *FEWControllerIcons::Token(EKeys::Gamepad_LeftShoulder),
        *FEWControllerIcons::Token(EKeys::Gamepad_DPad_Right)) : FString(TEXT("Build: B"));
}

FText UEWHotbarWidget::ResultText(EEWHotbarResult Result)
{
    switch (Result)
    {
        case EEWHotbarResult::Success: return FText::FromString(TEXT("Hotbar updated"));
        case EEWHotbarResult::EmptySlot: return FText::FromString(TEXT("That hotbar slot is empty"));
        case EEWHotbarResult::NotOwned: return FText::FromString(TEXT("That item is currently unavailable"));
        case EEWHotbarResult::UnsupportedAction: return FText::FromString(TEXT("That item's action is not available yet"));
        case EEWHotbarResult::InventoryFull: return FText::FromString(TEXT("Inventory is full — make space to return the equipped item"));
        case EEWHotbarResult::NoBenefit: return FText::FromString(TEXT("Hunger and health are already full"));
        case EEWHotbarResult::UnavailableSurvivor: return FText::FromString(TEXT("You cannot eat while dead"));
        case EEWHotbarResult::InvalidFood: return FText::FromString(TEXT("That food cannot be eaten"));
        default: return FText::FromString(TEXT("Hotbar change could not be completed"));
    }
}
void UEWHotbarWidget::ShowResult(EEWHotbarResult Result)
{
    if (Status) Status->SetText(ResultText(Result));
    MessageRemaining = 3.f;
}
