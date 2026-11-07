// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class EW : ModuleRules
{
	public EW(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"UMG",
			"Slate",
            "SlateCore"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { "Water", "Json", "RHI", "MoviePlayer" });

		PublicIncludePaths.AddRange(new string[] {
			"EW"
		});

	}
}
