#include "EWAnimationEditorLibrary.h"
#include "Animation/BlendSpace.h"

bool UEWAnimationEditorLibrary::CompileBlendSpace(UBlendSpace* BlendSpace)
{
    if (!BlendSpace || !BlendSpace->GetSkeleton() || BlendSpace->GetNumberOfBlendSamples() == 0)
    {
        return false;
    }

    BlendSpace->Modify();
    BlendSpace->ValidateSampleData();
    for (int32 Index = 0; Index < BlendSpace->GetNumberOfBlendSamples(); ++Index)
    {
        if (!BlendSpace->IsValidBlendSampleIndex(Index))
        {
            return false;
        }
    }
    BlendSpace->ResampleData();
    TArray<FBlendSampleData> Samples;
    int32 Triangle = INDEX_NONE;
    if (!BlendSpace->GetSamplesFromBlendInput(FVector::ZeroVector, Samples, Triangle, true) || Samples.IsEmpty())
    {
        return false;
    }
    BlendSpace->MarkPackageDirty();
    return true;
}
