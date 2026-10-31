#include "clan_curve.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#define Q(x) ((int32_t)((x)*65536))
int main(void)
{
 MdsClanKey linear[]={{Q(0),Q(0),Q(10)},{Q(1),Q(10),Q(10)}};
 assert(mds_clan_curve_eval(linear,2,Q(0))==Q(0));
 assert(mds_clan_curve_eval(linear,2,Q(1)/2)==Q(5));
 assert(mds_clan_curve_eval(linear,2,Q(1))==Q(10));
 assert(mds_clan_curve_eval(linear,2,Q(3))==Q(10));
 MdsClanKey smooth[]={{Q(0),Q(20),Q(0)},{Q(2),Q(40),Q(0)}};
 assert(mds_clan_curve_eval(smooth,2,Q(1))==Q(30));
 MdsClanKey dup[]={{Q(-10),Q(0),0},{Q(1),Q(1),0},{Q(1),Q(2),0},{Q(2),Q(3),0}};
 assert(mds_clan_curve_eval(dup,4,Q(1))==Q(2));
 assert(mds_clan_curve_eval(dup,4,Q(-100))==0);
 MdsClanKey vis[]={{Q(0),0,0},{Q(3),1,0}};
 assert(mds_clan_visibility_eval(vis,2,Q(2))==0);
 assert(mds_clan_visibility_eval(vis,2,Q(3))==1);
 assert(mds_clan_curve_eval(NULL,0,0)==0);
 assert(mds_clan_visibility_eval(NULL,0,0)==0);
 MdsClanKey wide[]={{0,INT32_MAX,0},{Q(2),INT32_MAX,0}};
 assert(mds_clan_curve_eval(wide,2,Q(1))==INT32_MAX);
 puts("PASS: CLAN Hermite, fixed-point linear/smooth, duplicate/negative keys, visibility, endpoints");
 return 0;
}
