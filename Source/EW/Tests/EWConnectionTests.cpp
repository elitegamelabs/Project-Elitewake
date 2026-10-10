#if WITH_DEV_AUTOMATION_TESTS
#include "EWGameInstance.h"
#include "Misc/AutomationTest.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEWPrivateAddressTest,"Elitewake.Multiplayer.PrivateAddress",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FEWPrivateAddressTest::RunTest(const FString& Parameters)
{
    FString Target;
    TestTrue(TEXT("Local default"),UEWGameInstance::NormalizePrivateAddress(TEXT(" localhost "),Target));
    TestEqual(TEXT("Canonical local address"),Target,FString(TEXT("127.0.0.1:7777")));
    for (const FString Address : {TEXT("10.1.2.3:65535"),TEXT("172.16.1.2:1"),TEXT("172.31.0.2"),TEXT("192.168.1.2:7777")})
        TestTrue(TEXT("Private IPv4 accepted"),UEWGameInstance::NormalizePrivateAddress(Address,Target));
    for (const FString Address : {TEXT(""),TEXT("8.8.8.8"),TEXT("172.15.1.2"),TEXT("172.32.1.2"),TEXT("192.169.1.2"),TEXT("0.0.0.0"),
        TEXT("localhost:"),TEXT("127.0.0.1:0"),TEXT("127.0.0.1:65536"),TEXT("127.0.0.1:1.5"),TEXT("127.0.0.1:-1"),
        TEXT("127.0.0.1?listen"),TEXT("/Game/ThirdPerson/Lvl_ThirdPerson"),TEXT("192.168.1.256"),TEXT("127..0.1"),TEXT("[::1]:7777"),TEXT("localhost:7777?game=Other")})
    {
        Target=TEXT("previous"); TestFalse(TEXT("Reject unsupported address/URL"),UEWGameInstance::NormalizePrivateAddress(Address,Target));
        TestTrue(TEXT("Rejected input leaves no target"),Target.IsEmpty());
    }
    return true;
}
#endif
