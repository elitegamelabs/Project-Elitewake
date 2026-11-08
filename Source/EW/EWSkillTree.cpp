// Copyright Elite Game Labs. All Rights Reserved.

#include "EWSkillTree.h"
#include "EWCraftingRecipe.h"

namespace
{
    FEWSkillNode Node(const TCHAR* Id, const TCHAR* Title, const TCHAR* Description, double X, double Y, int32 Cost, std::initializer_list<const TCHAR*> Requires,
        std::initializer_list<const TCHAR*> RecipeNames = {}, float Health = 0.f, float Stamina = 0.f, float Carry = 0.f)
    {
        FEWSkillNode N;
        N.Id = Id; N.Title = FText::FromString(Title); N.Description = FText::FromString(Description);
        N.Position = FVector2D(X, Y); N.Cost = Cost;
        for (const TCHAR* R : Requires) N.Requires.Add(R);
        for (const TCHAR* Name : RecipeNames)
            N.Recipes.Add(TSoftObjectPtr<UEWCraftingRecipe>(FSoftObjectPath(FString::Printf(TEXT("/Game/Elitewake/Crafting/Testing/DA_Recipe%s.DA_Recipe%s"), Name, Name))));
        N.MaxHealthBonus = Health; N.MaxStaminaBonus = Stamina; N.CarryBonus = Carry;
        return N;
    }
}

const TArray<FEWSkillNode>& FEWSkillTree::Nodes()
{
    // The Wayfarer: a first constellation of eight stars rising from the root. Costs, bonuses and recipes are working values.
    static const TArray<FEWSkillNode> Tree = {
        Node(TEXT("FirstLight"), TEXT("First Light"), TEXT("Where every survivor begins: working with the hands. The stars above are lit one by one with skill points, one earned for each level."), .50, .90, 0, {}),
        Node(TEXT("Gatherer"), TEXT("Gatherer"), TEXT("A trained eye for good timber, stone and healing plants. Unlocks the Hatchet and Herbal Remedy recipes and lets you carry 5 kg more."), .30, .68, 1, {TEXT("FirstLight")}, {TEXT("Hatchet"), TEXT("HerbalRemedy")}, 0.f, 0.f, 5.f),
        Node(TEXT("Torchbearer"), TEXT("Torchbearer"), TEXT("Light for the long night, and a fire to cook by. Unlocks the Inn Torch, Cooked Fish and Cooked Meat recipes."), .70, .68, 1, {TEXT("FirstLight")}, {TEXT("InnTorch"), TEXT("CookedFish"), TEXT("CookedMeat")}),
        Node(TEXT("Hardy"), TEXT("Hardy"), TEXT("A body that shrugs off knocks. +10 maximum health."), .16, .44, 1, {TEXT("Gatherer")}, {}, 10.f),
        Node(TEXT("FieldRepair"), TEXT("Field Repair"), TEXT("Patch a hull with what you carry. Unlocks the Repair Kit recipe."), .40, .46, 1, {TEXT("Gatherer")}, {TEXT("PrologueRepairKit")}),
        Node(TEXT("StrongBack"), TEXT("Strong Back"), TEXT("Carry more for the same effort. +10 kg carrying capacity."), .84, .44, 1, {TEXT("Torchbearer")}, {}, 0.f, 0.f, 10.f),
        Node(TEXT("SecondWind"), TEXT("Second Wind"), TEXT("Breath comes back sooner and runs deeper. +10 maximum stamina."), .62, .46, 1, {TEXT("Torchbearer")}, {}, 0.f, 10.f),
        // November 7: smelting the islands' ores into ingots at a fire (copper ore, iron ore, bog iron; add_smelting.py).
        Node(TEXT("Metalwork"), TEXT("Metalwork"), TEXT("Smelt ore into ingots at a fire, and shape metal into a pickaxe that bites into harder rock. Unlocks the Iron Ingot, Copper Ingot and Metal Pickaxe recipes, the metal armor (tricorn helmet, cuirass, pants), and a brass sextant for finding latitude."), .30, .20, 2, {TEXT("FieldRepair")}, {TEXT("MetalPickaxe"), TEXT("IronIngot"), TEXT("CopperIngot"), TEXT("IronIngotFromBogIron"),
            TEXT("MetalTricornHelmet"), TEXT("MetalCuirass"), TEXT("MetalPants"), TEXT("Sextant")}),
        Node(TEXT("DeepReserves"), TEXT("Deep Reserves"), TEXT("Strength held back for when it counts. +10 maximum health and +10 maximum stamina."), .72, .20, 2, {TEXT("Hardy"), TEXT("SecondWind")}, {}, 10.f, 10.f),
    };
    return Tree;
}

const FEWSkillNode* FEWSkillTree::Find(FName Id)
{
    return Nodes().FindByPredicate([Id](const FEWSkillNode& N) { return N.Id == Id; });
}
