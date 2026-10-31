#include "menu.h"
#include <assert.h>
#include <stdio.h>
int main(void){assert(mds_home_touch(100,25)==MDS_HOME_VIEW);assert(mds_home_touch(140,80)==MDS_HOME_CREATE);assert(mds_home_touch(100,120)==MDS_HOME_TRANSFER);assert(mds_home_touch(100,155)==MDS_HOME_QR);assert(mds_home_touch(235,25)==MDS_HOME_HELP);assert(!mds_home_touch(-1,10));assert(!mds_home_touch(256,192));assert(mds_gallery_touch(42,70,0)==0);assert(mds_gallery_touch(212,120,9)==99);assert(mds_gallery_touch(42,70,10)==-1);assert(mds_home_focus_step(0,-1)==3&&mds_home_focus_step(3,1)==0);assert(mds_gallery_slot_step(0,0,-1)==9);assert(mds_gallery_slot_step(0,9,1)==0);assert(mds_gallery_slot_step(4,42,1)==43);assert(mds_gallery_slot_step(4,49,1)==40);assert(mds_gallery_slot_step(9,99,1)==90);assert(mds_gallery_slot_step(2,99,1)==21);assert(mds_gallery_slot_step(10,0,1)==-1);assert(mds_gallery_slot_step(0,0,0)==-1);
assert(mds_gallery_page_step(0,4,1)==14);
assert(mds_gallery_page_step(4,47,1)==57);
assert(mds_gallery_page_step(4,47,-1)==37);
assert(mds_gallery_page_step(9,99,1)==9);
assert(mds_gallery_page_step(0,0,-1)==90);
assert(mds_gallery_page_step(7,99,1)==80);
assert(mds_gallery_page_step(10,0,1)==-1);
assert(mds_gallery_page_step(3,35,0)==-1);
MdsGalleryDrag drag={.source=-1};unsigned from=999;
assert(!mds_gallery_drag_begin(NULL,0,0,1));
assert(!mds_gallery_drag_begin(&drag,0,0,0)&&drag.source==-1);
assert(!mds_gallery_drag_begin(&drag,0,10,1));
assert(!mds_gallery_drag_begin(&drag,10,0,1));
assert(mds_gallery_drag_begin(&drag,0,8,1)&&drag.source==8);
assert(mds_gallery_drag_end(&drag,1,16,&from)==16&&from==8);
assert(drag.source==-1);
assert(mds_gallery_drag_end(&drag,1,12,&from)==-1);
assert(mds_gallery_drag_begin(&drag,9,99,1));
assert(mds_gallery_drag_end(&drag,0,3,&from)==3&&from==99);
assert(mds_gallery_drag_begin(&drag,4,47,1));
assert(mds_gallery_drag_end(&drag,4,47,&from)==-1); /* dropping on self */
assert(drag.source==-1);
assert(mds_gallery_drag_begin(&drag,4,47,1));
assert(mds_gallery_drag_end(&drag,5,47,&from)==-1); /* destination wrong page */
assert(mds_gallery_drag_begin(&drag,4,47,1));
assert(mds_gallery_drag_end(&drag,5,-1,&from)==-1); /* outside a slot */
assert(mds_gallery_drag_begin(&drag,4,47,1));
assert(mds_gallery_drag_end(&drag,5,52,NULL)==-1);
assert(drag.source==-1);
assert(mds_gallery_drag_begin(&drag,2,22,1));
mds_gallery_drag_reset(&drag);
assert(mds_gallery_drag_end(&drag,3,34,&from)==-1);
assert(mds_gallery_drag_end(NULL,3,34,&from)==-1);
puts("PASS: original menu, gallery D-pad and cross-page stylus drag move/swap guards");}
