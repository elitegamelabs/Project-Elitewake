#if WITH_DEV_AUTOMATION_TESTS
#include "Title/EWTitleWidget.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "Misc/AutomationTest.h"

// Route through Slate focus and hit testing: calling ContinueToMenu directly
// cannot detect an unfocusable or mouse-transparent painted widget.
class FEWTitleSlateInputCommand : public IAutomationLatentCommand
{
public:
    explicit FEWTitleSlateInputCommand(FAutomationTestBase* InTest) : Test(InTest) {}
    virtual bool Update() override
    {
        FSlateApplication& Slate = FSlateApplication::Get();
        if (!Window)
        {
            Window = SNew(SWindow).Title(FText::FromString(TEXT("Elitewake title input regression")))
                .ClientSize(FVector2D(960, 540)).ScreenPosition(FVector2D(60, 60));
            Slate.AddWindow(Window.ToSharedRef());
        }
        if (!Widget)
        {
            Widget = NewObject<UEWTitleWidget>();
            Widget->AddToRoot();
            Widget->Initialize();
            Widget->OnSinglePlayer.BindLambda([this]() { ++Starts; });
            Window->SetContent(Widget->TakeWidget());
            Frames = 0;
            return false;
        }
        if (++Frames < 4) return false;

        const TSharedRef<SWidget> Content = Widget->TakeWidget();
        const FGeometry Geometry = Content->GetCachedGeometry();
        const FVector2D Size = Geometry.GetLocalSize();
        if (Size.X <= 1 || Size.Y <= 1)
        {
            Test->AddError(TEXT("Title widget did not receive full-screen geometry"));
            Cleanup();
            return true;
        }
        Test->TestTrue(TEXT("Constructed Slate widget accepts keyboard focus"), Content->SupportsKeyboardFocus());
        Test->TestTrue(TEXT("Painted title is a mouse hit target"), Content->GetVisibility().IsHitTestVisible());
        Slate.SetKeyboardFocus(Content);
        auto Key = [&](FKey Value)
        {
            Slate.ProcessKeyDownEvent(FKeyEvent(Value, FModifierKeysState(), 0, false, 0, 0));
        };
        auto Pointer = [&](FKey Button, float Wheel, FVector2D Fraction)
        {
            const FVector2D Point = Geometry.LocalToAbsolute(Size * Fraction);
            TSet<FKey> Pressed;
            if (Button.IsValid()) Pressed.Add(Button);
            const FPointerEvent Event(0, Point, Point, Pressed, Button, Wheel, FModifierKeysState());
            Slate.ProcessMouseMoveEvent(Event);
            if (Wheel != 0)
                Slate.ProcessMouseWheelOrGestureEvent(Event, nullptr);
            else
            {
                Slate.ProcessMouseButtonDownEvent(Window->GetNativeWindow(), Event);
                Slate.ProcessMouseButtonUpEvent(FPointerEvent(0, Point, Point, TSet<FKey>(), Button, 0, FModifierKeysState()));
            }
        };
        switch (Scenario)
        {
        case 0: Key(EKeys::A); break;
        case 1: Pointer(EKeys::LeftMouseButton, 0, FVector2D(.5, .5)); break;
        case 2: Pointer(EKeys::RightMouseButton, 0, FVector2D(.5, .5)); break;
        case 3: Pointer(EKeys::MiddleMouseButton, 0, FVector2D(.5, .5)); break;
        case 4: Pointer(EKeys::ThumbMouseButton, 0, FVector2D(.5, .5)); break;
        case 5: Pointer(FKey(), 1, FVector2D(.5, .5)); break;
        case 6: Pointer(FKey(), -1, FVector2D(.5, .5)); break;
        }
        Test->TestTrue(FString::Printf(TEXT("Routed splash input %d opens main menu"), Scenario), Widget->IsMainMenuScreen());
        Test->TestEqual(TEXT("Splash input never starts gameplay"), Starts, 0);
        Key(EKeys::Enter);
        Key(EKeys::SpaceBar);
        Pointer(FKey(), 1, FVector2D(.25, .5));
        Pointer(EKeys::MiddleMouseButton, 0, FVector2D(.25, .5));
        Pointer(EKeys::LeftMouseButton, 0, FVector2D(.75, .5));
        Pointer(EKeys::RightMouseButton, 0, FVector2D(.75, .5));
        Test->TestEqual(TEXT("Keyboard, scroll, middle click and Multiplayer do not start gameplay"), Starts, 0);
        Pointer(EKeys::RightMouseButton, 0, FVector2D(.25, .5));
        Test->TestEqual(TEXT("Routed right click inside Single Player starts gameplay"), Starts, 1);
        Pointer(EKeys::LeftMouseButton, 0, FVector2D(.25, .5));
        Test->TestEqual(TEXT("Routed left click inside Single Player starts gameplay"), Starts, 2);

        Window->SetContent(SNullWidget::NullWidget);
        Widget->RemoveFromRoot();
        Widget = nullptr;
        Starts = 0;
        if (++Scenario < 7) return false;
        Cleanup();
        return true;
    }
private:
    void Cleanup()
    {
        if (Window) FSlateApplication::Get().RequestDestroyWindow(Window.ToSharedRef());
        if (Widget) Widget->RemoveFromRoot();
        Widget = nullptr;
        Window.Reset();
    }
    FAutomationTestBase* Test;
    TSharedPtr<SWindow> Window;
    UEWTitleWidget* Widget = nullptr;
    int32 Frames = 0;
    int32 Scenario = 0;
    int32 Starts = 0;
};

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWTitleSlateInputTest, "Elitewake.Title.RoutedKeyboardMouseAndWheel",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWTitleSlateInputTest::RunTest(const FString& Parameters)
{
    if (!FSlateApplication::IsInitialized())
    {
        AddError(TEXT("This input regression requires a Slate application"));
        return false;
    }
    ADD_LATENT_AUTOMATION_COMMAND(FEWTitleSlateInputCommand(this));
    return true;
}
#endif
