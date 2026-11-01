#include <assert.h>
#include <stdio.h>
#include "menu.h"

/* Actions fire only on release inside the originally pressed button.
 * Sliding across another button, over a Mii, or into an inert gap cancels. */
int main(void)
{
    MdsGalleryActionPress press;
    mds_gallery_action_press_reset(&press);
    assert(mds_gallery_action_press_release(&press,16,175)==MDS_GALLERY_ACTION_NONE);
    const int x[]={16,110,192};
    const MdsGalleryTouchAction actions[]={
        MDS_GALLERY_ACTION_FAVORITE,MDS_GALLERY_ACTION_COPY,MDS_GALLERY_ACTION_EDIT
    };
    for(unsigned i=0;i<3;i++){
        mds_gallery_action_press_begin(&press,actions[i]);
        mds_gallery_action_press_hold(&press,x[i]+1,180);
        assert(mds_gallery_action_press_release(&press,x[i],175)==actions[i]);
        assert(mds_gallery_action_press_release(&press,x[i],175)==MDS_GALLERY_ACTION_NONE);
        mds_gallery_action_press_begin(&press,actions[i]);
        mds_gallery_action_press_hold(&press,128,100); /* Mii grid */
        mds_gallery_action_press_hold(&press,x[i],175); /* no re-arm */
        assert(mds_gallery_action_press_release(&press,x[i],175)==MDS_GALLERY_ACTION_NONE);
        mds_gallery_action_press_begin(&press,actions[i]);
        assert(mds_gallery_action_press_release(&press,x[(i+1)%3],175)==MDS_GALLERY_ACTION_NONE);
        mds_gallery_action_press_begin(&press,actions[i]);
        mds_gallery_action_press_hold(&press,87,175); /* inert gap */
        assert(mds_gallery_action_press_release(&press,x[i],175)==MDS_GALLERY_ACTION_NONE);
        mds_gallery_action_press_begin(&press,actions[i]);
        mds_gallery_action_press_reset(&press); /* scene exit or dialog */
        assert(mds_gallery_action_press_release(&press,x[i],175)==MDS_GALLERY_ACTION_NONE);
    }
    mds_gallery_action_press_begin(&press,MDS_GALLERY_ACTION_NONE);
    assert(mds_gallery_action_press_release(&press,16,175)==MDS_GALLERY_ACTION_NONE);
    mds_gallery_action_press_begin(&press,(MdsGalleryTouchAction)99);
    assert(mds_gallery_action_press_release(&press,16,175)==MDS_GALLERY_ACTION_NONE);
    mds_gallery_action_press_reset(NULL);
    mds_gallery_action_press_begin(NULL,MDS_GALLERY_ACTION_EDIT);
    mds_gallery_action_press_hold(NULL,192,175);
    assert(mds_gallery_action_press_release(NULL,192,175)==MDS_GALLERY_ACTION_NONE);
    puts("PASS: gallery action press/release, cancel, cross-button, and scene isolation");
    return 0;
}
