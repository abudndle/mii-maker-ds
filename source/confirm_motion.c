#include "confirm_motion.h"
#include "clan_dialog.h"
#include <limits.h>
#include <stddef.h>
#include <string.h>

void mds_confirm_motion_reset(MdsConfirmMotion *motion)
{
    if(motion)memset(motion,0,sizeof(*motion));
}

void mds_confirm_motion_begin(MdsConfirmMotion *motion,uint32_t now)
{
    if(!motion)return;
    motion->begun=1;
    motion->started=now;
    motion->last_elapsed=UINT32_MAX;
    motion->completed=0;
}

int mds_confirm_motion_tick(MdsConfirmMotion *motion,uint32_t now)
{
    if(!motion||!motion->begun)return 0;
    uint32_t elapsed=(uint32_t)(now-motion->started);
    if(elapsed>=MDS_CLAN_DIALOG_VBLANKS){
        if(motion->completed)return 0;
        motion->completed=1;
        motion->last_elapsed=elapsed;
        return 1; /* one final unshifted confirmation frame */
    }
    if(motion->last_elapsed==elapsed)return 0;
    motion->last_elapsed=elapsed;
    return 1;
}

int mds_confirm_motion_ready(const MdsConfirmMotion *motion,uint32_t now)
{
    return motion&&motion->begun&&
           (uint32_t)(now-motion->started)>=MDS_CLAN_DIALOG_VBLANKS;
}

int mds_confirm_motion_offset(const MdsConfirmMotion *motion,uint32_t now)
{
    if(!motion||!motion->begun)return 0;
    if(mds_confirm_motion_ready(motion,now))return 0;
    /* Source DialogBase02_DialogIn W_Dialog CLPA Y, scaled 240->192.
     * This existing curve also serves the original user-profile dialog. */
    return mds_clan_dialog_y(now,motion->started);
}

void mds_confirm_motion_composite(uint16_t *dest,const uint16_t *background,
                                  const uint16_t *dialog,int offset_y)
{
    if(!dest||!background||!dialog)return;
    enum { width=MDS_CONFIRM_WIDTH,height=MDS_CONFIRM_HEIGHT };
    /* In the application the three 256x192 pixel buffers are disjoint.
     * The original gallery is visible behind the moving dialog until it
     * finishes entering; do not fill uncovered areas with a fake color. */
    memcpy(dest,background,(size_t)width*height*sizeof(*dest));
    if(offset_y<=-height||offset_y>=height)return;
    if(offset_y>height)offset_y=height;
    if(offset_y< -height)offset_y= -height;
    int top=offset_y<0?0:offset_y;
    int bottom=offset_y+height;
    if(bottom>height)bottom=height;
    if(bottom<=top)return;
    int source_top=top-offset_y;
    memcpy(dest+(size_t)top*width,
           dialog+(size_t)source_top*width,
           (size_t)(bottom-top)*width*sizeof(*dest));
}
