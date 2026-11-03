#ifndef MDS_FACE_HINT_H
#define MDS_FACE_HINT_H
#include <stdint.h>
/* Experimental eye-pair contrast cue, NOT face detection or recognition.
 * Two appropriately spaced dark patches can be scenery or other objects:
 * both false positives and negatives are expected on real photos. */
typedef enum {
 MDS_FACE_HINT_INVALID=0,
 MDS_FACE_HINT_NO_PAIR=1,
 MDS_FACE_HINT_POSSIBLE_PAIR=2
} MdsFaceHint;
/* Candidate centers are pixel coordinates, not reliable facial landmarks.
 * contrast is an uncalibrated integer, not a recognition confidence. */
typedef struct {
 unsigned left_x,right_x,eye_y,contrast;
} MdsEyePair;
/* On INVALID and NO_PAIR, leaves *out unchanged. Null out is INVALID. */
MdsFaceHint mds_eye_pair_locate_rgb555(const uint16_t *frame,
                                      unsigned width,unsigned height,
                                      MdsEyePair *out);
/* Legacy classification API preserved for camera diagnostics and tests. */
MdsFaceHint mds_face_hint_rgb555(const uint16_t *frame,
                                unsigned width,unsigned height);
#endif
