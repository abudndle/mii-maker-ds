#include "status.h"
MdsStatus mds_status(const MdsAvatar*a)
{
 if(a->value[61]&MDS_SPECIAL)return MDS_STATUS_SPECIAL;
 if(a->value[51])return MDS_STATUS_PERSONAL;
 if(a->value[61]&MDS_RECEIVED)return MDS_STATUS_RECEIVED;
 if(a->value[46])return MDS_STATUS_FAVORITE;
 return MDS_STATUS_NORMAL;
}
const uint8_t*mds_pants_color(const MdsAvatar*a)
{
 /* Software material tints; exact original shader response remains pending. */
 static const uint8_t colors[5][3]={{64,64,64},{190,24,24},{190,24,24},{32,70,180},{224,176,32}};
 return colors[mds_status(a)];
}
