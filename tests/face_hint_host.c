#include "face_hint.h"
#include <assert.h>
#include <stdint.h>
static uint16_t frame[256*192];
static uint16_t gray(unsigned n){return (uint16_t)(n | (n<<5) | (n<<10));}
static void base(void){for(unsigned i=0;i<256u*192u;i++)frame[i]=gray(21);}
static void eye_box(int cx,int cy)
{
    for(int y=cy-11;y<cy+11;y++)
        for(int x=cx-11;x<cx+11;x++)frame[y*256+x]=gray(8);
}
int main(void)
{
    assert(mds_face_hint_rgb555(0,256,192)==MDS_FACE_HINT_INVALID);
    assert(mds_face_hint_rgb555(frame,255,192)==MDS_FACE_HINT_INVALID);
    assert(mds_face_hint_rgb555(frame,256,191)==MDS_FACE_HINT_INVALID);
    base();
    assert(mds_face_hint_rgb555(frame,256,192)==MDS_FACE_HINT_NO_PAIR);
    base();eye_box(89,75);
    assert(mds_face_hint_rgb555(frame,256,192)==MDS_FACE_HINT_NO_PAIR);
    base();eye_box(167,75);
    assert(mds_face_hint_rgb555(frame,256,192)==MDS_FACE_HINT_NO_PAIR);
    base();eye_box(89,75);eye_box(167,75);
    assert(mds_face_hint_rgb555(frame,256,192)==MDS_FACE_HINT_POSSIBLE_PAIR);
    frame[0]=0xffff;
    assert(mds_face_hint_rgb555(frame,256,192)==MDS_FACE_HINT_POSSIBLE_PAIR);
    /* The RGB555 high bit cannot change the cue. */
    for(unsigned i=0;i<256u*192u;i++)frame[i]|=0x8000;
    assert(mds_face_hint_rgb555(frame,256,192)==MDS_FACE_HINT_POSSIBLE_PAIR);
    return 0;
}
