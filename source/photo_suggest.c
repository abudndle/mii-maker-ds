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
MdsPhotoSuggestResult mds_photo_suggest_diagnose(const uint16_t *image,unsigned width,unsigned height,
                      const MdsAvatar *seed,MdsAvatar out[3])
{
    if(!image||!seed||!out||width!=256u||height!=192u)
        return MDS_PHOTO_SUGGEST_INVALID;
    if(!mds_valid(seed))return MDS_PHOTO_SUGGEST_BAD_DRAFT;
    if(mds_photo_quality(image,width,height)!=MDS_PHOTO_USABLE)
        return MDS_PHOTO_SUGGEST_BAD_QUALITY;
    MdsEyePair pair;
    if(mds_eye_pair_locate_rgb555(image,width,height,&pair)!=
           MDS_FACE_HINT_POSSIBLE_PAIR)
        return MDS_PHOTO_SUGGEST_NO_PAIR;
    /* Fixed regions, NOT localized skin, hair or facial landmarks.
     * These are experimental appearance alternatives, not recognized Miis. */
    unsigned cheek=patch_luma(image,84,172,109,137);
    unsigned upper=patch_luma(image,80,176,32,56);
    unsigned skin=cheek<9u?4u:cheek<15u?3u:cheek<21u?2u:1u;
    unsigned hair=upper<8u?1u:upper<16u?2u:0u;
    /* Bounded geometric suggestions for existing Mii fields 13/14, based
     * on a possible contrast pair rather than verified eye landmarks. */
    unsigned eye_spacing=(pair.right_x-pair.left_x-55u)*12u/65u;
    unsigned eye_height=(94u-pair.eye_y)*18u/32u;
    /* Stage outputs before write, even if seed aliases the output array. */
    MdsAvatar candidates[3]={*seed,*seed,*seed};
    for(unsigned i=0;i<3u;i++){
        candidates[i].value[1]=(uint8_t)skin;
        candidates[i].value[6]=(uint8_t)hair;
        candidates[i].value[2]=(uint8_t)((seed->value[2]+i)%12u);
        candidates[i].value[5]=(uint8_t)((seed->value[5]+i*7u)%132u);
        int variation=i==0u?0:i==1u?-1:1;
        int spacing=(int)eye_spacing+variation;
        int height=(int)eye_height+variation;
        if(spacing<0)spacing=0;else if(spacing>12)spacing=12;
        if(height<0)height=0;else if(height>18)height=18;
        candidates[i].value[13]=(uint8_t)spacing;
        candidates[i].value[14]=(uint8_t)height;
        if(!mds_valid(&candidates[i]))return MDS_PHOTO_SUGGEST_BAD_DRAFT;
    }
    for(unsigned i=0;i<3u;i++)out[i]=candidates[i];
    return MDS_PHOTO_SUGGEST_READY;
}
int mds_photo_suggest(const uint16_t *frame,unsigned width,unsigned height,
                      const MdsAvatar *seed,MdsAvatar out[3])
{
    return mds_photo_suggest_diagnose(frame,width,height,seed,out)==
           MDS_PHOTO_SUGGEST_READY;
}
