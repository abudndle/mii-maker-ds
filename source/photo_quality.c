#include "photo_quality.h"
#include <stddef.h>

/* Deterministic sparse sampling; bounded work for ARM9. RGB555 channels
 * may contain bit 15 from the camera's pixel format; ignore alpha. */
MdsPhotoQuality mds_photo_quality(const uint16_t *pixels,
                                   unsigned width,unsigned height)
{
    if(!pixels || width!=256u || height!=192u)return MDS_PHOTO_INVALID;
    unsigned count=0,low=124u,high=0u;
    unsigned long sum=0;
    for(unsigned y=0;y<height;y+=8u)
        for(unsigned x=0;x<width;x+=8u){
            uint16_t p=pixels[(size_t)y*width+x];
            unsigned r=p&31u,g=(p>>5)&31u,b=(p>>10)&31u;
            unsigned luma=r+2u*g+b; /* 0..124, green-weighted. */
            if(luma<low)low=luma;
            if(luma>high)high=luma;
            sum+=luma;
            count++;
        }
    if(!count)return MDS_PHOTO_INVALID;
    if(sum<count*20ul)return MDS_PHOTO_TOO_DARK;
    if(sum>count*108ul)return MDS_PHOTO_TOO_BRIGHT;
    if(high-low<18u)return MDS_PHOTO_LOW_CONTRAST;
    return MDS_PHOTO_USABLE;
}
