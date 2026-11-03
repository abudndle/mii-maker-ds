#include "photo_candidate_input.h"
#include <assert.h>
int main(void)
{
 MdsPhotoTouch g={0};
 assert(mds_photo_touch_release(&g,110,180)==MDS_PHOTO_INPUT_NONE);
 mds_photo_touch_begin(&g,110,180);
 assert(g.pressed==MDS_PHOTO_INPUT_USE);
 mds_photo_touch_hold(&g,115,180);
 assert(mds_photo_touch_release(&g,115,180)==MDS_PHOTO_INPUT_USE);
 assert(mds_photo_touch_release(&g,115,180)==MDS_PHOTO_INPUT_NONE);
 /* Sliding into a different action, then back, must not activate it. */
 mds_photo_touch_begin(&g,110,180);
 mds_photo_touch_hold(&g,157,180);
 mds_photo_touch_hold(&g,110,180);
 assert(mds_photo_touch_release(&g,110,180)==MDS_PHOTO_INPUT_NONE);
 /* Crossing off the action strip disarms without re-arming. */
 mds_photo_touch_begin(&g,160,180);
 mds_photo_touch_hold(&g,160,140);
 assert(mds_photo_touch_release(&g,160,180)==MDS_PHOTO_INPUT_NONE);
 /* Outside-down never arms even if user slides into Use. */
 mds_photo_touch_begin(&g,110,140);
 mds_photo_touch_hold(&g,110,180);
 assert(mds_photo_touch_release(&g,110,180)==MDS_PHOTO_INPUT_NONE);
 /* Physical action can atomically cancel a pending destructive touch. */
 mds_photo_touch_begin(&g,160,180);
 mds_photo_touch_reset(&g);
 assert(mds_photo_touch_release(&g,160,180)==MDS_PHOTO_INPUT_NONE);
 /* A gesture that remains in a non-destructive button may activate. */
 mds_photo_touch_begin(&g,7,180);
 assert(mds_photo_touch_release(&g,7,180)==MDS_PHOTO_INPUT_PREV);
 return 0;
}
