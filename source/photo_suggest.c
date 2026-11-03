#include "photo_suggest.h"
#include "photo_quality.h"
#include "face_hint.h"

/* Brightness from fixed patches, not measured skin or hair regions.
 * These guesses can be incorrect and must remain editable and optional. */
static unsigned patch_luma(const uint16_t *image,unsigned x0,unsigned x1,
                           unsigned y0,unsigned y1)
{
    unsigned total=0,count=0;
    for(unsigned y=y0;y<y1;y+=4u)
        for(unsigned x=x0;x<x1;x+=4u){
            unsigned p=image[y*256u+x];
            total+=(3u*(p&31u)+6u*((p>>5)&31u)+((p>>10)&31u))/10u;
            count++;
        }
    return count?total/count:0;
}
int mds_photo_suggest(const uint16_t *image,unsigned width,unsigned height,
                      const MdsAvatar *seed,MdsAvatar out[3])
{
    if(!image||!seed||!out||width!=256u||height!=192u||!mds_valid(seed))return 0;
    if(mds_photo_quality(image,width,height)!=MDS_PHOTO_USABLE||
       mds_face_hint_rgb555(image,width,height)!=MDS_FACE_HINT_POSSIBLE_PAIR)
        return 0;
    /* Fixed regions, NOT localized skin, hair or facial landmarks.
     * These are experimental appearance alternatives, not recognized Miis. */
    unsigned cheek=patch_luma(image,84,172,109,137);
    unsigned upper=patch_luma(image,80,176,32,56);
    unsigned skin=cheek<9u?4u:cheek<15u?3u:cheek<21u?2u:1u;
    unsigned hair=upper<8u?1u:upper<16u?2u:0u;
    /* Stage outputs before write, even if seed aliases the output array. */
    MdsAvatar candidates[3]={*seed,*seed,*seed};
    for(unsigned i=0;i<3u;i++){
        candidates[i].value[1]=(uint8_t)skin;
        candidates[i].value[6]=(uint8_t)hair;
        candidates[i].value[2]=(uint8_t)((seed->value[2]+i)%12u);
        candidates[i].value[5]=(uint8_t)((seed->value[5]+i*7u)%132u);
        if(!mds_valid(&candidates[i]))return 0;
    }
    for(unsigned i=0;i<3u;i++)out[i]=candidates[i];
    return 1;
}
