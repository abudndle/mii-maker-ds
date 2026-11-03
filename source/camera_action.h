#ifndef MDS_CAMERA_ACTION_H
#define MDS_CAMERA_ACTION_H
/* Resolve simultaneous camera keys deterministically: B closes, then A
 * captures/retakes/scans, then X may suggest ONLY in inward-photo mode. */
typedef enum {
 MDS_CAMERA_ACTION_NONE=0,
 MDS_CAMERA_ACTION_CLOSE,
 MDS_CAMERA_ACTION_CAPTURE,
 MDS_CAMERA_ACTION_SUGGEST
} MdsCameraAction;
MdsCameraAction mds_camera_action(unsigned down,int is_qr);
#endif
