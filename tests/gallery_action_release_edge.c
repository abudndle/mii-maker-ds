#include <assert.h>
#include <stdio.h>
#include "menu.h"

/* A SELECT-up and touch-up may be captured in the same VBlank. Neither
 * an armed touch Edit nor standalone SELECT export may execute together. */
int main(void)
{
    MdsGalleryActionPress press;
    mds_gallery_action_press_reset(&press);
    mds_gallery_action_press_begin(&press,MDS_GALLERY_ACTION_EDIT);
    mds_gallery_action_press_bind_slot(&press,17);
    mds_gallery_action_press_cancel_for_physical(&press,0,0);
    assert(press.pressed==MDS_GALLERY_ACTION_EDIT);
    mds_gallery_action_press_cancel_for_physical(&press,0,1);
    assert(press.pressed==MDS_GALLERY_ACTION_NONE);
    assert(press.target_slot==-1);
    assert(mds_gallery_action_press_release_for_slot(&press,206,176,17,1)==
           MDS_GALLERY_ACTION_NONE);

    mds_gallery_action_press_begin(&press,MDS_GALLERY_ACTION_FAVORITE);
    mds_gallery_action_press_bind_slot(&press,5);
    mds_gallery_action_press_cancel_for_physical(&press,1,0);
    assert(mds_gallery_action_press_release_for_slot(&press,30,176,5,1)==
           MDS_GALLERY_ACTION_NONE);
    mds_gallery_action_press_cancel_for_physical(NULL,1,1);

    /* SELECT (or another physical key) held before touch-down has no
     * edge in the current frame. It must still cancel the touch command. */
    mds_gallery_action_press_begin(&press,MDS_GALLERY_ACTION_COPY);
    mds_gallery_action_press_bind_slot(&press,12);
    mds_gallery_action_press_cancel_for_held(&press,0);
    assert(press.pressed==MDS_GALLERY_ACTION_COPY&&press.target_slot==12);
    mds_gallery_action_press_cancel_for_held(&press,1);
    assert(press.pressed==MDS_GALLERY_ACTION_NONE&&press.target_slot==-1);
    assert(mds_gallery_action_press_release_for_slot(&press,125,176,12,1)==
           MDS_GALLERY_ACTION_NONE);
    mds_gallery_action_press_begin(&press,MDS_GALLERY_ACTION_EDIT);
    mds_gallery_action_press_bind_slot(&press,17);
    mds_gallery_action_press_cancel_for_held(&press,1);
    mds_gallery_action_press_cancel_for_held(&press,0);
    assert(mds_gallery_action_press_release_for_slot(&press,206,176,17,1)==
           MDS_GALLERY_ACTION_NONE); /* cannot re-arm by releasing the key */
    mds_gallery_action_press_cancel_for_held(NULL,1);

    unsigned export_action=MDS_GALLERY_CONTROL_EXPORT;
    assert(mds_gallery_controls_suppress_export_on_touch(export_action,0)==
           MDS_GALLERY_CONTROL_EXPORT);
    assert(mds_gallery_controls_suppress_export_on_touch(export_action,1)==
           MDS_GALLERY_CONTROL_NONE);
    assert(mds_gallery_controls_suppress_export_on_touch(
           MDS_GALLERY_CONTROL_RECALL|MDS_GALLERY_CONTROL_EXPORT,1)==
           MDS_GALLERY_CONTROL_RECALL);
    /* A SELECT-held touch on a box or room tab must consume image export,
     * even if the stylus is lifted before SELECT is released. */
    MdsGalleryControls controls;
    mds_gallery_controls_reset(&controls);
    assert(mds_gallery_controls_step(&controls,0,0,1,1,0)==MDS_GALLERY_CONTROL_NONE);
    mds_gallery_controls_consume_touch(&controls,1);
    mds_gallery_controls_consume_touch(&controls,0);
    assert(controls.select_used==1);
    assert(mds_gallery_controls_step(&controls,0,0,0,0,1)==MDS_GALLERY_CONTROL_NONE);
    /* No touch: standalone SELECT still exports. */
    mds_gallery_controls_reset(&controls);
    assert(mds_gallery_controls_step(&controls,0,0,1,1,0)==MDS_GALLERY_CONTROL_NONE);
    mds_gallery_controls_consume_touch(&controls,0);
    assert(mds_gallery_controls_step(&controls,0,0,0,0,1)==MDS_GALLERY_CONTROL_EXPORT);
    /* Same-frame SELECT-down + stylus-down must also consume export. */
    mds_gallery_controls_reset(&controls);
    mds_gallery_controls_step(&controls,0,0,1,1,0);
    mds_gallery_controls_consume_touch(&controls,1);
    assert(mds_gallery_controls_step(&controls,0,0,0,0,1)==MDS_GALLERY_CONTROL_NONE);
    mds_gallery_controls_consume_touch(NULL,1);
    puts("PASS: physical release cancels balloon presses and touch consumes SELECT export");
    return 0;
}
