using UnrealBuildTool;

public class EWEditor : ModuleRules
{
    public EWEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "EnhancedInput", "EW", "Slate", "SlateCore", "InputCore" });
    }
}
