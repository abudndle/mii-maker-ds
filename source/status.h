#ifndef MDS_STATUS_H
#define MDS_STATUS_H
#include "avatar.h"
#define MDS_RECEIVED 1u
#define MDS_SPECIAL 2u
typedef enum {MDS_STATUS_NORMAL,MDS_STATUS_PERSONAL,MDS_STATUS_FAVORITE,MDS_STATUS_RECEIVED,MDS_STATUS_SPECIAL} MdsStatus;
MdsStatus mds_status(const MdsAvatar *);
const uint8_t *mds_pants_color(const MdsAvatar *);
#endif
