#include "clan_home.h"
#include "clan_curve.h"
#define Q(v) ((int32_t)((v)*65536))
/* Original Plaza.arc.files/PlazaTop_Select.bclan, CLPA index=0 target=1.
 * Four top-button pane Y tracks (03, 02, 01, 00) in menu action order. */
static const MdsClanKey top3[]={{Q(0),Q(-75),0},{Q(1),Q(-77),0}};
static const MdsClanKey top2[]={{Q(0),Q(-31),0},{Q(1),Q(-33),0}};
static const MdsClanKey top1[]={{Q(0),Q(24),Q(-3)},{Q(1),Q(21),Q(-3)},{Q(1),Q(21),0}};
static const MdsClanKey top0[]={{Q(0),Q(88),0},{Q(1),Q(85),0}};
int mds_clan_home_running(uint32_t now,uint32_t started)
{
 return (uint32_t)(now-started)<=2;
}
int mds_clan_home_offset(int focus,uint32_t now,uint32_t started)
{
 if(focus<0||focus>3||!mds_clan_home_running(now,started))return 0;
 const MdsClanKey *keys=top3;
 unsigned count=2;
 int32_t end=Q(-77);
 if(focus==1){keys=top2;end=Q(-33);}
 if(focus==2){keys=top1;count=3;end=Q(21);}
 if(focus==3){keys=top0;end=Q(85);}
 int32_t value=mds_clan_curve_eval(keys,count,(int32_t)((now-started)*32768u));
 int64_t diff=(int64_t)value-end;
 if(diff>=0)return (int)((diff+32768)/65536);
 return (int)(-((-diff+32768)/65536));
}
