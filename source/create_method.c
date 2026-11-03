#include "create_method.h"
MdsCreateChoice mds_create_method_select(int selection,int dsi_enabled)
{
 if(selection==0)return MDS_CREATE_SCRATCH;
 if(selection==1&&dsi_enabled)return MDS_CREATE_PHOTO_PREVIEW;
 return MDS_CREATE_NONE;
}
MdsCreateChoice mds_create_method_touch(int x,int y,int dsi_enabled)
{
 if(x<20||x>=236)return MDS_CREATE_NONE;
 if(y>=48&&y<100)return MDS_CREATE_SCRATCH;
 if(y>=110&&y<162)return dsi_enabled?
    MDS_CREATE_PHOTO_PREVIEW:MDS_CREATE_NONE;
 return MDS_CREATE_NONE;
}
