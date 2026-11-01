#include "menu.h"
#include "menu_generated.h"
static int inside(const MdsMenuHit *r,int x,int y){return x>=r->x&&x<r->x+r->w&&y>=r->y&&y<r->y+r->h;}
int mds_home_touch(int x,int y)
{
    for(unsigned i=0;i<sizeof home_hits/sizeof home_hits[0];i++)if(inside(&home_hits[i],x,y))return home_hits[i].action;
    return MDS_HOME_NONE;
}
int mds_gallery_touch(int x,int y,unsigned page)
{
    if(page>=10)return -1;
    for(unsigned i=0;i<sizeof gallery_hits/sizeof gallery_hits[0];i++)if(inside(&gallery_hits[i],x,y))return (int)(page*10)+gallery_hits[i].action;
    return -1;
}
/* Bottom-screen accessibility strip: outside the source-derived room tabs,
 * fixed Mii boxes, and side arrows. A later private asset conversion can
 * replace these provisional bounds with transformed SelectBalloonButton panes.
 * Gaps between actions are intentionally inert. */
MdsGalleryTouchAction mds_gallery_action_touch(int x,int y)
{
 if(y<168||y>=191||x<8||x>=248)return MDS_GALLERY_ACTION_NONE;
 if(x<84)return MDS_GALLERY_ACTION_FAVORITE;
 if(x>=90&&x<166)return MDS_GALLERY_ACTION_COPY;
 if(x>=172)return MDS_GALLERY_ACTION_EDIT;
 return MDS_GALLERY_ACTION_NONE;
}
void mds_gallery_action_press_reset(MdsGalleryActionPress *gesture)
{
 if(gesture){gesture->pressed=MDS_GALLERY_ACTION_NONE;gesture->target_slot=-1;}
}
void mds_gallery_action_press_begin(MdsGalleryActionPress *gesture,
                                    MdsGalleryTouchAction action)
{
 if(!gesture)return;
 gesture->pressed=(action>=MDS_GALLERY_ACTION_FAVORITE&&
                   action<=MDS_GALLERY_ACTION_EDIT)?
                   action:MDS_GALLERY_ACTION_NONE;
 gesture->target_slot=-1;
}
void mds_gallery_action_press_bind_slot(MdsGalleryActionPress *gesture,unsigned slot)
{
 if(!gesture)return;
 gesture->target_slot=gesture->pressed!=MDS_GALLERY_ACTION_NONE&&slot<100u?
                      (int)slot:-1;
}
void mds_gallery_action_press_hold(MdsGalleryActionPress *gesture,int x,int y)
{
 if(gesture&&gesture->pressed!=MDS_GALLERY_ACTION_NONE&&
    mds_gallery_action_touch(x,y)!=gesture->pressed)
  gesture->pressed=MDS_GALLERY_ACTION_NONE;
}
MdsGalleryTouchAction mds_gallery_action_press_release(
    MdsGalleryActionPress *gesture,int x,int y)
{
 if(!gesture)return MDS_GALLERY_ACTION_NONE;
 MdsGalleryTouchAction action=gesture->pressed;
 mds_gallery_action_press_reset(gesture);
 return action!=MDS_GALLERY_ACTION_NONE&&
        mds_gallery_action_touch(x,y)==action?
        action:MDS_GALLERY_ACTION_NONE;
}
MdsGalleryTouchAction mds_gallery_action_press_release_for_slot(
    MdsGalleryActionPress *gesture,int x,int y,unsigned slot,int visible)
{
 if(!gesture)return MDS_GALLERY_ACTION_NONE;
 if(!visible||slot>=100u||gesture->target_slot!=(int)slot){
  mds_gallery_action_press_reset(gesture);
  return MDS_GALLERY_ACTION_NONE;
 }
 return mds_gallery_action_press_release(gesture,x,y);
}
MdsGalleryBoxAction mds_gallery_box_press(int slot,int occupied)
{
 if(slot<0||slot>=100)return MDS_GALLERY_BOX_NONE;
 return occupied?MDS_GALLERY_BOX_DRAG:MDS_GALLERY_BOX_SELECT;
}
int mds_gallery_room_touch(int x,int y)
{
    for(unsigned i=0;i<sizeof gallery_room_hits/sizeof gallery_room_hits[0];i++)
        if(inside(&gallery_room_hits[i],x,y))return (int)i;
    return -1;
}
int mds_gallery_room_arrow(int x,int y,unsigned page)
{
    /* B_ArrowL/B_ArrowR from EDITSelectBase.bclyt, scaled to DS. */
    if(page>=10||y<59||y>=131)return 0;
    if(x>=0&&x<19)return page>0?-1:0;
    if(x>=237&&x<256)return page<9?1:0;
    return 0;
}
int mds_gallery_slot_step(unsigned page,unsigned selected,int direction)
{
    if(page>=10||!direction)return -1;
    unsigned local=selected/10==page?selected%10:0;
    return (int)(page*10+(unsigned)((int)(local+10)+(direction>0?1:-1))%10);
}
int mds_gallery_page_step(unsigned page,unsigned selected,int direction)
{
    if(page>=10||!direction)return -1;
    unsigned position=selected/10==page?selected%10:0;
    /* Match original visible room-arrow limits: no hidden wrap from
     * the first room back to room ten or from the last to the first. */
    if((direction<0&&page==0)||(direction>0&&page==9))return -1;
    unsigned next_page=direction>0?page+1:page-1;
    return (int)(next_page*10+position);
}
void mds_gallery_drag_reset(MdsGalleryDrag *drag)
{
    if(drag)drag->source=-1;
}
int mds_gallery_drag_begin(MdsGalleryDrag *drag,unsigned page,int source,int occupied)
{
    if(!drag)return 0;
    drag->source=-1;
    if(!occupied||page>=10||source<0||source>=100||
       (unsigned)source/10!=page)return 0;
    drag->source=source;
    return 1;
}
int mds_gallery_drag_end(MdsGalleryDrag *drag,unsigned page,int destination,unsigned *source)
{
    if(!drag)return -1;
    int start=drag->source;
    drag->source=-1;
    if(!source||page>=10||start<0||start>=100||
       destination<0||destination>=100||
       /* Only a box in the currently displayed destination room is a
        * valid drop. A stale/off-page slot must never move a saved Mii. */
       (unsigned)destination/10!=page||destination==start)return -1;
    /* The source belongs to the room where the gesture began; the
     * destination may be on another room after an on-screen page change. */
    *source=(unsigned)start;
    return destination;
}
int mds_gallery_drag_blocks_actions(int was_dragging,int dragging)
{
    return was_dragging!=0||dragging!=0;
}
/* B/Back is a cancellation boundary: no pending drag, stylus button or
 * SELECT chord may be replayed after the gallery has been left. */
void mds_gallery_cancel_for_exit(MdsGalleryDrag *drag,
    MdsGalleryControls *controls,MdsGalleryActionPress *press,int *arrow_latch)
{
    mds_gallery_drag_reset(drag);
    mds_gallery_controls_reset(controls);
    mds_gallery_action_press_reset(press);
    if(arrow_latch)*arrow_latch=0;
}
int mds_gallery_next_saved(const unsigned char *used,unsigned current,int direction)
{
    if(!used||current>=100)return -1;
    unsigned slot=current;
    if(!direction)return used[slot]? (int)slot:-1;
    for(unsigned i=0;i<100;i++){
        slot=(slot+(direction>0?1:99))%100;
        if(used[slot])return (int)slot;
    }
    return -1;
}
int mds_home_focus_step(int current,int delta)
{
    /* Reduce before adding so arbitrary D-pad deltas cannot overflow int. */
    int a=current%4,b=delta%4;
    int v=(a+b)%4;
    return v<0?v+4:v;
}

/* Use the VBlank-captured held state, never the auto-repeat bitmask, to
 * distinguish SELECT+A from an ordinary A press. Defer standalone SELECT
 * export until release: holding SELECT to edit must not export first. */
int mds_gallery_controls_secondary_allowed(unsigned primary_action)
{
 /* A VBlank may carry multiple physical key edges. A primary gallery
  * command wins over destructive secondary actions in that same event. */
 return primary_action==MDS_GALLERY_CONTROL_NONE;
}
void mds_gallery_controls_reset(MdsGalleryControls *controls)
{
 if(controls){controls->select_used=0;controls->select_active=0;}
}
unsigned mds_gallery_controls_step(MdsGalleryControls *controls,
 int a_down,int a_held,int select_down,int select_held,int select_up)
{
 if(!controls)return MDS_GALLERY_CONTROL_NONE;
 if(select_down){
  controls->select_active=1;
  controls->select_used=(unsigned char)(a_held!=0);
 }
 unsigned action=MDS_GALLERY_CONTROL_NONE;
 if(a_down){
  if(select_held){
   controls->select_used=1;
   action|=MDS_GALLERY_CONTROL_EDIT;
  }else action|=MDS_GALLERY_CONTROL_RECALL;
 }
 if(select_up){
  if(controls->select_active&&!controls->select_used&&!a_held&&!a_down)
   action|=MDS_GALLERY_CONTROL_EXPORT;
  controls->select_used=0;
  controls->select_active=0;
 }
 return action;
}
