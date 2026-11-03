#include <nds.h>
#include "camera_ds.h"
#include <string.h>
#define CHANNEL 0
static uint16_t frame[256*192] __attribute__((aligned(32)));
static uint16_t display[256*192];
static int active,inflight,frames,have_frame,frozen,switch_requested;
static CameraDevice selected;
static MdsCameraPurpose camera_purpose;
static const char *status="Camera closed";
int mds_camera_open_for(MdsCameraPurpose purpose)
{
    if(purpose!=MDS_CAMERA_PHOTO_PREVIEW && purpose!=MDS_CAMERA_QR_SCAN){status="Invalid camera purpose";return 0;}
    if(!isDSiMode()){status="Camera requires DSi mode";return 0;}
    if(active){return camera_purpose==purpose;}
    if(!cameraInit()){status="Camera initialization failed";return 0;}
    camera_purpose=purpose;
    selected=purpose==MDS_CAMERA_QR_SCAN?CAMERA_OUTER:CAMERA_INNER;
    if(!cameraSelect(selected)){cameraDeinit();status="Camera unavailable";return 0;}
    active=1;inflight=0;frames=0;have_frame=0;frozen=0;switch_requested=0;
    status=purpose==MDS_CAMERA_QR_SCAN?"A scan Mii QR / B back":"A freeze / B back";
    return 1;
}
int mds_camera_open(void){return mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW);}
void mds_camera_close(void)
{
    if(!active)return;
    cameraStopTransfer();REG_NDMA_CR(CHANNEL)=0;cameraDeinit();
    active=0;inflight=0;have_frame=0;status="Camera closed";
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
    if(switch_requested && camera_purpose==MDS_CAMERA_PHOTO_PREVIEW){
        CameraDevice next=selected==CAMERA_INNER?CAMERA_OUTER:CAMERA_INNER;
        if(!cameraSelect(next)){status="Camera switch failed";return 1;}
        selected=next;frozen=0;have_frame=0;switch_requested=0;
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
int mds_camera_switch(void)
{
    if(!active || camera_purpose==MDS_CAMERA_QR_SCAN)return 0;
    switch_requested=1;
    return 1;
}
void mds_camera_freeze(void){if(active){frozen=!frozen;status=frozen?"Preview frozen. A resume":"A freeze / B back";}}
const uint16_t *mds_camera_frame(void){return active&&have_frame?display:NULL;}
const char *mds_camera_status(void){return status;}
