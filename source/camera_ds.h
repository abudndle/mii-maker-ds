#ifndef CAMERA_DS_H
#define CAMERA_DS_H
#include <stdint.h>
/* Preview capture only. Photo-to-Mii analysis is a separate unfinished stage. */
/* QR scanning always uses the outward sensor; photo preview uses inward. */
typedef enum { MDS_CAMERA_PHOTO_PREVIEW = 0, MDS_CAMERA_QR_SCAN = 1 } MdsCameraPurpose;
int mds_camera_open_for(MdsCameraPurpose purpose);
int mds_camera_open(void); /* Compatibility: inward photo preview. */
void mds_camera_close(void);
int mds_camera_update(void);
int mds_camera_switch(void); /* Legacy API: sensor switching disabled. */
int mds_camera_has_frame(void); /* True only when completed frame exists. */
void mds_camera_freeze(void);
const uint16_t *mds_camera_frame(void);
const char *mds_camera_status(void);
#endif
