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
