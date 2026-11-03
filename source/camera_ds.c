#include <nds.h>
#include "camera_ds.h"
#include "photo_quality.h"
#include "face_hint.h"
#include "photo_suggest.h"
#include <string.h>
#define CHANNEL 0
static uint16_t frame[256*192] __attribute__((aligned(32)));
static uint16_t display[256*192];
static int active,inflight,frames,have_frame,frozen;
static CameraDevice selected;
static MdsCameraPurpose camera_purpose;
static const char *status="Camera closed";
/* Privacy-sensitive RGB555 frames must be overwritten even if a compiler
 * considers their contents dead after camera shutdown. Unlike memset(),
 * writes through a volatile pointer cannot be removed as dead stores.
 * Only scrub after stopping NDMA, or a transfer could race the overwrite. */
static void scrub_pixels(uint16_t *pixels,size_t count)
{
    volatile uint16_t *p=(volatile uint16_t *)pixels;
    for(size_t i=0;i<count;i++)p[i]=0;
}
static void scrub_captured_frames(void)
{
    scrub_pixels(frame,sizeof frame/sizeof frame[0]);
    scrub_pixels(display,sizeof display/sizeof display[0]);
}
int mds_camera_open_for(MdsCameraPurpose purpose)
{
    if(purpose!=MDS_CAMERA_PHOTO_PREVIEW && purpose!=MDS_CAMERA_QR_SCAN){status="Invalid camera purpose";return 0;}
    if(!isDSiMode()){status="Camera requires DSi mode";return 0;}
    if(active){return camera_purpose==purpose;}
    if(!cameraInit()){status="Camera initialization failed";return 0;}
    camera_purpose=purpose;
    selected=purpose==MDS_CAMERA_QR_SCAN?CAMERA_OUTER:CAMERA_INNER;
    if(!cameraSelect(selected)){cameraDeinit();status="Camera unavailable";return 0;}
    active=1;inflight=0;frames=0;have_frame=0;frozen=0;
    status=purpose==MDS_CAMERA_QR_SCAN?"A scan Mii QR / B back":"A capture / B back";
    return 1;
}
int mds_camera_open(void){return mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW);}
void mds_camera_close(void)
{
    if(!active)return;
    cameraStopTransfer();REG_NDMA_CR(CHANNEL)=0;cameraDeinit();
    /* Never leave a captured portrait or scanned QR frame resident after
     * the sensor is closed. Stop NDMA first; wipe both the DMA destination
     * and the complete display snapshot, including on capture failure. */
    scrub_captured_frames();
    active=0;inflight=0;frames=0;have_frame=0;frozen=0;status="Camera closed";
}
int mds_camera_update(void)
{
    if(!active)return 0;
    if(inflight){
        if(ndmaBusy(CHANNEL)||cameraTransferActive()){
            if(++frames>180){mds_camera_close();status="Camera transfer timed out";return 0;}
            return 1;
        }
        DC_InvalidateRange(frame,sizeof frame);
        memcpy(display,frame,sizeof display);
        inflight=0;have_frame=1;
    }
    if(!frozen){
        DC_InvalidateRange(frame,sizeof frame);
        if(!cameraStartTransfer(frame,MCUREG_APT_SEQ_CMD_PREVIEW,CHANNEL)){
            mds_camera_close();status="Camera capture failed";return 0;
        }
        frames=0;inflight=1;
    }
    return 1;
}
/* The photo camera stays inward-facing; QR scanning stays outward-facing. */
int mds_camera_switch(void){return 0;}
int mds_camera_has_frame(void){return active&&have_frame;}
int mds_camera_photo_frozen(void){return active&&camera_purpose==MDS_CAMERA_PHOTO_PREVIEW&&frozen&&have_frame;}
void mds_camera_freeze(void)
{
    if(!active || camera_purpose!=MDS_CAMERA_PHOTO_PREVIEW)return;
    if(!frozen){
        if(!have_frame){status="Camera warming up. Try again.";return;}
        MdsPhotoQuality quality=mds_photo_quality(display,256u,192u);
        if(quality!=MDS_PHOTO_USABLE){
            status=quality==MDS_PHOTO_TOO_DARK?"Photo too dark. Improve lighting.":
                   quality==MDS_PHOTO_TOO_BRIGHT?"Photo too bright. Reduce glare.":
                   quality==MDS_PHOTO_LOW_CONTRAST?"Photo lacks contrast. Reframe.":
                   "Invalid photo frame.";
            return; /* Keep live preview; do not freeze an unusable photo. */
        }
        /* display holds the last complete frame; stop the in-flight DMA
         * so a later update cannot overwrite the captured snapshot. */
        if(inflight){cameraStopTransfer();REG_NDMA_CR(CHANNEL)=0;inflight=0;}
        frozen=1;
        status="Photo ready. X suggest / A retake";
    }else{
        /* Retake is a privacy boundary: invalidate and wipe the last
         * accepted portrait before starting another transfer. No NDMA
         * transfer is in flight while a frozen snapshot is shown. */
        frozen=0;
        have_frame=0;
        scrub_captured_frames();
        status="A capture / B back";
    }
}
void mds_camera_photo_suggestion_notice(MdsPhotoSuggestResult reason)
{
    if(!mds_camera_photo_frozen())return;
    switch(reason){
      case MDS_PHOTO_SUGGEST_BAD_QUALITY:
        status="Photo quality failed. A retake";break;
      case MDS_PHOTO_SUGGEST_NO_PAIR:
        status="No framing cue. A retake";break;
      case MDS_PHOTO_SUGGEST_BAD_DRAFT:
        status="Mii draft invalid. B back";break;
      case MDS_PHOTO_SUGGEST_INVALID:
        status="Photo data unavailable. A retake";break;
      case MDS_PHOTO_SUGGEST_READY:
        status="Suggestion stage unavailable. B back";break;
    }
}
int mds_camera_check_face_hint(void)
{
    /* Never infer a face from a live DMA buffer, QR scan or unready frame. */
    if(!active||camera_purpose!=MDS_CAMERA_PHOTO_PREVIEW||!frozen||!have_frame){
        status="Capture photo before checking framing";
        return 0;
    }
    MdsFaceHint hint=mds_face_hint_rgb555(display,256u,192u);
    if(hint==MDS_FACE_HINT_POSSIBLE_PAIR){
        status="Eye-pair cue only. Face recognition unavailable";
        return 1;
    }
    status=hint==MDS_FACE_HINT_NO_PAIR?
        "No eye-pair cue. A retake / B back":"Invalid photo frame";
    return 0;
}
const uint16_t *mds_camera_frame(void){return active&&have_frame?display:NULL;}
const char *mds_camera_status(void){return status;}
