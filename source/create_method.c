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

MdsCreateOutcome mds_create_method_input(MdsCreateInput input)
{
 MdsCreateOutcome result={MDS_CREATE_NONE,input.selection};
 if(input.cancel){result.choice=MDS_CREATE_BACK;return result;}
 if(input.touch){
  /* A rejected touch (including a disabled DSi-only photo button)
   * consumes this frame. Never fall through to A or directional input
   * and accidentally choose an unrelated creation method. */
  result.choice=mds_create_method_touch(input.x,input.y,input.dsi_enabled);
  return result;
 }
 if(input.confirm){
  result.choice=mds_create_method_select(input.selection,input.dsi_enabled);
  return result;
 }
 /* Opposite directions cancel one another on each axis. Multiple
  * non-opposing direction keys toggle only once in this two-choice menu. */
 if(input.selection>=0&&input.selection<=1&&
    ((!!input.up!=!!input.down)||(!!input.left!=!!input.right))){
  /* DS and DS Lite expose only Scratch. Never highlight an inert
   * camera entry on hardware without the DSi camera feature. */
  result.selection=input.dsi_enabled?(input.selection^1):0;
 }
 return result;
}
