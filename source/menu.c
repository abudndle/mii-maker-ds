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
unsigned mds_accessory_step(unsigned selected,int horizontal,int vertical)
{
    return ((selected/2+(unsigned)(vertical%2+2))%2)*2+
           (selected%2+(unsigned)(horizontal%2+2))%2;
}
int mds_accessory_field(unsigned selected)
{
    static const int fields[]={30,34,39,35};
    return selected<4?fields[selected]:-1;
}
/* Five columns per row, twenty rows across all ten gallery pages. */
unsigned mds_gallery_step(unsigned slot,int horizontal,int vertical)
{
    slot%=100;
    int column=((int)(slot%5)+horizontal%5+5)%5;
    int row=((int)(slot/5)+vertical%20+20)%20;
    return (unsigned)(row*5+column);
}
