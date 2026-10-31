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
       (unsigned)destination/10!=page||destination==start)return -1;
    *source=(unsigned)start;
    return destination;
}
int mds_home_focus_step(int current,int delta){int v=(current+delta)%4;return v<0?v+4:v;}
