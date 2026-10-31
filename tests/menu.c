#include "menu.h"
#include <assert.h>
#include <stdio.h>
static void navigation(void){
    for(unsigned slot=0;slot<100;slot++){
        unsigned right=mds_gallery_step(slot,1,0),down=mds_gallery_step(slot,0,1);
        assert(right/5==slot/5);
        assert(right%5==(slot%5+1)%5);
        assert(down%5==slot%5);
        assert(down/5==(slot/5+1)%20);
        assert(mds_gallery_step(right,-1,0)==slot);
        assert(mds_gallery_step(down,0,-1)==slot);
        assert(mds_gallery_step(mds_gallery_step(slot,0,2),0,-2)==slot);
        assert(mds_gallery_step(slot,0,2)%10==slot%10);
    }
    assert(mds_gallery_step(0,0,-1)==95);
    assert(mds_gallery_step(99,0,1)==4);
    assert(mds_gallery_step(4,1,0)==0);
    assert(mds_gallery_step(9,0,1)==14);
}
int main(void){navigation();assert(mds_home_touch(100,25)==MDS_HOME_VIEW);assert(mds_home_touch(140,80)==MDS_HOME_CREATE);assert(mds_home_touch(100,120)==MDS_HOME_TRANSFER);assert(mds_home_touch(100,155)==MDS_HOME_QR);assert(mds_home_touch(235,25)==MDS_HOME_HELP);assert(!mds_home_touch(-1,10));assert(!mds_home_touch(256,192));assert(mds_gallery_touch(42,70,0)==0);assert(mds_gallery_touch(212,120,9)==99);assert(mds_gallery_touch(42,70,10)==-1);assert(mds_home_focus_step(0,-1)==3&&mds_home_focus_step(3,1)==0);puts("PASS: original menu hitboxes, action routing, gallery slots, focus wrapping");}
