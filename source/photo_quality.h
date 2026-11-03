#ifndef MDS_PHOTO_QUALITY_H
#define MDS_PHOTO_QUALITY_H
#include <stdint.h>
/* Input is the completed RGB555 camera frame, not the DMA destination.
 * This is only an exposure/contrast check; it does NOT detect a face. */
typedef enum {
    MDS_PHOTO_INVALID=0,
    MDS_PHOTO_TOO_DARK,
    MDS_PHOTO_TOO_BRIGHT,
    MDS_PHOTO_LOW_CONTRAST,
    MDS_PHOTO_USABLE
} MdsPhotoQuality;
MdsPhotoQuality mds_photo_quality(const uint16_t *rgb555,
                                   unsigned width,unsigned height);
#endif
