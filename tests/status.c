#include "status.h"
#include <assert.h>
#include <stdio.h>
int main(void){MdsAvatar m;mds_new(&m);assert(mds_status(&m)==MDS_STATUS_NORMAL);m.value[46]=1;assert(mds_status(&m)==MDS_STATUS_FAVORITE);m.value[61]=1;assert(mds_status(&m)==MDS_STATUS_RECEIVED);m.value[51]=1;assert(mds_status(&m)==MDS_STATUS_PERSONAL);m.value[61]|=2;assert(mds_status(&m)==MDS_STATUS_SPECIAL);puts("PASS: normal/favorite/received/Personal/special status precedence");}
