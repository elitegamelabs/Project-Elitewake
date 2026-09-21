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
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"EW",
			"EW/Variant_Platforming",
			"EW/Variant_Platforming/Animation",
			"EW/Variant_Combat",
			"EW/Variant_Combat/AI",
			"EW/Variant_Combat/Animation",
			"EW/Variant_Combat/Gameplay",
			"EW/Variant_Combat/Interfaces",
			"EW/Variant_Combat/UI",
			"EW/Variant_SideScrolling",
			"EW/Variant_SideScrolling/AI",
			"EW/Variant_SideScrolling/Gameplay",
			"EW/Variant_SideScrolling/Interfaces",
			"EW/Variant_SideScrolling/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
