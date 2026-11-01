#ifndef MDS_CONFIRM_MOTION_H
#define MDS_CONFIRM_MOTION_H
#include <stdint.h>

/* Original Dialog.arc DialogBase02_DialogIn (W_Dialog CLPA Y).
 * The existing numeric Hermite curve is used, not a fabricated UI tween.
 * The 3DS source is 320x240; the converted lower screen is 256x192.
 * Real BCLAN binaries and Nintendo artwork remain in private NitroFS. */
#define MDS_CONFIRM_WIDTH 256
#define MDS_CONFIRM_HEIGHT 192
typedef struct {
    uint32_t started;
    uint32_t last_elapsed;
    unsigned begun;
    unsigned completed;
    unsigned exit_requested;
    unsigned exiting;
    unsigned exit_up;
} MdsConfirmMotion;
void mds_confirm_motion_reset(MdsConfirmMotion *motion);
void mds_confirm_motion_begin(MdsConfirmMotion *motion,uint32_t now);
/* A decision queues a source-derived exit, even if the entry is playing.
 * The exit begins only after the original entrance has settled. */
int mds_confirm_motion_request_exit(MdsConfirmMotion *motion,int up);
int mds_confirm_motion_exit_done(const MdsConfirmMotion *motion,uint32_t now);
int mds_confirm_motion_tick(MdsConfirmMotion *motion,uint32_t now);
int mds_confirm_motion_ready(const MdsConfirmMotion *motion,uint32_t now);
int mds_confirm_motion_offset(const MdsConfirmMotion *motion,uint32_t now);
/* Composite the real existing dialog bitmap on the underlying DS scene.
 * Pixel buffers are each MDS_CONFIRM_WIDTH * MDS_CONFIRM_HEIGHT in RGB555.
 * Clip the original source-derived W_Dialog translation at both edges. */
void mds_confirm_motion_composite(uint16_t *dest,const uint16_t *background,
                                  const uint16_t *dialog,int offset_y);
#endif
