#ifndef MDS_HEAD_H
#define MDS_HEAD_H
#include "avatar.h"
#include "cfl_resource.h"
#define MDS_HEAD_SIDE 128
/* Portable original-resource software preview; RGB555+A1 output, transparent background. */
/* Reset if the caller modifies/reuses the backing CFL archive bytes. */
void mds_render_reset_cache(void);
void mds_render_set_abort(int (*)(void));
int mds_mii_render(const MdsCflArchive *,const MdsAvatar *,const void *,size_t,uint16_t *,int);
/* Camera yaw is a 0..23 circular 15-degree step; angle 0 is front. */
int mds_mii_render_view(const MdsCflArchive *,const MdsAvatar *,const void *,size_t,uint16_t *,int,unsigned);
int mds_head_render_view(const MdsCflArchive *,const MdsAvatar *,uint16_t *,unsigned);
int mds_head_render(const MdsCflArchive *,const MdsAvatar *,uint16_t *);
#endif
