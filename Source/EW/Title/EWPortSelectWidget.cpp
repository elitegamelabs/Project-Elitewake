#include "Title/EWPortSelectWidget.h"
#include "Title/EWFreeports.h"
#include "Title/EWFrontEndPaint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Engine/Texture2D.h"


TSharedRef<SWidget> UEWPortSelectWidget::RebuildWidget()
{
    using namespace EWFrontEnd;
    SetIsFocusable(true);
    SetVisibility(ESlateVisibility::Visible);
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        UBorder* Root = WidgetTree->ConstructWidget<UBorder>();
        Root->SetBrushColor(FLinearColor::Transparent);
        Root->SetVisibility(ESlateVisibility::HitTestInvisible);
        WidgetTree->RootWidget = Root;
    }
    return Super::RebuildWidget();
}

void UEWPortSelectWidget::NativeConstruct()
{
    using namespace EWFrontEnd;
    Super::NativeConstruct();
    Focus = 0;          // Resume when it is offered, else Create New
}

void UEWPortSelectWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    using namespace EWFrontEnd;
    Super::NativeTick(Geometry, DeltaTime);
    LastSize = Geometry.GetLocalSize();
    Age += DeltaTime;
}

FName UEWPortSelectWidget::GetSelectedPortId() const { return FName(EWFreeports::List[Port].Id); }

void UEWPortSelectWidget::SelectPort(int32 Index)
{
    using namespace EWFrontEnd;
    if (Index >= 0 && Index < EWFreeports::Count) Port = Index;
}

void UEWPortSelectWidget::Resume()
{
    using namespace EWFrontEnd;
    if (bCanResume && !bAsking) OnResume.ExecuteIfBound();
}

void UEWPortSelectWidget::CreateNew()
{
    using namespace EWFrontEnd;
    if (bAsking) return;
    if (bCanResume) { bAsking = true; AskFocus = 1; return; }
    OnCreateNew.ExecuteIfBound();
}

void UEWPortSelectWidget::AnswerReplace(bool bYes)
{
    using namespace EWFrontEnd;
    if (!bAsking) return;
    bAsking = false;
    if (bYes) OnCreateNew.ExecuteIfBound();
}

void UEWPortSelectWidget::GoBack()
{
    using namespace EWFrontEnd;
    if (bAsking) { bAsking = false; return; }
    OnBack.ExecuteIfBound();
}

void UEWPortSelectWidget::Activate(int32 Button)
{
    using namespace EWFrontEnd;
    if (bCanResume && Button == 0) Resume();
    else CreateNew();
}

FVector2D UEWPortSelectWidget::GetPortMarker(int32 Index) const
{
    using namespace EWFrontEnd;
    const FLayout L = Layout(LastSize);
    return L.Markers.IsValidIndex(Index) ? L.Markers[Index] : FVector2D(-1, -1);
}

UEWPortSelectWidget::FLayout UEWPortSelectWidget::Layout(const FVector2D& Size) const
{
    using namespace EWFrontEnd;
    FLayout L;
    L.Box = FSlateRect(Size.X * .05f, Size.Y * .15f, Size.X * .95f, Size.Y * .79f);
    const float ListWidth = FMath::Clamp(L.Box.GetSize().X * .27f, 300.f, 460.f);
    L.Map = FSlateRect(L.Box.Left + 2, L.Box.Top + 2, L.Box.Right - ListWidth, L.Box.Bottom - 2);
    L.List = FSlateRect(L.Map.Right, L.Box.Top, L.Box.Right, L.Box.Bottom);
    // The whole world, every island, at the map's shape: a little sea round the outermost islands.
    const FVector2D MapSize = L.Map.GetSize();
    L.HalfH = 1760000.f;
    L.HalfW = L.HalfH * MapSize.X / FMath::Max(1.0, MapSize.Y);
    if (L.HalfW < 1760000.f) { L.HalfW = 1760000.f; L.HalfH = L.HalfW * MapSize.Y / FMath::Max(1.0, MapSize.X); }
    if (L.HalfW > ArtHalfX) { L.HalfW = ArtHalfX; L.HalfH = L.HalfW * MapSize.Y / FMath::Max(1.0, MapSize.X); }   // a very wide screen
    const float EntryH = (L.List.GetSize().Y - 24.f) / EWFreeports::Count;
    for (int32 I = 0; I < EWFreeports::Count; ++I)
    {
        L.Entries.Add(FSlateRect(L.List.Left + 14, L.List.Top + 12 + EntryH * I, L.List.Right - 14, L.List.Top + 12 + EntryH * (I + 1) - 6));
        const FVector2D C = EWFreeports::List[I].Centre;
        L.Markers.Add(FVector2D(L.Map.Left + (C.X + L.HalfW) / (2 * L.HalfW) * MapSize.X, L.Map.Top + (L.HalfH - C.Y) / (2 * L.HalfH) * MapSize.Y));
    }
    const float ButtonW = 400.f, ButtonH = 64.f, Gap = 28.f;
    const int32 N = ButtonCount();
    const float Total = N * ButtonW + (N - 1) * Gap;
    const float Top = L.Box.Bottom + (Size.Y - L.Box.Bottom) * .28f;
    for (int32 I = 0; I < N; ++I)
    {
        const float Left = (Size.X - Total) * .5f + I * (ButtonW + Gap);
        L.Buttons.Add(FSlateRect(Left, Top, Left + ButtonW, Top + ButtonH));
    }
    L.Back = FSlateRect(L.Box.Left, Size.Y * .045f, L.Box.Left + 150.f, Size.Y * .045f + 44.f);
    L.AskPanel = FSlateRect(Size.X * .5f - 380.f, Size.Y * .5f - 130.f, Size.X * .5f + 380.f, Size.Y * .5f + 130.f);
    L.AskYes = FSlateRect(L.AskPanel.Left + 60, L.AskPanel.Bottom - 90, L.AskPanel.Left + 360, L.AskPanel.Bottom - 34);
    L.AskNo = FSlateRect(L.AskPanel.Right - 360, L.AskPanel.Bottom - 90, L.AskPanel.Right - 60, L.AskPanel.Bottom - 34);
    return L;
}

FReply UEWPortSelectWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    using namespace EWFrontEnd;
    bGamepad = false;
    const FVector2D At = Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition());
    const FLayout L = Layout(Geometry.GetLocalSize());
    HoverPort = INDEX_NONE;
    if (bAsking)
    {
        if (L.AskYes.ContainsPoint(At)) AskFocus = 0;
        else if (L.AskNo.ContainsPoint(At)) AskFocus = 1;
        return FReply::Handled();
    }
    for (int32 I = 0; I < EWFreeports::Count; ++I)
        if (L.Entries[I].ContainsPoint(At) || FVector2D::Distance(L.Markers[I], At) < 26.f) HoverPort = I;
    for (int32 I = 0; I < L.Buttons.Num(); ++I) if (L.Buttons[I].ContainsPoint(At)) Focus = I;
    return FReply::Handled();
}

FReply UEWPortSelectWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    using namespace EWFrontEnd;
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Handled();
    const FVector2D At = Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition());
    const FLayout L = Layout(Geometry.GetLocalSize());
    if (bAsking)
    {
        if (L.AskYes.ContainsPoint(At)) AnswerReplace(true);
        else if (L.AskNo.ContainsPoint(At)) AnswerReplace(false);
        return FReply::Handled();
    }
    for (int32 I = 0; I < EWFreeports::Count; ++I)
        if (L.Entries[I].ContainsPoint(At) || FVector2D::Distance(L.Markers[I], At) < 26.f) { SelectPort(I); return FReply::Handled(); }
    for (int32 I = 0; I < L.Buttons.Num(); ++I)
        if (L.Buttons[I].ContainsPoint(At)) { Focus = I; Activate(I); return FReply::Handled(); }
    if (L.Back.ContainsPoint(At)) GoBack();
    return FReply::Handled();
}

FReply UEWPortSelectWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    using namespace EWFrontEnd;
    const FKey Key = Event.GetKey();
    bGamepad = Key.IsGamepadKey();
    const bool Up = Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up;
    const bool Down = Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down;
    const bool Left = Key == EKeys::Left || Key == EKeys::A || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_LeftStick_Left;
    const bool Right = Key == EKeys::Right || Key == EKeys::D || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Gamepad_LeftStick_Right;
    const bool Accept = Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom;
    const bool Cancel = Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::BackSpace;
    if (bAsking)
    {
        if (Left || Right) AskFocus = 1 - AskFocus;
        else if (Accept) AnswerReplace(AskFocus == 0);
        else if (Cancel) AnswerReplace(false);
        return FReply::Handled();
    }
    if (Up) SelectPort((Port + EWFreeports::Count - 1) % EWFreeports::Count);
    else if (Down) SelectPort((Port + 1) % EWFreeports::Count);
    else if (Left) Focus = FMath::Max(0, Focus - 1);
    else if (Right) Focus = FMath::Min(ButtonCount() - 1, Focus + 1);
    else if (Accept) Activate(Focus);
    else if (Cancel) GoBack();
    else if (Key == EKeys::One || Key == EKeys::Two || Key == EKeys::Three || Key == EKeys::Four || Key == EKeys::Five)
        SelectPort(Key == EKeys::One ? 0 : Key == EKeys::Two ? 1 : Key == EKeys::Three ? 2 : Key == EKeys::Four ? 3 : 4);
    else return FReply::Unhandled();
    return FReply::Handled();
}

int32 UEWPortSelectWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    using namespace EWFrontEnd;
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    const FPainter P{AllottedGeometry, OutDrawElements, Layer};
    const FVector2D Size = AllottedGeometry.GetLocalSize();
    const FLayout L = Layout(Size);
    using namespace EWFreeports;

    P.Box(1, FSlateRect(FVector2D::ZeroVector, Size), Ground);
    // Heading.
    P.Text(3, TEXT("SINGLE PLAYER"), Font(13, true, 420), FVector2D(Size.X * .5f, Size.Y * .045f), Gold, FVector2D(.5f, 0));
    P.Text(3, TEXT("Choose your Freeport"), Font(34, true), FVector2D(Size.X * .5f, Size.Y * .072f), Cream, FVector2D(.5f, 0));
    const bool bBackHover = false;
    P.Text(3, bGamepad ? TEXT("B  BACK") : TEXT("<  BACK"), Font(14, true, 200), L.Back.GetCenter(), bBackHover ? GoldLight : Muted, FVector2D(.5f, .5f));

    // The box: the world on the left, the Freeports beside it.
    P.Box(2, L.Box, Panel);
    if (MapArt)
    {
        const float U0 = (ArtHalfX - L.HalfW) / (2 * ArtHalfX), U1 = (ArtHalfX + L.HalfW) / (2 * ArtHalfX);
        const float V0 = (ArtHalfY - L.HalfH) / (2 * ArtHalfY), V1 = (ArtHalfY + L.HalfH) / (2 * ArtHalfY);
        P.Image(3, MapArt, L.Map, FLinearColor::White, FBox2f(FVector2f(U0, V0), FVector2f(U1, V1)));
    }
    P.Box(4, FSlateRect(L.Map.Right, L.Box.Top, L.Map.Right + 1, L.Box.Bottom), Line);
    P.Outline(4, L.Box, 1.f, Line);
    P.Corners(5, FSlateRect(L.Box.Left - 6, L.Box.Top - 6, L.Box.Right + 6, L.Box.Bottom + 6), 34.f, 3.f, Gold);
    // North.
    P.Text(5, TEXT("N"), Font(14, true), FVector2D(L.Map.Left + 34, L.Map.Top + 20), GoldLight, FVector2D(.5f, 0));
    P.Box(5, FSlateRect(L.Map.Left + 33, L.Map.Top + 44, L.Map.Left + 35, L.Map.Top + 74), GoldLight);

    // Markers: a diamond at each Freeport, the chosen one ringed and named on the map.
    const float Pulse = .5f + .5f * FMath::Sin(Age * 3.f);
    for (int32 I = 0; I < Count; ++I)
    {
        const FVector2D M = L.Markers[I];
        const bool bChosen = I == Port, bHover = I == HoverPort;
        const float R = bChosen ? 11.f : bHover ? 9.f : 7.f;
        if (bChosen)
        {
            const float Ring = 18.f + 8.f * Pulse;
            P.Outline(6, FSlateRect(M.X - Ring, M.Y - Ring, M.X + Ring, M.Y + Ring), 2.f, GoldLight.CopyWithNewOpacity(1.f - .6f * Pulse));
        }
        // A diamond from stacked bars.
        for (int32 Row = -int32(R); Row <= int32(R); ++Row)
        {
            const float Half = R - FMath::Abs(Row);
            P.Box(7, FSlateRect(M.X - Half, M.Y + Row, M.X + Half, M.Y + Row + 1), bChosen ? GoldLight : bHover ? Gold : Cream);
        }
        // Named on the map when chosen or pointed at; the list beside names them all.
        if (!bChosen && !bHover) continue;
        const FString Label = List[I].Name;
        const FSlateFontInfo LabelFont = Font(bChosen ? 15 : 13, bChosen);
        const FVector2D TextSize = Measure(Label, LabelFont);
        // Named below its marker, kept inside the map.
        const float X = FMath::Clamp(M.X, L.Map.Left + TextSize.X * .5f + 8, L.Map.Right - TextSize.X * .5f - 8);
        P.Box(7, FSlateRect(X - TextSize.X * .5f - 8, M.Y + 18, X + TextSize.X * .5f + 8, M.Y + 22 + TextSize.Y), Ground.CopyWithNewOpacity(.72f));
        P.Text(8, Label, LabelFont, FVector2D(X, M.Y + 20), bChosen ? GoldLight : Cream, FVector2D(.5f, 0));
    }

    // The list.
    P.Text(5, TEXT("FREEPORTS"), Font(12, true, 380), FVector2D(L.List.Left + 26, L.List.Top - 26), Gold);
    for (int32 I = 0; I < Count; ++I)
    {
        const FSlateRect E = L.Entries[I];
        const bool bChosen = I == Port, bHover = I == HoverPort;
        if (bChosen) { P.Box(5, E, Highlight * 1.6f); P.Box(6, FSlateRect(E.Left, E.Top, E.Left + 4, E.Bottom), Gold); }
        else if (bHover) P.Box(5, E, Highlight);
        P.Text(7, List[I].Name, Font(17, true), FVector2D(E.Left + 20, E.Top + 12), bChosen ? GoldLight : Cream);
        P.Text(7, FString::Printf(TEXT("%s  ·  %s"), List[I].Island, List[I].Region), Font(13), FVector2D(E.Left + 20, E.Top + 40), Muted);
        if (bChosen && E.GetSize().Y > 92)
        {
            // The line, wrapped to the entry's width.
            const FSlateFontInfo LineFont = Font(12);
            TArray<FString> Words;
            FString(List[I].Line).ParseIntoArray(Words, TEXT(" "));
            FString Current;
            float Y = E.Top + 64;
            for (const FString& Word : Words)
            {
                const FString Next = Current.IsEmpty() ? Word : Current + TEXT(" ") + Word;
                if (!Current.IsEmpty() && Measure(Next, LineFont).X > E.GetSize().X - 36)
                {
                    P.Text(7, Current, LineFont, FVector2D(E.Left + 20, Y), Cream.CopyWithNewOpacity(.8f));
                    Y += 18;
                    Current = Word;
                }
                else Current = Next;
            }
            if (!Current.IsEmpty() && Y + 16 < E.Bottom) P.Text(7, Current, LineFont, FVector2D(E.Left + 20, Y), Cream.CopyWithNewOpacity(.8f));
        }
    }

    // Below the box, centred: Resume (when played before) and Create New Survivor.
    for (int32 I = 0; I < L.Buttons.Num(); ++I)
    {
        const bool bResume = bCanResume && I == 0;
        P.Button(5, L.Buttons[I], bResume ? TEXT("RESUME GAME") : TEXT("CREATE NEW SURVIVOR"), !bAsking && I == Focus, bResume || !bCanResume, 17);
        const FString Note = bResume ? (ResumeNote.IsEmpty() ? FString(TEXT("Continue where you left off")) : ResumeNote.ToString())
            : FString::Printf(TEXT("Start at %s"), List[Port].Name);
        P.Text(5, Note, Font(13), FVector2D(L.Buttons[I].GetCenter().X, L.Buttons[I].Bottom + 12), Muted, FVector2D(.5f, 0));
    }
    const FString Hint = bGamepad ? TEXT("D-pad: choose a Freeport    ← →: choose    A: confirm    B: back")
        : TEXT("Click a Freeport, or ↑ ↓ to choose    ← → and Enter to confirm    Esc: back");
    P.Text(5, Hint, Font(12), FVector2D(Size.X * .5f, Size.Y - 34), Muted.CopyWithNewOpacity(.75f), FVector2D(.5f, .5f));

    if (bAsking)
    {
        P.Box(20, FSlateRect(FVector2D::ZeroVector, Size), Ground.CopyWithNewOpacity(.7f));
        P.Box(21, L.AskPanel, Panel.CopyWithNewOpacity(1.f));
        P.Corners(22, L.AskPanel, 26.f, 3.f, Gold);
        P.Text(23, TEXT("Start a new survivor?"), Font(24, true), FVector2D(L.AskPanel.GetCenter().X, L.AskPanel.Top + 34), Cream, FVector2D(.5f, 0));
        P.Text(23, TEXT("Your survivor from before is replaced when the new one is first saved."), Font(14),
            FVector2D(L.AskPanel.GetCenter().X, L.AskPanel.Top + 84), Muted, FVector2D(.5f, 0));
        P.Button(23, L.AskYes, TEXT("START NEW"), AskFocus == 0, true, 15);
        P.Button(23, L.AskNo, TEXT("KEEP MY SURVIVOR"), AskFocus == 1, false, 15);
    }
    return Layer + 30;
}
