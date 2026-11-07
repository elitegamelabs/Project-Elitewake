#if WITH_DEV_AUTOMATION_TESTS
#include "EWWorkFeedback.h"
#include "EWItemDefinition.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWHitMarkerMessagesTest, "Elitewake.WorkFeedback.HitMarkerMessages",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWHitMarkerMessagesTest::RunTest(const FString& Parameters)
{
    auto* Marker=NewObject<UEWHitMarkerWidget>(GetTransientPackage());
    TestEqual(TEXT("No markers at first"),Marker->GetMarkerCount(),0);
    const TArray<FEWGatherGain> None;
    Marker->ShowHit(false,None,EEWWorkRefusal::None);
    TestEqual(TEXT("A blow that gave nothing and was not refused says nothing"),Marker->GetLastLine(),FString());
    TestEqual(TEXT("But it still shows a marker"),Marker->GetMarkerCount(),1);
    for (const EEWWorkRefusal Refusal : {EEWWorkRefusal::NeedsHatchet,EEWWorkRefusal::NeedsPickaxe,EEWWorkRefusal::PackFull})
    {
        Marker->ShowHit(false,None,Refusal);
        TestFalse(*FString::Printf(TEXT("Refusal %d gives the player a message"),int32(Refusal)),Marker->GetLastLine().IsEmpty());
    }
    Marker->ShowHit(false,None,EEWWorkRefusal::NeedsHatchet);
    TestEqual(TEXT("Hatchet message"),Marker->GetLastLine(),FString(TEXT("Needs a hatchet")));
    Marker->ShowHit(false,None,EEWWorkRefusal::NeedsPickaxe);
    TestEqual(TEXT("Pickaxe message"),Marker->GetLastLine(),FString(TEXT("Needs a pickaxe")));
    Marker->ShowHit(false,None,EEWWorkRefusal::PackFull);
    TestEqual(TEXT("Full pack message"),Marker->GetLastLine(),FString(TEXT("Your pack is full")));

    auto* Wood=NewObject<UEWItemDefinition>(); Wood->DisplayName=FText::FromString(TEXT("Wood"));
    FEWGatherGain Gain; Gain.Item=Wood; Gain.Count=3;
    FEWGatherGain Empty; Empty.Item=Wood; Empty.Count=0;
    Marker->ShowGains({Gain});
    TestEqual(TEXT("A gain reads +count name"),Marker->GetLastLine(),FString(TEXT("+3 Wood")));
    Marker->ShowGains({Empty});
    TestEqual(TEXT("A zero gain adds no line"),Marker->GetLastLine(),FString(TEXT("+3 Wood")));
    const int32 Before=Marker->GetMarkerCount();
    Marker->ShowHit(true,{Gain},EEWWorkRefusal::None);
    TestEqual(TEXT("Each blow counts one marker"),Marker->GetMarkerCount(),Before+1);
    return true;
}
#endif
