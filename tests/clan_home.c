#include "clan_home.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
int main(void)
{
 assert(mds_clan_home_offset(0,100,100)==2);
 assert(mds_clan_home_offset(1,100,100)==2);
 assert(mds_clan_home_offset(2,100,100)==3);
 assert(mds_clan_home_offset(3,100,100)==3);
 for(int i=0;i<4;i++){
  assert(mds_clan_home_offset(i,102,100)==0);
  assert(mds_clan_home_offset(i,103,100)==0);
  assert(mds_clan_home_offset(i,1,UINT32_MAX-1)==0);
 }
 assert(mds_clan_home_offset(-1,100,100)==0);
 assert(mds_clan_home_offset(4,100,100)==0);
 assert(mds_clan_home_running(0,UINT32_MAX-1));
 assert(!mds_clan_home_running(4,UINT32_MAX-1));
 puts("PASS: original home CLPA tracks and VBlank rollover");
 return 0;
}
