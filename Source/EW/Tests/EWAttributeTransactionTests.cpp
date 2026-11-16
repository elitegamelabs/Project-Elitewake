#if WITH_DEV_AUTOMATION_TESTS
#include "EWProgressionComponent.h"
#include "EWSurvivalComponent.h"
#include "EWWalletComponent.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWAttributeTransactionTest, "Elitewake.Progression.AttributeTransactions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEWAttributeTransactionTest::RunTest(const FString& Parameters)
{
    auto* Owner = NewObject<AActor>();
    auto* Progress = NewObject<UEWProgressionComponent>(Owner); Owner->AddInstanceComponent(Progress);
    auto* Wallet = NewObject<UEWWalletComponent>(Owner); Owner->AddInstanceComponent(Wallet);
    auto* Survival = NewObject<UEWSurvivalComponent>(Owner); Owner->AddInstanceComponent(Survival);
    Progress->Restore(6, 25, 5, {0, 0, 0, 0}, 3, {TEXT("Gatherer")});
    const auto Skills = Progress->GetUnlockedSkills();
    const int32 SkillPoints = Progress->GetSkillPoints();
    auto Good = [] { return true; };
    auto Bad = [] { return false; };
    const auto Start = Progress->GetAttributeRevision();
    TestTrue(TEXT("Negative allocation rejected"), Progress->CommitAttributePoints({-1, 0, 0, 0}, Start, Good) == EEWAttributeResult::InvalidAllocation);
    TestTrue(TEXT("Wrong-sized allocation rejected"), Progress->CommitAttributePoints({1}, Start, Good) == EEWAttributeResult::InvalidAllocation);
    TestTrue(TEXT("Over budget rejected"), Progress->CommitAttributePoints({6, 0, 0, 0}, Start, Good) == EEWAttributeResult::NotEnoughPoints);
    TestTrue(TEXT("Failed allocation save rolls back"), Progress->CommitAttributePoints({2, 1, 0, 0}, Start, Bad) == EEWAttributeResult::SaveFailed);
    TestEqual(TEXT("No points lost on failed save"), Progress->GetUnspentPoints(), 5);
    TestTrue(TEXT("Batch commits"), Progress->CommitAttributePoints({2, 1, 0, 0}, Start, Good) == EEWAttributeResult::Success);
    TestEqual(TEXT("Exact budget consumed"), Progress->GetUnspentPoints(), 2);
    TestTrue(TEXT("Repeated confirmation rejected"), Progress->CommitAttributePoints({2, 1, 0, 0}, Start, Good) == EEWAttributeResult::Stale);
    const auto BeforeReset = Progress->GetAttributeRevision();
    Wallet->SetCopper(74999);
    TestTrue(TEXT("One copper short cannot reset"), Progress->ResetAttributePoints(BeforeReset, Good) == EEWAttributeResult::NotEnoughGold);
    Wallet->SetCopper(75001);
    Survival->ApplyDamage(35.f);
    Survival->UpdateStamina(true, 1.f);
    const float Health = Survival->GetHealth();
    const float Stamina = Survival->GetStamina();
    TestTrue(TEXT("Failed reset save rolls back"), Progress->ResetAttributePoints(BeforeReset, Bad) == EEWAttributeResult::SaveFailed);
    TestEqual(TEXT("Failed reset refunds exact purse"), Wallet->GetCopper(), int64(75001));
    TestEqual(TEXT("Failed reset restores invested health points"), Progress->GetStatPoints(EEWStat::Vitality), 2);
    TestEqual(TEXT("Failed reset preserves current health"), Survival->GetHealth(), Health);
    TestEqual(TEXT("Failed reset preserves current stamina"), Survival->GetStamina(), Stamina);
    TestTrue(TEXT("Reset succeeds"), Progress->ResetAttributePoints(BeforeReset, Good) == EEWAttributeResult::Success);
    TestEqual(TEXT("Exactly five gold charged"), Wallet->GetCopper(), int64(1));
    TestEqual(TEXT("Committed points refunded"), Progress->GetUnspentPoints(), 5);
    TestEqual(TEXT("Health investment cleared"), Progress->GetStatPoints(EEWStat::Vitality), 0);
    TestEqual(TEXT("Skill points preserved"), Progress->GetSkillPoints(), SkillPoints);
    TestTrue(TEXT("Unlocked skills preserved"), Progress->GetUnlockedSkills() == Skills);
    TestEqual(TEXT("Level preserved"), Progress->GetLevel(), 6);
    TestEqual(TEXT("Experience preserved"), Progress->GetExperience(), 25);
    TestTrue(TEXT("Reset replay rejected"), Progress->ResetAttributePoints(BeforeReset, Good) == EEWAttributeResult::Stale);
    TestTrue(TEXT("Empty reset rejected without charge"), Progress->ResetAttributePoints(Progress->GetAttributeRevision(), Good) == EEWAttributeResult::NothingToReset);
    Owner->SetRole(ROLE_SimulatedProxy);
    TestTrue(TEXT("Client cannot commit directly"), Progress->CommitAttributePoints({1, 0, 0, 0}, Progress->GetAttributeRevision(), Good) == EEWAttributeResult::NotAuthority);
    return true;
}
#endif
