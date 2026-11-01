#include <assert.h>
#include <stdio.h>
#include "menu.h"

/* A queued release must not mutate a different saved Mii, even if the
 * original balloon becomes transparent or the player changes rooms. */
int main(void)
{
    MdsGalleryActionPress p;
    mds_gallery_action_press_reset(&p);
    assert(p.target_slot==-1);
    assert(mds_gallery_action_press_release_for_slot(&p,30,176,0,1)==MDS_GALLERY_ACTION_NONE);
    mds_gallery_action_press_begin(&p,MDS_GALLERY_ACTION_FAVORITE);
    mds_gallery_action_press_bind_slot(&p,4);
    assert(p.target_slot==4);
    assert(mds_gallery_action_press_release_for_slot(&p,30,176,5,1)==MDS_GALLERY_ACTION_NONE);
    assert(p.pressed==MDS_GALLERY_ACTION_NONE&&p.target_slot==-1);
    mds_gallery_action_press_begin(&p,MDS_GALLERY_ACTION_COPY);
    mds_gallery_action_press_bind_slot(&p,4);
    assert(mds_gallery_action_press_release_for_slot(&p,125,176,4,0)==MDS_GALLERY_ACTION_NONE);
    assert(p.target_slot==-1);
    mds_gallery_action_press_begin(&p,MDS_GALLERY_ACTION_COPY);
    mds_gallery_action_press_bind_slot(&p,4);
    assert(mds_gallery_action_press_release_for_slot(&p,125,176,4,1)==MDS_GALLERY_ACTION_COPY);
    assert(p.target_slot==-1);
    mds_gallery_action_press_begin(&p,MDS_GALLERY_ACTION_EDIT);
    mds_gallery_action_press_bind_slot(&p,99);
    assert(mds_gallery_action_press_release_for_slot(&p,206,176,99,1)==MDS_GALLERY_ACTION_EDIT);
    mds_gallery_action_press_begin(&p,MDS_GALLERY_ACTION_FAVORITE);
    mds_gallery_action_press_bind_slot(&p,100);
    assert(mds_gallery_action_press_release_for_slot(&p,30,176,100,1)==MDS_GALLERY_ACTION_NONE);
    assert(mds_gallery_action_press_release_for_slot(NULL,30,176,4,1)==MDS_GALLERY_ACTION_NONE);
    puts("PASS: gallery action releases are bound to the original slot and visible artwork");
    return 0;
}
