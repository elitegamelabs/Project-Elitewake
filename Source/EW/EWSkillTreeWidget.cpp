#include "EWSkillTreeWidget.h"
#include "EWCharacter.h"
#include "EWCraftingRecipe.h"
#include "EWInventoryComponent.h"
#include "EWItemDefinition.h"
#include "EWPlayerController.h"
#include "EWProgressionComponent.h"
#include "EWSkillTree.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/ScaleBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

namespace
{
    constexpr float StarSize = 46.f, SkyWidth = 640.f, SkyHeight = 460.f;
    FVector2D PixelOf(const FEWSkillNode& N) { return FVector2D(N.Position.X * SkyWidth, N.Position.Y * SkyHeight); }
}

TSharedRef<SWidget> UEWSkillTreeWidget::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
        WidgetTree->RootWidget = Row;
        // The night sky with its stars.
        auto* SkyBorder = WidgetTree->ConstructWidget<UBorder>(); SkyBorder->SetBrushColor(FLinearColor(.012f, .02f, .05f, .95f)); SkyBorder->SetPadding(FMargin(8));
        // The sky fills the whole panel under the tabs (owner, October 25): the constellation scales to fit it.
        auto* SkySlot = Row->AddChildToHorizontalBox(SkyBorder); SkySlot->SetPadding(FMargin(0, 0, 12, 0)); { auto S = FSlateChildSize(ESlateSizeRule::Fill); S.Value = 2.4f; SkySlot->SetSize(S); }
        auto* SkyScale = WidgetTree->ConstructWidget<UScaleBox>(); SkyScale->SetStretch(EStretch::ScaleToFit); SkyBorder->SetContent(SkyScale);
        auto* SkySize = WidgetTree->ConstructWidget<USizeBox>(); SkySize->SetWidthOverride(SkyWidth); SkySize->SetHeightOverride(SkyHeight); SkyScale->SetContent(SkySize);
        Sky = WidgetTree->ConstructWidget<UCanvasPanel>(); SkySize->SetContent(Sky);
        const TArray<FEWSkillNode>& Nodes = FEWSkillTree::Nodes();
        // Lines first, so the stars sit on top of them.
        for (int32 Child = 0; Child < Nodes.Num(); ++Child)
            for (const FName& Parent : Nodes[Child].Requires)
            {
                const int32 ParentIndex = Nodes.IndexOfByPredicate([Parent](const FEWSkillNode& N) { return N.Id == Parent; });
                if (ParentIndex == INDEX_NONE) continue;
                const FVector2D A = PixelOf(Nodes[ParentIndex]), B = PixelOf(Nodes[Child]);
                auto* Line = WidgetTree->ConstructWidget<UBorder>(); Line->SetBrushColor(FLinearColor(.35f, .42f, .55f, .5f));
                auto* LineSlot = Sky->AddChildToCanvas(Line);
                LineSlot->SetAutoSize(false); LineSlot->SetAlignment(FVector2D(0.f, .5f)); LineSlot->SetPosition(A);
                LineSlot->SetSize(FVector2D((B - A).Size(), 3.f));
                Line->SetRenderTransformPivot(FVector2D(0.f, .5f));
                Line->SetRenderTransformAngle(FMath::RadiansToDegrees(FMath::Atan2(B.Y - A.Y, B.X - A.X)));
                Line->SetVisibility(ESlateVisibility::HitTestInvisible);
                Lines.Add(Line); LineEnds.Add(TPair<int32, int32>(Child, ParentIndex));
            }
        for (int32 Index = 0; Index < Nodes.Num(); ++Index)
        {
            auto* Star = WidgetTree->ConstructWidget<UEWSkillStarButton>(); Star->Initialize(Index);
            Star->OnStarClicked.AddDynamic(this, &UEWSkillTreeWidget::StarClicked);
            Star->OnStarHovered.AddDynamic(this, &UEWSkillTreeWidget::StarHovered);
            Star->SetBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
            auto* Disc = WidgetTree->ConstructWidget<UBorder>(); Disc->SetHorizontalAlignment(HAlign_Center); Disc->SetVerticalAlignment(VAlign_Center);
            auto* Glyph = WidgetTree->ConstructWidget<UTextBlock>(); Glyph->SetText(FText::FromString(TEXT("✦"))); Glyph->SetJustification(ETextJustify::Center);
            { auto F = Glyph->GetFont(); F.Size = 28; Glyph->SetFont(F); }
            Disc->SetContent(Glyph); Star->SetContent(Disc);
            auto* Box = WidgetTree->ConstructWidget<USizeBox>(); Box->SetWidthOverride(StarSize); Box->SetHeightOverride(StarSize); Box->SetContent(Star);
            auto* Place = Sky->AddChildToCanvas(Box);
            Place->SetAutoSize(true); Place->SetAlignment(FVector2D(.5f, .5f)); Place->SetPosition(PixelOf(Nodes[Index]));
            auto* Name = WidgetTree->ConstructWidget<UTextBlock>(); Name->SetText(Nodes[Index].Title); Name->SetJustification(ETextJustify::Center);
            Name->SetColorAndOpacity(FSlateColor(FLinearColor(.78f, .84f, .92f))); { auto F = Name->GetFont(); F.Size = 12; Name->SetFont(F); }
            Name->SetVisibility(ESlateVisibility::HitTestInvisible);
            auto* NamePlace = Sky->AddChildToCanvas(Name);
            NamePlace->SetAutoSize(true); NamePlace->SetAlignment(FVector2D(.5f, 0.f)); NamePlace->SetPosition(PixelOf(Nodes[Index]) + FVector2D(0.f, StarSize * .5f));
            Stars.Add(Disc); StarGlyphs.Add(Glyph);
        }
        // The panel for the star under the mouse or picked with the arrows.
        auto* DetailBorder = WidgetTree->ConstructWidget<UBorder>(); DetailBorder->SetBrushColor(FLinearColor(.035f, .045f, .055f, .95f)); DetailBorder->SetPadding(FMargin(16));
        auto* DetailSlot = Row->AddChildToHorizontalBox(DetailBorder); DetailSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); DetailSlot->SetPadding(FMargin(0));
        auto* Column = WidgetTree->ConstructWidget<UVerticalBox>(); DetailBorder->SetContent(Column);
        auto Text = [this, Column](int32 Size, const FLinearColor& Colour, float Below)
        {
            auto* Label = WidgetTree->ConstructWidget<UTextBlock>(); Label->SetAutoWrapText(true); Label->SetColorAndOpacity(FSlateColor(Colour));
            auto F = Label->GetFont(); F.Size = Size; Label->SetFont(F);
            Column->AddChildToVerticalBox(Label)->SetPadding(FMargin(0, 0, 0, Below)); return Label;
        };
        PointsLine = Text(15, FLinearColor(.75f, .85f, .95f), 12.f);
        Title = Text(22, FLinearColor(.95f, .88f, .6f), 8.f);
        Body = Text(15, FLinearColor::White, 12.f);
        Materials = Text(15, FLinearColor(.8f, .9f, .8f), 14.f);
        UnlockButton = WidgetTree->ConstructWidget<UButton>(); UnlockButton->SetBackgroundColor(FLinearColor(.2f, .5f, .35f));
        UnlockLabel = WidgetTree->ConstructWidget<UTextBlock>(); { auto F = UnlockLabel->GetFont(); F.Size = 18; UnlockLabel->SetFont(F); }
        UnlockLabel->SetJustification(ETextJustify::Center); UnlockButton->SetContent(UnlockLabel);
        UnlockButton->OnClicked.AddDynamic(this, &UEWSkillTreeWidget::OnUnlockClicked);
        Column->AddChildToVerticalBox(UnlockButton);
        auto* Hint = Text(12, FLinearColor(.6f, .66f, .72f), 0.f);
        Hint->SetText(NSLOCTEXT("Elitewake", "SkillHint", "Mouse: point at a star to read it, click Unlock. Keyboard and controller: arrows or d-pad pick a star, Enter or A lights it."));
        Column->RemoveChild(Hint); Column->AddChildToVerticalBox(Hint)->SetPadding(FMargin(0, 14, 0, 0));
    }
    return Super::RebuildWidget();
}

FName UEWSkillTreeWidget::GetSelectedId() const
{
    const TArray<FEWSkillNode>& Nodes = FEWSkillTree::Nodes();
    return Nodes.IsValidIndex(Selected) ? Nodes[Selected].Id : NAME_None;
}
int32 UEWSkillTreeWidget::GetNodeCount() const { return FEWSkillTree::Nodes().Num(); }
FText UEWSkillTreeWidget::GetDetailTitle() const { return Title ? Title->GetText() : FText::GetEmpty(); }
FText UEWSkillTreeWidget::GetDetailMaterials() const { return Materials ? Materials->GetText() : FText::GetEmpty(); }
bool UEWSkillTreeWidget::IsUnlockEnabled() const { return UnlockButton && UnlockButton->GetIsEnabled(); }

void UEWSkillTreeWidget::SelectNode(int32 Index)
{
    if (!FEWSkillTree::Nodes().IsValidIndex(Index) || Index == Selected) return;
    Selected = Index;
    Refresh();
}

void UEWSkillTreeWidget::MoveSelection(FVector2D Direction)
{
    const TArray<FEWSkillNode>& Nodes = FEWSkillTree::Nodes();
    if (!Nodes.IsValidIndex(Selected) || Direction.IsNearlyZero()) return;
    Direction.Normalize();
    int32 Best = INDEX_NONE; float BestScore = TNumericLimits<float>::Max();
    for (int32 i = 0; i < Nodes.Num(); ++i)
    {
        if (i == Selected) continue;
        const FVector2D To = PixelOf(Nodes[i]) - PixelOf(Nodes[Selected]);
        const float Distance = To.Size();
        if (Distance < 1.f) continue;
        const float Along = FVector2D::DotProduct(To / Distance, Direction);
        if (Along < .35f) continue;                         // roughly that way
        const float Score = Distance * (2.f - Along);        // near and straight on wins
        if (Score < BestScore) { BestScore = Score; Best = i; }
    }
    if (Best != INDEX_NONE) SelectNode(Best);
}

bool UEWSkillTreeWidget::UnlockSelected()
{
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    if (!Progress || !Progress->CanUnlockSkill(GetSelectedId())) return false;
    if (auto* Controller = Cast<AEWPlayerController>(GetOwningPlayer())) Controller->RequestUnlockSkill(GetSelectedId());
    return true;
}

void UEWSkillTreeWidget::NativeTick(const FGeometry& Geometry, float Delta)
{
    Super::NativeTick(Geometry, Delta);
    RefreshClock += Delta;
    if (RefreshClock >= .2f) { RefreshClock = 0.f; Refresh(); }
}

void UEWSkillTreeWidget::Refresh()
{
    const TArray<FEWSkillNode>& Nodes = FEWSkillTree::Nodes();
    const auto* Character = Cast<AEWCharacter>(GetOwningPlayerPawn());
    const auto* Progress = Character ? Character->GetProgressionComponent() : nullptr;
    const auto* Pack = Character ? Character->GetInventoryComponent() : nullptr;
    if (!Progress || Stars.Num() != Nodes.Num() || !Nodes.IsValidIndex(Selected)) return;
    for (int32 i = 0; i < Nodes.Num(); ++i)
    {
        const bool bLit = Progress->IsSkillUnlocked(Nodes[i].Id), bReady = Progress->CanUnlockSkill(Nodes[i].Id);
        const FLinearColor Glow = bLit ? FLinearColor(1.f, .82f, .3f) : bReady ? FLinearColor(.75f, .9f, 1.f) : FLinearColor(.28f, .32f, .4f);
        StarGlyphs[i]->SetColorAndOpacity(FSlateColor(Glow));
        Stars[i]->SetBrushColor(i == Selected ? FLinearColor(1.f, .85f, .35f, .45f) : FLinearColor(0.f, 0.f, 0.f, 0.f));
    }
    for (int32 i = 0; i < Lines.Num(); ++i)
    {
        const bool bBothLit = Progress->IsSkillUnlocked(Nodes[LineEnds[i].Key].Id);
        Lines[i]->SetBrushColor(bBothLit ? FLinearColor(1.f, .82f, .3f, .85f) : FLinearColor(.35f, .42f, .55f, .5f));
    }
    const FEWSkillNode& N = Nodes[Selected];
    PointsLine->SetText(FText::Format(NSLOCTEXT("Elitewake", "SkillPoints", "Skill points: {0}   (one is earned with every level)"), Progress->GetSkillPoints()));
    Title->SetText(N.Title);
    const bool bLit = Progress->IsSkillUnlocked(N.Id);
    FString Needs;
    for (const FName& Parent : N.Requires)
        if (const FEWSkillNode* P = FEWSkillTree::Find(Parent))
            if (!Progress->IsSkillUnlocked(Parent)) Needs += (Needs.IsEmpty() ? TEXT("") : TEXT(", ")) + P->Title.ToString();
    Body->SetText(FText::FromString(N.Description.ToString() + (bLit ? TEXT("\n\nLit.") : Needs.IsEmpty() ? FString::Printf(TEXT("\n\nCost: %d skill point%s."), N.Cost, N.Cost == 1 ? TEXT("") : TEXT("s"))
        : FString::Printf(TEXT("\n\nCost: %d skill point%s. Needs first: %s."), N.Cost, N.Cost == 1 ? TEXT("") : TEXT("s"), *Needs))));
    // Recipes this star adds, with what each one costs and how much of it is in the pack.
    FString Costs;
    for (const TSoftObjectPtr<UEWCraftingRecipe>& Soft : N.Recipes)
        if (const UEWCraftingRecipe* Recipe = Soft.LoadSynchronous())
        {
            Costs += FString::Printf(TEXT("Recipe: %s (%.0f s)\n"), Recipe->Output ? *Recipe->Output->DisplayName.ToString() : TEXT("?"), Recipe->CraftSeconds);
            for (const FEWCraftingIngredient& Part : Recipe->Ingredients) if (Part.Item)
                Costs += FString::Printf(TEXT("   %s x%d  (you have %d)\n"), *Part.Item->DisplayName.ToString(), Part.Quantity, Pack ? Pack->GetItemCount(Part.Item) : 0);
        }
    Materials->SetText(FText::FromString(Costs.IsEmpty() ? FString() : TEXT("MATERIALS\n") + Costs));
    Materials->SetVisibility(Costs.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    const bool bCan = Progress->CanUnlockSkill(N.Id);
    UnlockButton->SetIsEnabled(bCan);
    UnlockButton->SetRenderOpacity(bCan ? 1.f : .35f);
    UnlockLabel->SetText(bLit ? NSLOCTEXT("Elitewake", "SkillLit", "Unlocked") : bCan ? NSLOCTEXT("Elitewake", "SkillUnlock", "Unlock  (Enter / A)") : NSLOCTEXT("Elitewake", "SkillLocked", "Locked"));
}
