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
int mds_gallery_room_arrow(int x,int y,unsigned page)
{
    if(page>=10||y<44||y>=144)return 0;
    if(x>=0&&x<20)return page>0?-1:0;
    if(x>=236&&x<256)return page<9?1:0;
    return 0;
}
/* Independent room-selector button in the header, distinct from L/R arrows
 * and the ten Mii destination boxes. */
int mds_gallery_room_button(int x,int y)
{
    return x>=96&&x<160&&y>=4&&y<36;
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
    unsigned next_page=(page+(direction>0?1:9))%10;
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
       destination==start)return -1;
    /* The source belongs to the room where the gesture began; the
     * destination may be on another room after an on-screen page change. */
    *source=(unsigned)start;
    return destination;
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
