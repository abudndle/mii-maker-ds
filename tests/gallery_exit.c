#include <assert.h>
#include <stdio.h>
#include "menu.h"

/* Back must cancel both an active Mii drag and an armed balloon tap.
 * SELECT release must not export after leaving and reentering Gallery. */
int main(void)
{
    MdsGalleryDrag drag;
    MdsGalleryControls controls;
    MdsGalleryActionPress press;
    int arrow_latch=1;

    mds_gallery_drag_reset(&drag);
    mds_gallery_controls_reset(&controls);
    mds_gallery_action_press_reset(&press);
    assert(mds_gallery_drag_begin(&drag,0,3,1));
    mds_gallery_controls_step(&controls,0,0,1,1,0);
    mds_gallery_action_press_begin(&press,MDS_GALLERY_ACTION_FAVORITE);
    assert(drag.source==3);
    assert(controls.select_active==1);
    assert(press.pressed==MDS_GALLERY_ACTION_FAVORITE);

    mds_gallery_cancel_for_exit(&drag,&controls,&press,&arrow_latch);
    assert(drag.source==-1);
    assert(arrow_latch==0);
    assert(press.pressed==MDS_GALLERY_ACTION_NONE);
    assert(controls.select_active==0&&controls.select_used==0);
    assert(mds_gallery_action_press_release(&press,16,175)==MDS_GALLERY_ACTION_NONE);
    assert(mds_gallery_controls_step(&controls,0,0,0,0,1)==
           MDS_GALLERY_CONTROL_NONE);
    assert(mds_gallery_drag_end(&drag,0,4,NULL)==-1);

    /* A second Back with no active gesture is harmless, as are null state
     * pointers. Neither may synthesize an action. */
    mds_gallery_cancel_for_exit(&drag,&controls,&press,&arrow_latch);
    mds_gallery_cancel_for_exit(NULL,NULL,NULL,NULL);
    assert(arrow_latch==0);
    assert(mds_gallery_action_press_release(&press,192,175)==
           MDS_GALLERY_ACTION_NONE);
    puts("PASS: gallery Back clears drag, touch, SELECT and arrow state");
    return 0;
}
