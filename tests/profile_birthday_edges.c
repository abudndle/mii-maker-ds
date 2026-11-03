#include "profile.h"
#include <assert.h>
#include <limits.h>
#include <string.h>
int main(void)
{
 MdsAvatar avatar;mds_new(&avatar);
 MdsProfile p;mds_profile_begin(&p);
 p.month=0;p.day=0;
 mds_profile_date_step(&p,0,1);
 assert(p.month==1&&p.day==2);
 assert(mds_profile_date_valid((unsigned)p.month,(unsigned)p.day));
 p.month=-1;p.day=-8;
 mds_profile_date_step(&p,0,-1);
 assert(p.month==1&&p.day==31);
 p.month=13;p.day=999;
 mds_profile_date_step(&p,1,1);
 assert(p.month==2&&p.day==29);
 p.month=2;p.day=30;
 mds_profile_date_step(&p,0,1);
 assert(p.month==2&&p.day==1);
 p.month=2;p.day=29;
 mds_profile_date_step(&p,1,1);
 assert(p.month==3&&p.day==29);
 p.month=12;p.day=31;
 mds_profile_date_step(&p,1,1);
 assert(p.month==1&&p.day==31);
 p.month=1;p.day=1;
 mds_profile_date_step(&p,1,-1);
 assert(p.month==12&&p.day==1);
 p.month=4;p.day=30;
 mds_profile_date_step(&p,0,INT_MIN);
 assert(p.month==4&&p.day==29);
 mds_profile_date_step(&p,0,INT_MAX);
 assert(p.month==4&&p.day==30);
 p.month=2;p.day=31;
 mds_profile_date_step(&p,0,0);
 assert(p.month==2&&p.day==29);
 /* Invalid date should be normalized in the editor only; the avatar
  * must remain unchanged until a validated Done action commits. */
 assert(avatar.value[49]==0&&avatar.value[50]==0);
 p.month=2;p.day=30;p.mode=MDS_PROFILE_BIRTHDAY;
 assert(!mds_profile_done(&p,&avatar));
 assert(avatar.value[49]==0&&avatar.value[50]==0);
 mds_profile_date_step(&p,0,1);
 assert(mds_profile_done(&p,&avatar));
 assert(avatar.value[49]==2&&avatar.value[50]==1);
 mds_profile_date_step(0,0,1);
 return 0;
}
