#include "camera_action.h"
MdsCameraAction mds_camera_action(unsigned down,int is_qr)
{
 /* Portable key masks from libnds, kept in the caller rather than here. */
 enum {A=1u<<0,B=1u<<1,X=1u<<10};
 if(down&B)return MDS_CAMERA_ACTION_CLOSE;
 if(down&A)return MDS_CAMERA_ACTION_CAPTURE;
 if(!is_qr&&(down&X))return MDS_CAMERA_ACTION_SUGGEST;
 return MDS_CAMERA_ACTION_NONE;
}
