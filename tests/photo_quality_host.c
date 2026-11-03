#include "photo_quality.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
static uint16_t pixels[256*192];
static uint16_t grey(unsigned v){return (uint16_t)(v|(v<<5)|(v<<10));}
int main(void)
{
    assert(mds_photo_quality_rgb555(NULL,256,192)==MDS_PHOTO_INVALID);
    assert(mds_photo_quality_rgb555(pixels,255,192)==MDS_PHOTO_INVALID);
    assert(mds_photo_quality_rgb555(pixels,256,191)==MDS_PHOTO_INVALID);
    memset(pixels,0,sizeof pixels);
    assert(mds_photo_quality_rgb555(pixels,256,192)==MDS_PHOTO_TOO_DARK);
    for(unsigned i=0;i<256u*192u;i++)pixels[i]=grey(31);
    assert(mds_photo_quality_rgb555(pixels,256,192)==MDS_PHOTO_TOO_BRIGHT);
    for(unsigned i=0;i<256u*192u;i++)pixels[i]=grey(16);
    assert(mds_photo_quality_rgb555(pixels,256,192)==MDS_PHOTO_TOO_FLAT);
    /* 4x4 luminance blocks in the sampled region create measurable texture. */
    for(unsigned y=0;y<192;y++)for(unsigned x=0;x<256;x++)
        pixels[y*256u+x]=grey((x/8u+y/8u)%2u?23u:9u);
    assert(mds_photo_quality_rgb555(pixels,256,192)==MDS_PHOTO_EXPOSURE_OK);
    return 0;
}
