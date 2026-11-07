#pragma once
#include "CoreMinimal.h"
#include "Engine/Texture2D.h"

/** Small native silhouettes; no external art or runtime file dependency. */
namespace EWHudIcon
{
inline bool Inside(int32 Kind, float X, float Y)
{
    auto Ellipse = [](float X, float Y, float CX, float CY, float RX, float RY)
    { return FMath::Square((X-CX)/RX)+FMath::Square((Y-CY)/RY)<=1.f; };
    if (Kind==10 || Kind==11) return X>.025f && X<.975f && Y>.025f && Y<.975f;
    if (Kind==5) // Hatchet.
        return (X>.43f && X<.54f && Y>.17f && Y<.9f) ||
            (Y>.17f && Y<.39f && X>.32f && X<.8f-(Y-.17f)*.4f);
    if (Kind==6) // Pickaxe.
        return (X>.45f && X<.55f && Y>.24f && Y<.9f) ||
            (X>.1f && X<.9f && FMath::Abs(Y-(.2f+FMath::Square(X-.5f)))<.055f);
    if (Kind==7) // Berry cluster.
        return Ellipse(X,Y,.35f,.55f,.2f,.2f) || Ellipse(X,Y,.65f,.55f,.2f,.2f) ||
            Ellipse(X,Y,.5f,.77f,.18f,.17f) || Ellipse(X,Y,.43f,.22f,.19f,.08f);
    if (Kind==8) // Resource bundle.
        return (X>.22f && X<.73f && Y>.3f && Y<.76f) || Ellipse(X,Y,.73f,.53f,.14f,.23f);
    if (Kind==9) // Headwear.
        return Ellipse(X,Y,.5f,.7f,.4f,.08f) || (X>.3f && X<.7f && Y>.3f && Y<.7f);
    if (Kind==0)
    {
        const float A=(X-.5f)*2.5f, B=(.52f-Y)*2.5f;
        return FMath::Pow(A*A+B*B-.3f,3.f)-A*A*B*B*B<=0.f && Y>.1f && Y<.9f;
    }
    if (Kind==2) // Drumstick and bone.
        return Ellipse(X,Y,.43f,.4f,.29f,.26f) ||
            (FMath::Abs(X-Y)<.085f && Y>.47f && Y<.81f) ||
            Ellipse(X,Y,.74f,.83f,.09f,.09f) || Ellipse(X,Y,.84f,.73f,.09f,.09f);
    if (Kind==3)
        return (X>.4f && X<.6f && Y>.12f && Y<.45f) ||
            (X>.35f && X<.65f && Y>.1f && Y<.18f) ||
            Ellipse(X,Y,.5f,.62f,.3f,.28f);
    if (Kind==4)
        return (Ellipse(X,Y,.5f,.28f,.2f,.17f) && !Ellipse(X,Y,.5f,.28f,.115f,.085f)) ||
            (Y>.37f && Y<.87f && FMath::Abs(X-.5f)<.2f+(Y-.37f)*.25f);
    const FVector2D Points[]={{.57f,.08f},{.23f,.56f},{.46f,.56f},{.37f,.93f},{.8f,.4f},{.55f,.4f}};
    bool Result=false;
    for (int32 I=0,J=5;I<6;J=I++)
        if ((Points[I].Y>Y)!=(Points[J].Y>Y) &&
            X<(Points[J].X-Points[I].X)*(Y-Points[I].Y)/(Points[J].Y-Points[I].Y)+Points[I].X) Result=!Result;
    return Result;
}
inline UTexture2D* Make(int32 Kind, bool Outline)
{
    constexpr int32 Size=96;
    UTexture2D* Texture=UTexture2D::CreateTransient(Size,Size,PF_B8G8R8A8);
    Texture->Filter=TF_Bilinear;
    FColor* Data=static_cast<FColor*>(Texture->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE));
    for(int32 Y=0;Y<Size;++Y) for(int32 X=0;X<Size;++X)
    {
        int32 Coverage=0;
        for(int32 SY=0;SY<2;++SY) for(int32 SX=0;SX<2;++SX)
        {
            const float U=(X+(SX+.5f)/2)/Size,V=(Y+(SY+.5f)/2)/Size,D=(Kind==11 ? 7.f : Kind==10 ? 4.f : 2.f)/Size;
            const bool In=Inside(Kind,U,V);
            const bool Edge=In && (!Inside(Kind,U-D,V)||!Inside(Kind,U+D,V)||!Inside(Kind,U,V-D)||!Inside(Kind,U,V+D));
            if(Outline ? Edge : In) ++Coverage;
        }
        Data[Y*Size+X]=FColor(255,255,255,Coverage*255/4);
    }
    Texture->GetPlatformData()->Mips[0].BulkData.Unlock();Texture->UpdateResource();
    return Texture;
}
}
