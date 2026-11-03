#ifndef MDS_PHOTO_SUGGEST_H
#define MDS_PHOTO_SUGGEST_H
#include "avatar.h"
/* Experimental RGB555-to-editor suggestions, NOT validated face detection.
 * A possible eye-pair contrast cue DOES NOT establish a human face.
 * Never saves, never retains photos, and only changes appearance fields. */
int mds_photo_suggest(const uint16_t *frame,unsigned width,unsigned height,
                      const MdsAvatar *seed,MdsAvatar out[3]);
#endif
