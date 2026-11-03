#include "photo_candidate_input.h"
MdsPhotoInput mds_photo_candidate_touch(int x,int y)
{
 if(y<164||y>=192||x<0||x>=256)return MDS_PHOTO_INPUT_NONE;
 if(x<48)return MDS_PHOTO_INPUT_PREV;
 if(x<96)return MDS_PHOTO_INPUT_NEXT;
 if(x<144)return MDS_PHOTO_INPUT_USE;
 if(x<192)return MDS_PHOTO_INPUT_RETRY;
 return MDS_PHOTO_INPUT_CANCEL;
}

void mds_photo_touch_reset(MdsPhotoTouch *g)
{
 if(g)g->pressed=MDS_PHOTO_INPUT_NONE;
}
void mds_photo_touch_begin(MdsPhotoTouch *g,int x,int y)
{
 if(g)g->pressed=mds_photo_candidate_touch(x,y);
}
void mds_photo_touch_hold(MdsPhotoTouch *g,int x,int y)
{
 if(g&&g->pressed!=MDS_PHOTO_INPUT_NONE&&
    mds_photo_candidate_touch(x,y)!=g->pressed)
     mds_photo_touch_reset(g);
}
MdsPhotoInput mds_photo_touch_release(MdsPhotoTouch *g,int x,int y)
{
 if(!g)return MDS_PHOTO_INPUT_NONE;
 MdsPhotoInput pressed=g->pressed;
 mds_photo_touch_reset(g);
 return pressed!=MDS_PHOTO_INPUT_NONE&&
        pressed==mds_photo_candidate_touch(x,y)?
        pressed:MDS_PHOTO_INPUT_NONE;
}
