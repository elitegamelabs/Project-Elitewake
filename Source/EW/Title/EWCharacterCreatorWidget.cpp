#include "Title/EWCharacterCreatorWidget.h"
#include "Title/EWFrontEndPaint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Input/Events.h"

using namespace EWFrontEnd;

namespace
{
const TCHAR* TabNames[] = {TEXT("BODY"), TEXT("FACE"), TEXT("HAIR"), TEXT("SKIN"), TEXT("MAKEUP"), TEXT("TATTOOS")};
constexpr int32 TabCount = UE_ARRAY_COUNT(TabNames);
constexpr float RowHeight = 50.f;
constexpr float HeaderHeight = 40.f;
const TCHAR* GroupName(EEWLookGroup Group)
{
    switch (Group)
    {
    case EEWLookGroup::Head: return TEXT("HEAD");
    case EEWLookGroup::Brows: return TEXT("BROWS");
    case EEWLookGroup::Eyes: return TEXT("EYES");
    case EEWLookGroup::Nose: return TEXT("NOSE");
    case EEWLookGroup::Cheeks: return TEXT("CHEEKS");
    case EEWLookGroup::Mouth: return TEXT("MOUTH");
    case EEWLookGroup::Jaw: return TEXT("JAW AND CHIN");
    case EEWLookGroup::Ears: return TEXT("EARS");
    default: return TEXT("");
    }
}
bool IsUp(const FKey& K) { return K == EKeys::Up || K == EKeys::W || K == EKeys::Gamepad_DPad_Up || K == EKeys::Gamepad_LeftStick_Up; }
bool IsDown(const FKey& K) { return K == EKeys::Down || K == EKeys::S || K == EKeys::Gamepad_DPad_Down || K == EKeys::Gamepad_LeftStick_Down; }
bool IsLeft(const FKey& K) { return K == EKeys::Left || K == EKeys::A || K == EKeys::Gamepad_DPad_Left || K == EKeys::Gamepad_LeftStick_Left; }
bool IsRight(const FKey& K) { return K == EKeys::Right || K == EKeys::D || K == EKeys::Gamepad_DPad_Right || K == EKeys::Gamepad_LeftStick_Right; }
}

TSharedRef<SWidget> UEWCharacterCreatorWidget::RebuildWidget()
{
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

void UEWCharacterCreatorWidget::NativeConstruct()
{
    Super::NativeConstruct();
    Appearance = Appearance.Clamped(Roster);
    Slots = Appearance.Tattoos;
    Slots.SetNum(FEWAppearance::MaxTattoos);
    BuildRows();
    Changed();
}

int32 UEWCharacterCreatorWidget::GetTabCount() const { return TabCount; }

void UEWCharacterCreatorWidget::BuildRows()
{
    Rows.Reset();
    auto Header = [this](const TCHAR* Label) { FRow R; R.Kind = ERowKind::Header; R.Label = Label; Rows.Add(R); };
    auto Slider = [this](int32 Index) { FRow R; R.Kind = ERowKind::Slider; R.Slider = Index; R.Label = FEWAppearance::Sliders()[Index].Label; Rows.Add(R); };
    auto Choice = [this](const TCHAR* Id) { FRow R; R.Kind = ERowKind::Choice; R.Choice = FEWAppearance::ChoiceIndex(Id); R.Label = FEWAppearance::Choices()[R.Choice].Label; Rows.Add(R); };
    auto Special = [this](ESpecial What, ERowKind Kind, const TCHAR* Label) { FRow R; R.Kind = Kind; R.Special = What; R.Label = Label; Rows.Add(R); };
    auto Group = [&](EEWLookGroup G) { for (int32 I = 0; I < FEWAppearance::Sliders().Num(); ++I) if (FEWAppearance::Sliders()[I].Group == G) Slider(I); };
    switch (Tab)
    {
    case 0:
        Special(ESpecial::Sex, ERowKind::Choice, TEXT("Survivor"));
        Special(ESpecial::Preset, ERowKind::Choice, TEXT("Start from preset"));
        Header(TEXT("SIZE AND SHAPE"));
        Group(EEWLookGroup::Body);
        break;
    case 1:
        for (EEWLookGroup G : {EEWLookGroup::Head, EEWLookGroup::Brows, EEWLookGroup::Eyes, EEWLookGroup::Nose, EEWLookGroup::Cheeks,
                               EEWLookGroup::Mouth, EEWLookGroup::Jaw, EEWLookGroup::Ears})
        {
            Header(GroupName(G));
            if (G == EEWLookGroup::Brows) Choice(TEXT("BrowStyle"));
            if (G == EEWLookGroup::Eyes) Choice(TEXT("EyeColour"));
            Group(G);
        }
        break;
    case 2:
        Choice(TEXT("HairStyle"));
        Choice(TEXT("HairColour"));
        Choice(TEXT("FacialHair"));
        break;
    case 3:
        Group(EEWLookGroup::Skin);
        Choice(TEXT("Scars"));
        break;
    case 4:
        Choice(TEXT("Makeup"));
        Choice(TEXT("MakeupColour"));
        Group(EEWLookGroup::Makeup);
        break;
    default:
        Special(ESpecial::TattooSlot, ERowKind::Choice, TEXT("Tattoo"));
        Special(ESpecial::TattooDesign, ERowKind::Choice, TEXT("Design"));
        Special(ESpecial::TattooPlace, ERowKind::Choice, TEXT("Placement"));
        Special(ESpecial::TattooSize, ERowKind::Slider, TEXT("Size"));
        Special(ESpecial::TattooAngle, ERowKind::Slider, TEXT("Turn"));
        Special(ESpecial::TattooInk, ERowKind::Choice, TEXT("Ink"));
        break;
    }
    Selected = FMath::Clamp(Selected, 0, FMath::Max(0, Selectable().Num() - 1));
}

TArray<int32> UEWCharacterCreatorWidget::Selectable() const
{
    TArray<int32> Out;
    for (int32 I = 0; I < Rows.Num(); ++I) if (Rows[I].Kind != ERowKind::Header) Out.Add(I);
    return Out;
}

int32 UEWCharacterCreatorWidget::GetRowCount() const { return Selectable().Num(); }

FString UEWCharacterCreatorWidget::GetSelectedRowLabel() const
{
    const TArray<int32> S = Selectable();
    return S.IsValidIndex(Selected) ? Rows[S[Selected]].Label : FString();
}

int32 UEWCharacterCreatorWidget::GetTotalOptionCount() const
{
    // Every slider and list on every tab, with sex, preset and the tattoo's six settings.
    return FEWAppearance::Sliders().Num() + FEWAppearance::Choices().Num() + 2 + 6;
}

void UEWCharacterCreatorWidget::ShowTab(int32 NewTab)
{
    Tab = (NewTab % TabCount + TabCount) % TabCount;
    Selected = 0;
    Scroll = 0.f;
    BuildRows();
}

void UEWCharacterCreatorWidget::Changed()
{
    Appearance = Appearance.Clamped(Roster);
    OnChanged.ExecuteIfBound();
}

void UEWCharacterCreatorWidget::SyncTattoos()
{
    Appearance.Tattoos.Reset();
    for (const FEWTattoo& T : Slots) if (T.Design != 0) Appearance.Tattoos.Add(T);
}

void UEWCharacterCreatorWidget::SelectBody(int32 Index)
{
    if (!Roster || !Roster->Bodies.IsValidIndex(Index)) return;
    Appearance.Body = static_cast<uint8>(Index);
    Changed();
}

void UEWCharacterCreatorWidget::SelectPreset(int32 Index)
{
    Appearance.ApplyPreset(Index);
    Slots = Appearance.Tattoos;
    Slots.SetNum(FEWAppearance::MaxTattoos);
    Changed();
}

void UEWCharacterCreatorWidget::SetSliderValue(const FString& Id, float Value)
{
    const int32 Index = FEWAppearance::SliderIndex(*Id);
    if (Index == INDEX_NONE) return;
    Appearance.SetSlider(Index, Value);
    Changed();
}

float UEWCharacterCreatorWidget::GetSliderValue(const FString& Id) const
{
    const int32 Index = FEWAppearance::SliderIndex(*Id);
    return Index == INDEX_NONE ? -1.f : Appearance.GetSlider(Index);
}

void UEWCharacterCreatorWidget::SetChoiceValue(const FString& Id, int32 Value)
{
    const int32 Index = FEWAppearance::ChoiceIndex(*Id);
    if (Index == INDEX_NONE) return;
    Appearance.SetPick(Index, Value);
    Changed();
}

void UEWCharacterCreatorWidget::SetTattoo(int32 TattooIndex, int32 Design, int32 Place, float Size, float Angle, int32 Ink)
{
    if (!Slots.IsValidIndex(TattooIndex)) return;
    FEWTattoo& T = Slots[TattooIndex];
    T.Design = static_cast<uint8>(FMath::Clamp(Design, 0, FEWAppearance::TattooDesigns().Num() - 1));
    T.Place = static_cast<uint8>(FMath::Clamp(Place, 0, FEWAppearance::TattooPlaces().Num() - 1));
    T.Size = static_cast<uint8>(FMath::RoundToInt(FMath::Clamp(Size, 0.f, 1.f) * 255.f));
    T.Angle = static_cast<uint8>(FMath::RoundToInt(FMath::Clamp(Angle, 0.f, 1.f) * 255.f));
    T.Ink = static_cast<uint8>(FMath::Clamp(Ink, 0, FEWAppearance::TattooInks().Num() - 1));
    SyncTattoos();
    Changed();
}

void UEWCharacterCreatorWidget::Randomise()
{
    Appearance.Randomise(int32(FPlatformTime::Cycles()) ^ (RandomSeed++ * 7919));
    Slots = Appearance.Tattoos;
    Slots.SetNum(FEWAppearance::MaxTattoos);
    Changed();
}

void UEWCharacterCreatorWidget::SetSail() { OnSetSail.ExecuteIfBound(); }
void UEWCharacterCreatorWidget::GoBack() { OnBack.ExecuteIfBound(); }

int32 UEWCharacterCreatorWidget::RowOptions(const FRow& Row) const
{
    switch (Row.Special)
    {
    case ESpecial::Sex: return Roster ? FMath::Max(1, Roster->Bodies.Num()) : 2;
    case ESpecial::Preset: return FEWAppearance::PresetNames().Num();
    case ESpecial::TattooSlot: return FEWAppearance::MaxTattoos;
    case ESpecial::TattooDesign: return FEWAppearance::TattooDesigns().Num();
    case ESpecial::TattooPlace: return FEWAppearance::TattooPlaces().Num();
    case ESpecial::TattooInk: return FEWAppearance::TattooInks().Num();
    default: return Row.Choice != INDEX_NONE ? FEWAppearance::Choices()[Row.Choice].Options.Num() : 1;
    }
}

float UEWCharacterCreatorWidget::RowValue(const FRow& Row) const
{
    const FEWTattoo& T = Slots[TattooSlot];
    switch (Row.Special)
    {
    case ESpecial::Sex: return Appearance.Body;
    case ESpecial::Preset: return Appearance.Preset;
    case ESpecial::TattooSlot: return TattooSlot;
    case ESpecial::TattooDesign: return T.Design;
    case ESpecial::TattooPlace: return T.Place;
    case ESpecial::TattooInk: return T.Ink;
    case ESpecial::TattooSize: return T.Size / 255.f;
    case ESpecial::TattooAngle: return T.Angle / 255.f;
    default: return Row.Kind == ERowKind::Slider ? Appearance.GetSlider(Row.Slider) : Appearance.GetPick(Row.Choice);
    }
}

FString UEWCharacterCreatorWidget::RowText(const FRow& Row) const
{
    const int32 V = FMath::RoundToInt(RowValue(Row));
    const FEWTattoo& T = Slots[TattooSlot];
    switch (Row.Special)
    {
    case ESpecial::Sex: return V == 0 ? TEXT("Male") : TEXT("Female");
    case ESpecial::Preset: return FEWAppearance::PresetNames()[V];
    case ESpecial::TattooSlot:
        return FString::Printf(TEXT("%d of %d  (%s)"), V + 1, FEWAppearance::MaxTattoos, Slots[V].Design ? FEWAppearance::TattooDesigns()[Slots[V].Design] : TEXT("empty"));
    case ESpecial::TattooDesign: return FEWAppearance::TattooDesigns()[V];
    case ESpecial::TattooPlace: return FEWAppearance::TattooPlaces()[V];
    case ESpecial::TattooInk: return FEWAppearance::TattooInks()[V];
    case ESpecial::TattooSize: return FString::Printf(TEXT("%d%%"), FMath::RoundToInt(FMath::Lerp(50.f, 150.f, T.Size / 255.f)));
    case ESpecial::TattooAngle: return FString::Printf(TEXT("%d°"), FMath::RoundToInt(FMath::Lerp(-180.f, 180.f, T.Angle / 255.f)));
    default: break;
    }
    if (Row.Kind == ERowKind::Choice) return FEWAppearance::Choices()[Row.Choice].Options[V];
    if (Row.Slider == 0)
    {
        // The mannequins stand about 180 cm (man) and 168 cm (woman) as made.
        const float Base = Appearance.Body == 0 ? 180.f : 168.f;
        const int32 Cm = FMath::RoundToInt(Base * Appearance.Height);
        return FString::Printf(TEXT("%d cm  (%d' %d\")"), Cm, int32(Cm / 30.48f), FMath::RoundToInt(FMath::Fmod(Cm / 2.54f, 12.f)) % 12);
    }
    return FString::Printf(TEXT("%d"), FMath::RoundToInt(RowValue(Row) * 100.f));
}

void UEWCharacterCreatorWidget::SetRowValue(const FRow& Row, float Value)
{
    FEWTattoo& T = Slots[TattooSlot];
    const int32 Options = RowOptions(Row);
    const int32 Pick = ((FMath::RoundToInt(Value) % Options) + Options) % Options;
    switch (Row.Special)
    {
    case ESpecial::Sex: SelectBody(Pick); return;
    case ESpecial::Preset: SelectPreset(Pick); return;
    case ESpecial::TattooSlot: TattooSlot = Pick; return;
    case ESpecial::TattooDesign: T.Design = static_cast<uint8>(Pick); break;
    case ESpecial::TattooPlace: T.Place = static_cast<uint8>(Pick); break;
    case ESpecial::TattooInk: T.Ink = static_cast<uint8>(Pick); break;
    case ESpecial::TattooSize: T.Size = static_cast<uint8>(FMath::RoundToInt(FMath::Clamp(Value, 0.f, 1.f) * 255.f)); break;
    case ESpecial::TattooAngle: T.Angle = static_cast<uint8>(FMath::RoundToInt(FMath::Clamp(Value, 0.f, 1.f) * 255.f)); break;
    default:
        if (Row.Kind == ERowKind::Slider) Appearance.SetSlider(Row.Slider, Value);
        else Appearance.SetPick(Row.Choice, Pick);
        Changed();
        return;
    }
    SyncTattoos();
    Changed();
}

void UEWCharacterCreatorWidget::Step(const FRow& Row, int32 Direction, bool bFine)
{
    if (Row.Kind == ERowKind::Slider) SetRowValue(Row, RowValue(Row) + Direction * (bFine ? .01f : .04f));
    else if (Row.Kind == ERowKind::Choice) SetRowValue(Row, RowValue(Row) + Direction);
}

void UEWCharacterCreatorWidget::MoveSelection(int32 Direction)
{
    const int32 Count = Selectable().Num();
    if (Count == 0) return;
    Selected = (Selected + Direction + Count) % Count;
    KeepSelectionInView();
}

void UEWCharacterCreatorWidget::KeepSelectionInView()
{
    const FLayout L = Layout(LastSize);
    const TArray<int32> S = Selectable();
    if (!S.IsValidIndex(Selected) || !L.Rows.IsValidIndex(S[Selected])) return;
    // The row index just before (a header) comes into view with it.
    const int32 RowIndex = S[Selected];
    const FSlateRect R = L.Rows[RowIndex];
    const float Top = RowIndex > 0 && Rows[RowIndex - 1].Kind == ERowKind::Header ? L.Rows[RowIndex - 1].Top : R.Top;
    if (Top < L.List.Top) Scroll -= L.List.Top - Top;
    else if (R.Bottom > L.List.Bottom) Scroll += R.Bottom - L.List.Bottom;
    Scroll = FMath::Max(0.f, Scroll);
}

UEWCharacterCreatorWidget::FLayout UEWCharacterCreatorWidget::Layout(const FVector2D& Size) const
{
    FLayout L;
    L.Preview = FSlateRect(Size.X * .025f, Size.Y * .05f, Size.X * .485f, Size.Y * .95f);
    L.Panel = FSlateRect(Size.X * .51f, 0, Size.X, Size.Y);
    const float Left = L.Panel.Left + 44.f, Right = Size.X - 44.f;
    const float TabTop = Size.Y * .05f + 96.f;
    for (int32 I = 0; I < TabCount; ++I)
        L.Tabs.Add(FSlateRect(Left + (Right - Left) * I / TabCount, TabTop, Left + (Right - Left) * (I + 1) / TabCount, TabTop + 46.f));
    L.List = FSlateRect(Left, TabTop + 62.f, Right, Size.Y - 150.f);
    float Y = L.List.Top - Scroll;
    for (const FRow& Row : Rows)
    {
        const float H = Row.Kind == ERowKind::Header ? HeaderHeight : RowHeight;
        L.Rows.Add(FSlateRect(Left, Y, Right, Y + H - 4.f));
        Y += H;
    }
    const float ButtonTop = Size.Y - 116.f;
    L.Back = FSlateRect(Left, ButtonTop, Left + 170.f, ButtonTop + 58.f);
    L.Random = FSlateRect(Left + 190.f, ButtonTop, Left + 400.f, ButtonTop + 58.f);
    L.Sail = FSlateRect(Right - 300.f, ButtonTop, Right, ButtonTop + 58.f);
    return L;
}

FSlateRect UEWCharacterCreatorWidget::ControlOf(const FSlateRect& Row) const
{
    return FSlateRect(Row.Left + Row.GetSize().X * .42f, Row.Top + 6.f, Row.Right - 10.f, Row.Bottom - 6.f);
}

FSlateRect UEWCharacterCreatorWidget::TrackOf(const FSlateRect& Row) const
{
    const FSlateRect C = ControlOf(Row);
    return FSlateRect(C.Left + 8.f, C.GetCenter().Y - 3.f, C.Right - 150.f, C.GetCenter().Y + 3.f);
}

FVector4 UEWCharacterCreatorWidget::GetPreviewBox() const
{
    const FSlateRect R = Layout(LastSize).Preview;
    return FVector4(R.Left, R.Top, R.GetSize().X, R.GetSize().Y);
}

void UEWCharacterCreatorWidget::NativeTick(const FGeometry& Geometry, float DeltaTime)
{
    Super::NativeTick(Geometry, DeltaTime);
    LastSize = Geometry.GetLocalSize();
    if (FMath::Abs(TurnAxis) > .15f) OnTurn.ExecuteIfBound(TurnAxis * 160.f * DeltaTime);
    // Keep the list from scrolling past its end.
    const FLayout L = Layout(LastSize);
    if (L.Rows.Num())
    {
        const float Content = L.Rows.Last().Bottom + Scroll - L.List.Top;
        Scroll = FMath::Clamp(Scroll, 0.f, FMath::Max(0.f, Content - L.List.GetSize().Y + 8.f));
    }
}

FReply UEWCharacterCreatorWidget::NativeOnMouseButtonDown(const FGeometry& Geometry, const FPointerEvent& Event)
{
    bGamepad = false;
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Handled();
    const FVector2D At = Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition());
    const FLayout L = Layout(Geometry.GetLocalSize());
    for (int32 I = 0; I < L.Tabs.Num(); ++I) if (L.Tabs[I].ContainsPoint(At)) { ShowTab(I); return FReply::Handled(); }
    if (L.Back.ContainsPoint(At)) { GoBack(); return FReply::Handled(); }
    if (L.Random.ContainsPoint(At)) { Randomise(); return FReply::Handled(); }
    if (L.Sail.ContainsPoint(At)) { SetSail(); return FReply::Handled(); }
    if (L.Preview.ContainsPoint(At)) { bTurning = true; return FReply::Handled().CaptureMouse(TakeWidget()); }
    if (L.List.ContainsPoint(At))
    {
        const TArray<int32> S = Selectable();
        for (int32 K = 0; K < S.Num(); ++K)
        {
            const FSlateRect R = L.Rows[S[K]];
            if (!R.ContainsPoint(At)) continue;
            Selected = K;
            const FRow& Row = Rows[S[K]];
            const FSlateRect C = ControlOf(R);
            if (!C.ContainsPoint(At)) return FReply::Handled();
            if (Row.Kind == ERowKind::Slider)
            {
                const FSlateRect T = TrackOf(R);
                SetRowValue(Row, (At.X - T.Left) / FMath::Max(1.0, T.GetSize().X));
                DragRow = S[K];
                return FReply::Handled().CaptureMouse(TakeWidget());
            }
            Step(Row, At.X < C.GetCenter().X ? -1 : 1);
            return FReply::Handled();
        }
    }
    return FReply::Handled();
}

FReply UEWCharacterCreatorWidget::NativeOnMouseButtonUp(const FGeometry& Geometry, const FPointerEvent& Event)
{
    DragRow = INDEX_NONE;
    bTurning = false;
    return FReply::Handled().ReleaseMouseCapture();
}

FReply UEWCharacterCreatorWidget::NativeOnMouseMove(const FGeometry& Geometry, const FPointerEvent& Event)
{
    const FVector2D At = Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition());
    const FLayout L = Layout(Geometry.GetLocalSize());
    if (!Event.GetCursorDelta().IsNearlyZero()) bGamepad = false;
    if (bTurning) { OnTurn.ExecuteIfBound(Event.GetCursorDelta().X * .5f); return FReply::Handled(); }
    if (Rows.IsValidIndex(DragRow))
    {
        const FSlateRect T = TrackOf(L.Rows[DragRow]);
        SetRowValue(Rows[DragRow], (At.X - T.Left) / FMath::Max(1.0, T.GetSize().X));
        return FReply::Handled();
    }
    HoverButton = L.Back.ContainsPoint(At) ? 0 : L.Random.ContainsPoint(At) ? 1 : L.Sail.ContainsPoint(At) ? 2 : INDEX_NONE;
    if (L.List.ContainsPoint(At))
    {
        const TArray<int32> S = Selectable();
        for (int32 K = 0; K < S.Num(); ++K) if (L.Rows[S[K]].ContainsPoint(At)) Selected = K;
    }
    return FReply::Handled();
}

FReply UEWCharacterCreatorWidget::NativeOnMouseWheel(const FGeometry& Geometry, const FPointerEvent& Event)
{
    const FVector2D At = Geometry.AbsoluteToLocal(Event.GetScreenSpacePosition());
    const FLayout L = Layout(Geometry.GetLocalSize());
    if (L.Preview.ContainsPoint(At)) OnZoom.ExecuteIfBound(Event.GetWheelDelta());
    else Scroll = FMath::Max(0.f, Scroll - Event.GetWheelDelta() * RowHeight * 1.5f);
    return FReply::Handled();
}

FReply UEWCharacterCreatorWidget::NativeOnAnalogValueChanged(const FGeometry& Geometry, const FAnalogInputEvent& Event)
{
    if (Event.GetKey() == EKeys::Gamepad_RightX) { TurnAxis = Event.GetAnalogValue(); bGamepad = true; return FReply::Handled(); }
    return Super::NativeOnAnalogValueChanged(Geometry, Event);
}

FReply UEWCharacterCreatorWidget::NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
    const FKey Key = Event.GetKey();
    if (Key.IsGamepadKey()) bGamepad = true;
    else if (!Key.IsMouseButton()) bGamepad = false;
    const TArray<int32> S = Selectable();
    const FRow* Row = S.IsValidIndex(Selected) ? &Rows[S[Selected]] : nullptr;
    if (IsUp(Key)) MoveSelection(-1);
    else if (IsDown(Key)) MoveSelection(1);
    else if (IsLeft(Key) && Row) Step(*Row, -1, Event.IsShiftDown());
    else if (IsRight(Key) && Row) Step(*Row, 1, Event.IsShiftDown());
    else if (Key == EKeys::Gamepad_LeftShoulder || Key == EKeys::PageUp || (Key == EKeys::Tab && Event.IsShiftDown())) ShowTab(Tab - 1);
    else if (Key == EKeys::Gamepad_RightShoulder || Key == EKeys::PageDown || Key == EKeys::Tab) ShowTab(Tab + 1);
    else if (Key == EKeys::Q) OnTurn.ExecuteIfBound(-15.f);
    else if (Key == EKeys::E) OnTurn.ExecuteIfBound(15.f);
    else if (Key == EKeys::Gamepad_RightTrigger || Key == EKeys::Equals || Key == EKeys::Add) OnZoom.ExecuteIfBound(1.f);
    else if (Key == EKeys::Gamepad_LeftTrigger || Key == EKeys::Hyphen || Key == EKeys::Subtract) OnZoom.ExecuteIfBound(-1.f);
    else if (Key == EKeys::R || Key == EKeys::Gamepad_FaceButton_Top) Randomise();
    else if ((Key == EKeys::Delete || Key == EKeys::Gamepad_FaceButton_Left) && Row) SetRowValue(*Row, Row->Kind == ERowKind::Slider ? .5f : 0.f);
    else if (Key == EKeys::Gamepad_FaceButton_Bottom && Row && Row->Kind == ERowKind::Choice) Step(*Row, 1);
    else if (Key == EKeys::Enter || Key == EKeys::Gamepad_Special_Right) SetSail();
    else if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right) GoBack();
    else return FReply::Unhandled();
    return FReply::Handled();
}

int32 UEWCharacterCreatorWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const int32 Layer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
    const FPainter P{AllottedGeometry, OutDrawElements, Layer};
    const FVector2D Size = AllottedGeometry.GetLocalSize();
    const FLayout L = Layout(Size);
    const FSlateRect& V = L.Preview;

    // The ground around the preview box (the survivor shows through the box), and the panel.
    P.Box(1, FSlateRect(0, 0, L.Panel.Left, V.Top), Ground);
    P.Box(1, FSlateRect(0, V.Bottom, L.Panel.Left, Size.Y), Ground);
    P.Box(1, FSlateRect(0, V.Top, V.Left, V.Bottom), Ground);
    P.Box(1, FSlateRect(V.Right, V.Top, L.Panel.Left, V.Bottom), Ground);
    P.Box(1, L.Panel, Panel.CopyWithNewOpacity(1.f));
    P.Gradient(2, FSlateRect(V.Left, V.Bottom - 120, V.Right, V.Bottom), {Ground.CopyWithNewOpacity(0.f), Ground.CopyWithNewOpacity(.75f)}, false);
    P.Outline(3, V, 1.f, Line);
    P.Corners(4, FSlateRect(V.Left - 6, V.Top - 6, V.Right + 6, V.Bottom + 6), 34.f, 3.f, Gold);
    const FString Who = FString::Printf(TEXT("%s  ·  %s"), Appearance.Body == 0 ? TEXT("MALE") : TEXT("FEMALE"),
        *FString(FEWAppearance::PresetNames()[Appearance.Preset]).ToUpper());
    P.Text(5, Who, Font(12, true, 300), FVector2D(V.Left + 26, V.Top + 22), GoldLight);
    P.Text(5, bGamepad ? TEXT("Right stick: turn    LT / RT: zoom") : TEXT("Drag: turn    Wheel: zoom    Q / E: turn"),
        Font(12), FVector2D(V.GetCenter().X, V.Bottom - 54), Cream.CopyWithNewOpacity(.85f), FVector2D(.5f, .5f));
    P.Text(5, TEXT("The stand-in figure shows body, size and skin. Face, hair, makeup and tattoos are kept for your survivor's final model."),
        Font(10), FVector2D(V.GetCenter().X, V.Bottom - 28), Muted.CopyWithNewOpacity(.8f), FVector2D(.5f, .5f));

    // Heading and tabs.
    const float Left = L.Tabs[0].Left;
    P.Text(5, TEXT("NEW SURVIVOR"), Font(12, true, 420), FVector2D(Left, Size.Y * .05f), Gold);
    P.Text(5, TEXT("Create your survivor"), Font(30, true), FVector2D(Left, Size.Y * .05f + 24), Cream);
    for (int32 I = 0; I < TabCount; ++I)
    {
        const FSlateRect T = L.Tabs[I];
        const bool bOn = I == Tab;
        if (bOn) P.Box(5, T, Highlight * 1.5f);
        P.Box(6, FSlateRect(T.Left, T.Bottom - (bOn ? 3 : 1), T.Right, T.Bottom), bOn ? Gold : Line);
        P.Text(7, TabNames[I], Font(13, true, 220), T.GetCenter(), bOn ? GoldLight : Cream.CopyWithNewOpacity(.75f), FVector2D(.5f, .5f));
    }
    if (bGamepad)
    {
        P.Text(7, TEXT("LB"), Font(11, true), FVector2D(L.Tabs[0].Left - 8, L.Tabs[0].GetCenter().Y), Muted, FVector2D(1, .5f));
        P.Text(7, TEXT("RB"), Font(11, true), FVector2D(L.Tabs.Last().Right + 8, L.Tabs.Last().GetCenter().Y), Muted, FVector2D(0, .5f));
    }

    // Rows, those wholly inside the list.
    const TArray<int32> S = Selectable();
    const int32 Chosen = S.IsValidIndex(Selected) ? S[Selected] : INDEX_NONE;
    for (int32 I = 0; I < Rows.Num(); ++I)
    {
        const FSlateRect R = L.Rows[I];
        if (R.Top < L.List.Top - 1 || R.Bottom > L.List.Bottom + 1) continue;
        const FRow& Row = Rows[I];
        if (Row.Kind == ERowKind::Header)
        {
            P.Text(6, Row.Label, Font(11, true, 380), FVector2D(R.Left + 4, R.Bottom - 8), Gold, FVector2D(0, 1));
            P.Box(6, FSlateRect(R.Left, R.Bottom - 2, R.Right, R.Bottom - 1), Line);
            continue;
        }
        const bool bOn = I == Chosen;
        if (bOn) { P.Box(5, R, Highlight * 1.4f); P.Box(6, FSlateRect(R.Left, R.Top, R.Left + 4, R.Bottom), Gold); }
        P.Text(7, Row.Label, Font(15, bOn), FVector2D(R.Left + 18, R.GetCenter().Y), bOn ? GoldLight : Cream, FVector2D(0, .5f));
        const FSlateRect C = ControlOf(R);
        if (Row.Kind == ERowKind::Slider)
        {
            const FSlateRect T = TrackOf(R);
            const float Value = RowValue(Row);
            const bool bSkin = Row.Slider == FEWAppearance::SliderIndex(TEXT("SkinTone"));
            if (bSkin && Roster && Roster->Tones.Num() > 1)
            {
                TArray<FLinearColor> Tones;
                for (const FLinearColor& Tone : Roster->Tones) Tones.Add(Tone.CopyWithNewOpacity(1.f));
                P.Gradient(7, FSlateRect(T.Left, T.Top - 3, T.Right, T.Bottom + 3), Tones, true);
            }
            else
            {
                P.Box(7, T, Cream.CopyWithNewOpacity(.18f));
                P.Box(8, FSlateRect(T.Left, T.Top, FMath::Lerp(T.Left, T.Right, Value), T.Bottom), bOn ? Gold : Gold.CopyWithNewOpacity(.7f));
                P.Box(8, FSlateRect(T.GetCenter().X - .5f, T.Top - 4, T.GetCenter().X + .5f, T.Bottom + 4), Cream.CopyWithNewOpacity(.35f));
            }
            const float X = FMath::Lerp(T.Left, T.Right, Value);
            const float K = bOn ? 9.f : 7.f;
            P.Box(9, FSlateRect(X - K, T.GetCenter().Y - K, X + K, T.GetCenter().Y + K), bOn ? GoldLight : Cream);
            P.Outline(10, FSlateRect(X - K, T.GetCenter().Y - K, X + K, T.GetCenter().Y + K), 1.f, Ground);
            P.Text(9, RowText(Row), Font(13, bOn), FVector2D(C.Right - 4, C.GetCenter().Y), bOn ? GoldLight : Muted, FVector2D(1, .5f));
        }
        else
        {
            const FSlateRect LeftArrow(C.Left, C.Top, C.Left + 34, C.Bottom), RightArrow(C.Right - 34, C.Top, C.Right, C.Bottom);
            P.Box(7, LeftArrow, Highlight * (bOn ? 1.8f : 1.f));
            P.Box(7, RightArrow, Highlight * (bOn ? 1.8f : 1.f));
            P.Text(8, TEXT("‹"), Font(18, true), LeftArrow.GetCenter(), bOn ? GoldLight : Cream, FVector2D(.5f, .5f));
            P.Text(8, TEXT("›"), Font(18, true), RightArrow.GetCenter(), bOn ? GoldLight : Cream, FVector2D(.5f, .5f));
            P.Text(8, RowText(Row), Font(14, bOn), C.GetCenter(), bOn ? GoldLight : Cream, FVector2D(.5f, .5f));
        }
    }
    // Scroll cues.
    if (Scroll > 1.f) P.Text(8, TEXT("▲"), Font(10), FVector2D(L.List.GetCenter().X, L.List.Top - 10), Muted, FVector2D(.5f, .5f));
    if (L.Rows.Num() && L.Rows.Last().Bottom > L.List.Bottom + 1)
        P.Text(8, TEXT("▼"), Font(10), FVector2D(L.List.GetCenter().X, L.List.Bottom + 10), Muted, FVector2D(.5f, .5f));

    // Buttons and the controls.
    P.Button(6, L.Back, bGamepad ? TEXT("B  BACK") : TEXT("BACK"), HoverButton == 0, false, 14);
    P.Button(6, L.Random, bGamepad ? TEXT("Y  RANDOMISE") : TEXT("RANDOMISE"), HoverButton == 1, false, 14);
    P.Button(6, L.Sail, bGamepad ? TEXT("START  SET SAIL") : TEXT("SET SAIL"), HoverButton == 2, true, 18);
    const FString Hint = bGamepad ? TEXT("D-pad ↑↓: choose    ←→: change    A: next option    X: reset    LB / RB: tabs")
        : TEXT("↑↓: choose    ←→: change (Shift: fine)    Del: reset    Tab: next tab    R: randomise    Enter: set sail");
    P.Text(6, Hint, Font(11), FVector2D(L.Panel.GetCenter().X, Size.Y - 30), Muted.CopyWithNewOpacity(.8f), FVector2D(.5f, .5f));
    return Layer + 14;
}
