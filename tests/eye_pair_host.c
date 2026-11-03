#include "face_hint.h"
#include <assert.h>
#include <stdint.h>
static uint16_t image[256*192];
static uint16_t grey(unsigned v){return (uint16_t)(v|(v<<5)|(v<<10));}
static void reset(void){for(unsigned i=0;i<256u*192u;i++)image[i]=grey(21);}
static void eye(unsigned x,unsigned y,unsigned w,unsigned h)
{
    for(unsigned iy=y;iy<y+h;iy++)
        for(unsigned ix=x;ix<x+w;ix++)image[iy*256u+ix]=grey(8);
}
static void check(unsigned x1,unsigned x2,unsigned y)
{
    MdsEyePair pair={0};
    assert(mds_eye_pair_locate_rgb555(image,256,192,&pair)==MDS_FACE_HINT_POSSIBLE_PAIR);
    assert(pair.left_x>x1-15&&pair.left_x<x1+15);
    assert(pair.right_x>x2-15&&pair.right_x<x2+15);
    assert(pair.eye_y>y-15&&pair.eye_y<y+15);
    assert(pair.right_x-pair.left_x>=55&&pair.right_x-pair.left_x<=120);
    assert(pair.contrast>=20);
}
int main(void)
{
    MdsEyePair out={4,5,6,7};
    assert(mds_eye_pair_locate_rgb555(0,256,192,&out)==MDS_FACE_HINT_INVALID);
    assert(mds_eye_pair_locate_rgb555(image,255,192,&out)==MDS_FACE_HINT_INVALID);
    assert(mds_eye_pair_locate_rgb555(image,256,192,0)==MDS_FACE_HINT_INVALID);
    assert(out.left_x==4&&out.right_x==5);
    reset();
    assert(mds_eye_pair_locate_rgb555(image,256,192,&out)==MDS_FACE_HINT_NO_PAIR);
    assert(out.left_x==4);
    reset();eye(78,64,22,22);eye(156,64,22,22);check(89,167,75);
    reset();eye(68,70,22,22);eye(172,70,22,22);check(79,183,81);
    reset();eye(78,64,22,22);
    assert(mds_eye_pair_locate_rgb555(image,256,192,&out)==MDS_FACE_HINT_NO_PAIR);
    reset();eye(68,64,22,22);eye(172,64,22,22);
    for(unsigned i=0;i<256u*192u;i++)image[i]|=0x8000;
    check(79,183,75);
    reset();
    for(unsigned y=64;y<86;y++)
        for(unsigned x=48;x<208;x++)image[y*256u+x]=grey(8);
    assert(mds_eye_pair_locate_rgb555(image,256,192,&out)==MDS_FACE_HINT_NO_PAIR);
    return 0;
}
