#ifndef MDS_PHOTO_CANDIDATE_INPUT_H
#define MDS_PHOTO_CANDIDATE_INPUT_H
/* Provisional five-button touch strip on photo suggestion screen.
 * No actions outside the strip, including the editor feature controls. */
typedef enum {
 MDS_PHOTO_INPUT_NONE=0,
 MDS_PHOTO_INPUT_PREV,
 MDS_PHOTO_INPUT_NEXT,
 MDS_PHOTO_INPUT_USE,
 MDS_PHOTO_INPUT_RETRY,
 MDS_PHOTO_INPUT_CANCEL
} MdsPhotoInput;
MdsPhotoInput mds_photo_candidate_touch(int x,int y);
/* Stylus gestures are transactional: activation occurs on release over the
 * same initial button, and leaving its area permanently disarms the gesture.
 * Call reset when entering/leaving photo suggestions or on physical input. */
typedef struct {
 MdsPhotoInput pressed;
} MdsPhotoTouch;
void mds_photo_touch_reset(MdsPhotoTouch *gesture);
void mds_photo_touch_begin(MdsPhotoTouch *gesture,int x,int y);
void mds_photo_touch_hold(MdsPhotoTouch *gesture,int x,int y);
MdsPhotoInput mds_photo_touch_release(MdsPhotoTouch *gesture,int x,int y);
/* Called once each VBlank, including frames without queued button edges.
 * Returns true only on a release that remained in the original action region
 * throughout every sampled stylus position. No actions are executed here. */
int mds_photo_touch_sample(MdsPhotoTouch *gesture,int down,int held,int up,
                           int x,int y);
#endif
