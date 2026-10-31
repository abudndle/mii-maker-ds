#ifndef MDS_MOTION_H
#define MDS_MOTION_H
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#define MDS_MOTION_CLIPS 64
#define MDS_MOTION_BONES 18
#define MDS_MOTION_FRAME_BYTES (48+MDS_MOTION_BONES*48)
typedef struct {char name[24];uint32_t offset,count,loop,fps;} MdsMotionClip;
typedef struct {
 FILE *file;
 unsigned count;
 MdsMotionClip clips[MDS_MOTION_CLIPS];
} MdsMotion;
/* Borrowed FILE, caller retains ownership. Failed open leaves zero state. */
int mds_motion_open(MdsMotion *,FILE *);
int mds_motion_find(const MdsMotion *,const char *);
/* Cycle through all available clips; -1 selects from automatic playback. */
int mds_motion_cycle(const MdsMotion *,int current,int direction);
unsigned mds_motion_frame(const MdsMotionClip *,uint32_t,int *);
/* Emits BOD3 (56 + vertex_count * 18 bytes), preserving original order/IDs. */
int mds_motion_pose(MdsMotion *,unsigned,unsigned,const void *,size_t,void *,size_t);
#endif
