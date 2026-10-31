#ifndef MDS_ANIMATION_H
#define MDS_ANIMATION_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
 const uint8_t *data;
 size_t size,pose_bytes;
 unsigned count,period,step,fps;
} MdsAnimation;
int mds_animation_open(MdsAnimation *,const void *,size_t);
const void *mds_animation_pose(const MdsAnimation *,uint32_t,unsigned *);
#endif
