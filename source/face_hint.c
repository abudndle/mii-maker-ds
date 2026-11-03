#include "face_hint.h"
#include <stddef.h>

/* Bounded upper-portrait contrast search; not actual eye or face detection.
 * Require BOTH lateral flanks and the lower region to be brighter than the
 * proposed eye region. This rejects broad horizontal dark bands, but does not
 * establish that a human face appears in the photograph. */
static unsigned patch(const uint16_t *p,unsigned x0,unsigned x1,
                      unsigned y0,unsigned y1)
{
    unsigned sum=0,count=0;
    for(unsigned y=y0;y<y1;y+=4u)
        for(unsigned x=x0;x<x1;x+=4u){
            unsigned v=p[(size_t)y*256u+x];
            sum+=(3u*(v&31u)+6u*((v>>5)&31u)+((v>>10)&31u))/10u;
            count++;
        }
    return sum/count; /* All internal rectangles are nonempty. */
}
static unsigned score(const uint16_t *p,unsigned x,unsigned y,
                      unsigned *brightness)
{
    unsigned eye=patch(p,x-10u,x+10u,y-8u,y+8u);
    unsigned lower=patch(p,x-10u,x+10u,y+32u,y+48u);
    unsigned side_left=patch(p,x-34u,x-22u,y-8u,y+8u);
    unsigned side_right=patch(p,x+22u,x+34u,y-8u,y+8u);
    unsigned side=(side_left+side_right)/2u;
    *brightness=eye;
    if(lower<eye+4u||side_left<eye+3u||side_right<eye+3u)return 0;
    return (lower-eye)+(side-eye);
}
MdsFaceHint mds_eye_pair_locate_rgb555(const uint16_t *p,
                unsigned width,unsigned height,MdsEyePair *out)
{
    if(!p||width!=256u||height!=192u||!out)return MDS_FACE_HINT_INVALID;
    unsigned best=0;
    MdsEyePair pair={0,0,0,0};
    /* All samples stay within the 256x192 preview. 4-pixel strides and
     * finite search ranges bound ARM9 work, with no allocations or floats. */
    for(unsigned y=62u;y<=94u;y+=4u){
        for(unsigned x1=72u;x1<=116u;x1+=4u){
            unsigned luma1=0,s1=score(p,x1,y,&luma1);
            if(s1<10u)continue;
            for(unsigned x2=140u;x2<=192u;x2+=4u){
                unsigned distance=x2-x1;
                if(distance<55u||distance>120u)continue;
                unsigned luma2=0,s2=score(p,x2,y,&luma2);
                if(s2<10u||
                   (luma1>luma2?luma1-luma2:luma2-luma1)>7u)continue;
                if(s1+s2>best){
                    best=s1+s2;
                    pair.left_x=x1;
                    pair.right_x=x2;
                    pair.eye_y=y;
                    pair.contrast=best;
                }
            }
        }
    }
    if(!best)return MDS_FACE_HINT_NO_PAIR;
    *out=pair;
    return MDS_FACE_HINT_POSSIBLE_PAIR;
}
MdsFaceHint mds_face_hint_rgb555(const uint16_t *p,
                                 unsigned width,unsigned height)
{
    MdsEyePair ignored;
    return mds_eye_pair_locate_rgb555(p,width,height,&ignored);
}
