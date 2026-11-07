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
    // Owner, October 30: friends join over the Internet by public IPv4 or a host name.
    TestTrue(TEXT("Public IPv4 accepted"),UEWGameInstance::NormalizePrivateAddress(TEXT("8.8.8.8"),Target));
    TestEqual(TEXT("Public IPv4 gets the game port"),Target,FString(TEXT("8.8.8.8:7777")));
    TestTrue(TEXT("Host name accepted"),UEWGameInstance::NormalizePrivateAddress(TEXT("My-Host.ddns.net:7777"),Target));
    TestEqual(TEXT("Host name is lower case with its port"),Target,FString(TEXT("my-host.ddns.net:7777")));
    for (const FString Address : {TEXT(""),TEXT("0.0.0.0"),TEXT("224.0.0.1"),TEXT("-bad.example.com"),TEXT("host..name"),TEXT("host_name"),
        TEXT("localhost:"),TEXT("127.0.0.1:0"),TEXT("127.0.0.1:65536"),TEXT("127.0.0.1:1.5"),TEXT("127.0.0.1:-1"),
        TEXT("127.0.0.1?listen"),TEXT("/Game/ThirdPerson/Lvl_ThirdPerson"),TEXT("192.168.1.256"),TEXT("127..0.1"),TEXT("[::1]:7777"),TEXT("localhost:7777?game=Other")})
    {
        Target=TEXT("previous"); TestFalse(TEXT("Reject unsupported address/URL"),UEWGameInstance::NormalizePrivateAddress(Address,Target));
        TestTrue(TEXT("Rejected input leaves no target"),Target.IsEmpty());
    }
    return true;
}
#endif
