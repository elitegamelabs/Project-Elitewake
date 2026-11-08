#pragma once

#include "CoreMinimal.h"
#include "EWLogbook.generated.h"

/** What a ship's log line records (FUTURE_IMPLEMENTATIONS Part 8, 13). */
UENUM(BlueprintType)
enum class EEWLogKind : uint8 { Port, Damage, Repair, Discovery, Cargo, Note };

/** One line of a ship's log: what happened, and the hour of the day it was written. */
USTRUCT(BlueprintType)
struct FEWLogEntry
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly, Category="Logbook") EEWLogKind Kind = EEWLogKind::Note;
    UPROPERTY(BlueprintReadOnly, Category="Logbook") FString Text;
    /** The hour of the day, 0 to 24 (the world keeps no count of days yet). */
    UPROPERTY(BlueprintReadOnly, Category="Logbook") float Hour = 0.f;
};
