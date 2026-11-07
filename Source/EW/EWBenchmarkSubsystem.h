#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Containers/Ticker.h"
#include "EWBenchmarkSubsystem.generated.h"

/**
 * The minimum-machine benchmark (owner, November 2: the game must run on a GTX 1660 Super at 1920x1080 Low). Started only
 * with -EWBenchmark on the command line, in a Development build (never in Shipping): on Coastal Playground it tours a fixed
 * route (where the survivor spawns, Saltreach, then the nearest island of Jungle, Desert, Swamp and Winter), lets each stop
 * settle, turns the view slowly through a full circle while it records frame times, and then quits. It writes
 * Saved/EWBenchmark.json beside the game: each stop's mean, 95th-percentile and worst frame, GPU time, and the UTC times the
 * recording began and ended (the launcher, Scripts/Release/Run 1660 test.bat, samples video memory over the same times).
 */
UCLASS()
class EW_API UEWBenchmarkSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    static constexpr float SettleSeconds = 12.f;
    static constexpr float RecordSeconds = 20.f;
    static constexpr float WarmUpSeconds = 25.f;

private:
    bool Tick(float DeltaTime);
    bool MoveTo(int32 Stop);
    void Finish(const FString& Error);

    struct FStop { FString Name; FDateTime Began, Ended; TArray<float> FrameMs, GpuMs; bool bPlaced = false; };
    TArray<FStop> Stops;
    int32 Current = INDEX_NONE;
    float Clock = 0.f;
    bool bRecording = false;
    bool bDone = false;
    FTSTicker::FDelegateHandle TickHandle;
};
