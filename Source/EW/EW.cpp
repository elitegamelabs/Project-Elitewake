// Copyright Epic Games, Inc. All Rights Reserved.

#include "EW.h"
#include "Modules/ModuleManager.h"

#if WITH_EDITOR
void StartEWSeparateProcessVerification();
void StopEWSeparateProcessVerification();
void StartEWSessionVerification();
void StopEWSessionVerification();
#endif

class FEWGameModule : public FDefaultGameModuleImpl
{
public:
    virtual void StartupModule() override
    {
        FDefaultGameModuleImpl::StartupModule();
#if WITH_EDITOR
        StartEWSeparateProcessVerification();
        StartEWSessionVerification();
#endif
    }
    virtual void ShutdownModule() override
    {
#if WITH_EDITOR
        StopEWSeparateProcessVerification();
        StopEWSessionVerification();
#endif
        FDefaultGameModuleImpl::ShutdownModule();
    }
};
IMPLEMENT_PRIMARY_GAME_MODULE(FEWGameModule, EW, "EW");

DEFINE_LOG_CATEGORY(LogEW)
