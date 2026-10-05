#include "Animation/BlendSpace.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWStanceBlendSpaceTest, "Elitewake.Animation.StanceBlendSpaces",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEWStanceBlendSpaceTest::RunTest(const FString& Parameters)
{
    USkeleton* Target = LoadObject<USkeleton>(nullptr, TEXT("/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin"));
    USkeleton* Source = LoadObject<USkeleton>(nullptr, TEXT("/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin"));
    if (TestNotNull(TEXT("Quinn skeleton"), Target) && TestNotNull(TEXT("Library skeleton"), Source))
    {
        const FReferenceSkeleton& A = Target->GetReferenceSkeleton();
        const FReferenceSkeleton& B = Source->GetReferenceSkeleton();
        TestEqual(TEXT("Matching bone count"), A.GetNum(), B.GetNum());
        for (int32 Index = 0; Index < FMath::Min(A.GetNum(), B.GetNum()); ++Index)
        {
            TestEqual(TEXT("Matching bone name"), A.GetBoneName(Index), B.GetBoneName(Index));
            TestEqual(TEXT("Matching parent hierarchy"), A.GetParentIndex(Index), B.GetParentIndex(Index));
            TestTrue(TEXT("Matching reference transform"), A.GetRefBonePose()[Index].Equals(B.GetRefBonePose()[Index], 0.01f));
        }
        TestTrue(TEXT("Library registered as compatible"), Target->IsCompatibleForEditor(Source));
    }
    for (const TCHAR* Path : { TEXT("/Game/Elitewake/Animations/BS_EWCrouch.BS_EWCrouch"),
                              TEXT("/Game/Elitewake/Animations/BS_EWProne.BS_EWProne") })
    {
        UBlendSpace* BlendSpace = LoadObject<UBlendSpace>(nullptr, Path);
        if (!TestNotNull(Path, BlendSpace))
        {
            continue;
        }
        TestEqual(TEXT("Idle row and eight directions including seam duplicate"), BlendSpace->GetNumberOfBlendSamples(), 12);
        BlendSpace->ForEachImmutableSample([this](const FBlendSample& Sample)
        {
            if (TestNotNull(TEXT("Real animation sample"), Sample.Animation.Get()))
            {
                TestTrue(TEXT("CharacterMovement owns displacement"), Sample.Animation->bForceRootLock && !Sample.Animation->bEnableRootMotion);
            }
        });
        const float MaxSpeed = BlendSpace->GetBlendParameter(1).Max;
        for (const float Speed : { 0.f, MaxSpeed * 0.5f, MaxSpeed })
        {
            for (const float Direction : { -180.f, -135.f, -90.f, -45.f, 0.f, 45.f, 90.f, 135.f, 180.f })
            {
                TArray<FBlendSampleData> Samples;
                int32 Triangle = INDEX_NONE;
                const FString Label = FString::Printf(TEXT("%s direction %.0f speed %.0f"), Path, Direction, Speed);
                TestTrue(Label, BlendSpace->GetSamplesFromBlendInput(FVector(Direction, Speed, 0), Samples, Triangle, true));
                float TotalWeight = 0.f;
                for (const FBlendSampleData& Sample : Samples)
                {
                    TestTrue(TEXT("Sample resolves to a real animation"),
                        BlendSpace->GetBlendSample(Sample.SampleDataIndex).Animation != nullptr);
                    TotalWeight += Sample.TotalWeight;
                }
                TestTrue(Label + TEXT(" normalized weights"), FMath::IsNearlyEqual(TotalWeight, 1.f, 0.001f));
            }
        }
    }
    return true;
}
