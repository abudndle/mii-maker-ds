#include "face_hint.h"
#include <stddef.h>
/* Experimental framing cue, NOT face recognition: compare two fixed upper
 * patches against lower patches. It cannot establish that a person exists.
 * The centered 3DS-style portrait framing is an assumption, not a finding. */
static unsigned avg(const uint16_t *p,unsigned left,unsigned right,
                    unsigned top,unsigned bottom)
{
    unsigned sum=0,count=0;
    for(unsigned y=top;y<bottom;y+=4u)
        for(unsigned x=left;x<right;x+=4u){
            unsigned v=p[(size_t)y*256u+x];
            sum+=(3u*(v&31u)+6u*((v>>5)&31u)+((v>>10)&31u))/10u;
            count++;
        }
    return count?sum/count:0;
}
MdsFaceHint mds_face_hint_rgb555(const uint16_t *p,
                                 unsigned width,unsigned height)
{
    if(!p||width!=256u||height!=192u)return MDS_FACE_HINT_INVALID;
    unsigned l=avg(p,68,112,60,92),r=avg(p,145,189,60,92);
    unsigned lc=avg(p,68,112,108,140),rc=avg(p,145,189,108,140);
    if(lc<l+3u||rc<r+3u||
       (l>r?l-r:r-l)>7u)return MDS_FACE_HINT_NO_PAIR;
    return MDS_FACE_HINT_POSSIBLE_PAIR;
}
