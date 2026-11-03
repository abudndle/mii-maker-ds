#include "photo_quality.h"
#include <stddef.h>
MdsPhotoQuality mds_photo_quality_rgb555(const uint16_t *frame,
                                          unsigned width, unsigned height)
{
    if(!frame || width!=256u || height!=192u)return MDS_PHOTO_INVALID;
    /* Sampling the central preview area limits the impact of dark borders.
     * RGB555 channel order follows BlocksDS RGB15: r in low 5 bits. */
    unsigned total=0, squared=0, count=0;
    for(unsigned y=24;y<168;y+=4)
        for(unsigned x=32;x<224;x+=4){
            unsigned p=frame[y*256u+x];
            unsigned r=p&31u,g=(p>>5)&31u,b=(p>>10)&31u;
            unsigned luma=(3u*r+6u*g+b+5u)/10u;
            total+=luma;squared+=luma*luma;count++;
        }
    if(!count)return MDS_PHOTO_INVALID;
    unsigned mean=total/count;
    if(mean<6u)return MDS_PHOTO_TOO_DARK;
    if(mean>27u)return MDS_PHOTO_TOO_BRIGHT;
    /* E[X^2]-E[X]^2, computed without floating point or overflow. */
    if((uint64_t)squared*count-(uint64_t)total*total<
       (uint64_t)4u*count*count)return MDS_PHOTO_TOO_FLAT;
    return MDS_PHOTO_EXPOSURE_OK;
}
