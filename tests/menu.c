#include "menu.h"
#include <assert.h>
#include <stdio.h>
int main(void){assert(mds_home_touch(100,25)==MDS_HOME_VIEW);assert(mds_home_touch(140,80)==MDS_HOME_CREATE);assert(mds_home_touch(100,120)==MDS_HOME_TRANSFER);assert(mds_home_touch(100,155)==MDS_HOME_QR);assert(mds_home_touch(235,25)==MDS_HOME_HELP);assert(!mds_home_touch(-1,10));assert(!mds_home_touch(256,192));assert(mds_gallery_touch(42,70,0)==0);assert(mds_gallery_touch(212,120,9)==99);assert(mds_gallery_touch(42,70,10)==-1);assert(mds_home_focus_step(0,-1)==3&&mds_home_focus_step(3,1)==0);puts("PASS: original menu hitboxes, action routing, gallery slots, focus wrapping");}
