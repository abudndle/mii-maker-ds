#ifndef CAMERA_DS_H
#define CAMERA_DS_H
#include <stdint.h>
/* Preview capture only. Photo-to-Mii analysis is a separate unfinished stage. */
int mds_camera_open(void);
void mds_camera_close(void);
void mds_camera_suspend(void);
int mds_camera_resume(void);
int mds_camera_update(void);
int mds_camera_switch(void);
void mds_camera_freeze(void);
const uint16_t *mds_camera_frame(void);
const char *mds_camera_status(void);
#endif
