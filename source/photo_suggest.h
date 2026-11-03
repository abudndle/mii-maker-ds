#ifndef MDS_PHOTO_SUGGEST_H
#define MDS_PHOTO_SUGGEST_H
#include "avatar.h"
/* Experimental RGB555-to-editor suggestions, NOT validated face detection.
 * A possible eye-pair contrast cue DOES NOT establish a human face.
 * Never saves, never retains photos, and only changes appearance fields. */
typedef enum {
 MDS_PHOTO_SUGGEST_INVALID=0,
 MDS_PHOTO_SUGGEST_BAD_DRAFT,
 MDS_PHOTO_SUGGEST_BAD_QUALITY,
 MDS_PHOTO_SUGGEST_NO_PAIR,
 MDS_PHOTO_SUGGEST_READY
} MdsPhotoSuggestResult;
/* A failed call never changes the caller's three output avatars. */
MdsPhotoSuggestResult mds_photo_suggest_diagnose(
    const uint16_t *frame,unsigned width,unsigned height,
    const MdsAvatar *seed,MdsAvatar out[3]);
/* Compatibility with the existing boolean candidate API. */
int mds_photo_suggest(const uint16_t *frame,unsigned width,unsigned height,
                      const MdsAvatar *seed,MdsAvatar out[3]);
#endif
