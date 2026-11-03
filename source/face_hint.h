#ifndef MDS_FACE_HINT_H
#define MDS_FACE_HINT_H
#include <stdint.h>
/* Experimental fixed-framing cue, NOT face detection, recognition, or
 * photo-to-Mii inference. False positives and negatives are expected. */
typedef enum {
 MDS_FACE_HINT_INVALID=0,
 MDS_FACE_HINT_NO_PAIR=1,
 MDS_FACE_HINT_POSSIBLE_PAIR=2
} MdsFaceHint;
MdsFaceHint mds_face_hint_rgb555(const uint16_t *frame,
                                  unsigned width,unsigned height);
#endif
