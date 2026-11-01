#include "saved_select.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
 MdsGallery g;
 memset(&g,0,sizeof g);
 assert(mds_saved_first(&g)==-1);
 assert(mds_saved_next(&g,-1,1)==-1);
 assert(mds_saved_count(&g)==0);
 g.used[3]=g.used[17]=g.used[99]=1;
 assert(mds_saved_count(&g)==3);
 assert(mds_saved_first(&g)==3);
 assert(mds_saved_next(&g,3,1)==17);
 assert(mds_saved_next(&g,17,1)==99);
 assert(mds_saved_next(&g,99,1)==3);
 assert(mds_saved_next(&g,3,-1)==99);
 assert(mds_saved_next(&g,-1,-1)==3);
 assert(mds_saved_next(&g,101,1)==3);
 assert(mds_saved_next(&g,17,0)==-1);
 assert(mds_saved_next(NULL,0,1)==-1);
 puts("PASS: native saved-Mii picker traverses 100 cartridge slots and wraps");
 return 0;
}
