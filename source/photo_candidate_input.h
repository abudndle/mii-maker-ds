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
#endif
