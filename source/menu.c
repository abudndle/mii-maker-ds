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
int mds_home_focus_step(int current,int delta){int v=(current+delta)%4;return v<0?v+4:v;}
