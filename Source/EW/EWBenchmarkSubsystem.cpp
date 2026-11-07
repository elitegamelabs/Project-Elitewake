#include "EWBenchmarkSubsystem.h"
#include "EWCharacter.h"
#include "EWPlayerController.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "RHI.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "HAL/PlatformTime.h"

bool UEWBenchmarkSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
#if UE_BUILD_SHIPPING
    return false;
#else
    return FParse::Param(FCommandLine::Get(), TEXT("EWBenchmark"));
#endif
}

void UEWBenchmarkSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    for (const TCHAR* Name : {TEXT("Spawn"), TEXT("Saltreach"), TEXT("Jungle"), TEXT("Desert"), TEXT("Swamp"), TEXT("Winter")})
    {
        FStop Stop; Stop.Name = Name; Stops.Add(Stop);
    }
    Clock = -WarmUpSeconds;          // the world loads and settles before the first stop
    TickHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &UEWBenchmarkSubsystem::Tick));
    UE_LOG(LogTemp, Display, TEXT("EWBENCHMARK started: %d stops"), Stops.Num());
}

void UEWBenchmarkSubsystem::Deinitialize()
{
    FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
    Super::Deinitialize();
}

bool UEWBenchmarkSubsystem::MoveTo(int32 Stop)
{
    UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
    auto* Controller = World ? Cast<AEWPlayerController>(UGameplayStatics::GetPlayerController(World, 0)) : nullptr;
    auto* Survivor = Controller ? Cast<AEWCharacter>(Controller->GetPawn()) : nullptr;
    if (!Survivor) return false;
    if (Stops[Stop].Name == TEXT("Spawn")) return true;                       // stay where the survivor spawned
    if (Stops[Stop].Name == TEXT("Saltreach")) { Controller->DebugTeleportToPort(); return true; }
    static const TMap<FString, int32> Regions = {{TEXT("Jungle"), 1}, {TEXT("Desert"), 2}, {TEXT("Swamp"), 3}, {TEXT("Winter"), 4}};
    FVector Spot;
    if (!AEWPlayerController::FindRegionLanding(World, Regions.FindRef(Stops[Stop].Name), Spot, Survivor)) return false;
    return Survivor->TeleportTo(Spot, Survivor->GetActorRotation(), false, true);
}

bool UEWBenchmarkSubsystem::Tick(float DeltaTime)
{
    if (bDone) return false;
    UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
    if (!World || !World->HasBegunPlay() || !UGameplayStatics::GetPlayerPawn(World, 0)) return true;
    Clock += DeltaTime;
    if (Clock < 0.f) return true;
    if (Current == INDEX_NONE || (bRecording && Clock >= RecordSeconds))
    {
        if (Current != INDEX_NONE) { Stops[Current].Ended = FDateTime::UtcNow(); bRecording = false; }
        if (++Current >= Stops.Num()) { Finish(FString()); return false; }
        if (!MoveTo(Current)) { Finish(FString::Printf(TEXT("could not reach %s"), *Stops[Current].Name)); return false; }
        Stops[Current].bPlaced = true;
        Clock = 0.f;
        return true;
    }
    if (!bRecording && Clock >= SettleSeconds)
    {
        bRecording = true; Clock = 0.f;
        Stops[Current].Began = FDateTime::UtcNow();
        return true;
    }
    if (bRecording)
    {
        FStop& Stop = Stops[Current];
        Stop.FrameMs.Add(DeltaTime * 1000.f);
        Stop.GpuMs.Add(FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles()));
        // A slow full turn of the view while recording, so every direction is drawn.
        if (APlayerController* Controller = UGameplayStatics::GetPlayerController(World, 0))
        {
            FRotator View = Controller->GetControlRotation();
            View.Pitch = -5.f;
            View.Yaw += 360.f / RecordSeconds * DeltaTime;
            Controller->SetControlRotation(View);
        }
    }
    return true;
}

namespace
{
    float Percentile(TArray<float> Values, float P)
    {
        if (Values.IsEmpty()) return 0.f;
        Values.Sort();
        return Values[FMath::Clamp(FMath::FloorToInt(P * (Values.Num() - 1)), 0, Values.Num() - 1)];
    }
    float Mean(const TArray<float>& Values)
    {
        if (Values.IsEmpty()) return 0.f;
        double Sum = 0.0; for (float V : Values) Sum += V;
        return float(Sum / Values.Num());
    }
}

void UEWBenchmarkSubsystem::Finish(const FString& Error)
{
    bDone = true;
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetBoolField(TEXT("success"), Error.IsEmpty());
    Root->SetStringField(TEXT("error"), Error);
    Root->SetStringField(TEXT("gpu"), GRHIAdapterName);
    const FIntPoint Size = GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport ? GEngine->GameViewport->Viewport->GetSizeXY() : FIntPoint::ZeroValue;
    Root->SetStringField(TEXT("resolution"), FString::Printf(TEXT("%dx%d"), Size.X, Size.Y));
    TArray<TSharedPtr<FJsonValue>> Out;
    for (const FStop& Stop : Stops)
    {
        if (!Stop.bPlaced) continue;
        TSharedRef<FJsonObject> S = MakeShared<FJsonObject>();
        S->SetStringField(TEXT("stop"), Stop.Name);
        S->SetStringField(TEXT("began_utc"), Stop.Began.ToIso8601());
        S->SetStringField(TEXT("ended_utc"), Stop.Ended.ToIso8601());
        S->SetNumberField(TEXT("frames"), Stop.FrameMs.Num());
        S->SetNumberField(TEXT("frame_ms_mean"), FMath::RoundToFloat(Mean(Stop.FrameMs) * 10.f) / 10.f);
        S->SetNumberField(TEXT("frame_ms_p95"), FMath::RoundToFloat(Percentile(Stop.FrameMs, .95f) * 10.f) / 10.f);
        S->SetNumberField(TEXT("frame_ms_worst"), FMath::RoundToFloat(Percentile(Stop.FrameMs, 1.f) * 10.f) / 10.f);
        S->SetNumberField(TEXT("gpu_ms_mean"), FMath::RoundToFloat(Mean(Stop.GpuMs) * 10.f) / 10.f);
        Out.Add(MakeShared<FJsonValueObject>(S));
    }
    Root->SetArrayField(TEXT("stops"), Out);
    FString Text;
    auto Writer = TJsonWriterFactory<>::Create(&Text);
    FJsonSerializer::Serialize(Root, Writer);
    FFileHelper::SaveStringToFile(Text, *FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("EWBenchmark.json")));
    UE_LOG(LogTemp, Display, TEXT("EWBENCHMARK finished success=%d %s"), Error.IsEmpty() ? 1 : 0, *Error);
    FPlatformMisc::RequestExit(false, TEXT("EWBenchmark"));
}
