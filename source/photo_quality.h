#ifndef MDS_PHOTO_QUALITY_H
#define MDS_PHOTO_QUALITY_H
#include <stdint.h>
/* Exposure/texture screening only. This is NOT face detection or a Mii mapper.
 * Only accepts the native DSi preview's RGB555 256 x 192 buffer. */
typedef enum {
    MDS_PHOTO_INVALID = 0, MDS_PHOTO_TOO_DARK,
    MDS_PHOTO_TOO_BRIGHT, MDS_PHOTO_TOO_FLAT, MDS_PHOTO_EXPOSURE_OK
} MdsPhotoQuality;
MdsPhotoQuality mds_photo_quality_rgb555(const uint16_t *frame,
                                          unsigned width, unsigned height);
#endif
