#include <nds.h>
#include "camera_ds.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
unsigned mock_ndma_cr[4];
static int dsi=1,init_failure,select_failure=-1,initialized,stops,starts;
static CameraDevice sensor;
int isDSiMode(void){return dsi;}
int cameraInit(void){if(init_failure)return 0;initialized=1;return 1;}
int cameraSelect(CameraDevice selected){if((int)selected==select_failure)return 0;sensor=selected;return 1;}
void cameraDeinit(void){initialized=0;}
void cameraStopTransfer(void){stops++;}
int ndmaBusy(unsigned channel){(void)channel;return 0;}
int cameraTransferActive(void){return 0;}
void DC_InvalidateRange(const void *buffer,size_t size){(void)buffer;(void)size;}
int cameraStartTransfer(uint16_t *frame,int command,unsigned channel)
{
 (void)command;(void)channel;assert(initialized);starts++;
 for(unsigned i=0;i<256*192;i++)frame[i]=sensor==CAMERA_OUTER?0x9234:0x8123;
 return 1;
}
int main(void)
{
 dsi=0;assert(!mds_camera_open());mds_camera_suspend();assert(!mds_camera_resume());
 dsi=1;assert(mds_camera_open()&&sensor==CAMERA_INNER);
 assert(mds_camera_update()&&mds_camera_update());assert(mds_camera_frame()[0]==0x8123);
 assert(mds_camera_switch()&&mds_camera_update()&&mds_camera_update());
 assert(sensor==CAMERA_OUTER&&mds_camera_frame()[0]==0x9234);
 mds_camera_freeze();assert(mds_camera_update());
 int prior_stops=stops,prior_starts=starts;
 mock_ndma_cr[0]=123;mds_camera_suspend();
 assert(!initialized&&stops==prior_stops+1&&mock_ndma_cr[0]==0&&!mds_camera_frame());
 assert(mds_camera_resume()&&initialized&&sensor==CAMERA_OUTER);
 assert(mds_camera_frame()[0]==0x9234&&strstr(mds_camera_status(),"frozen"));
 assert(mds_camera_update()&&starts==prior_starts); /* Frozen view stays frozen. */
 mds_camera_freeze();assert(mds_camera_update()&&starts==prior_starts+1);
 mds_camera_suspend();assert(mds_camera_resume()&&mds_camera_update());
 assert(starts==prior_starts+2&&sensor==CAMERA_OUTER);
 mds_camera_suspend();init_failure=1;assert(!mds_camera_resume()&&!initialized);
 init_failure=0;assert(mds_camera_open());
 assert(mds_camera_switch()&&mds_camera_update());mds_camera_suspend();
 select_failure=CAMERA_OUTER;assert(!mds_camera_resume()&&!initialized&&!mds_camera_frame());
 assert(!strcmp(mds_camera_status(),"Camera resume failed"));select_failure=-1;
 assert(mds_camera_open());mds_camera_suspend();mds_camera_close();
 assert(!mds_camera_resume()&&!initialized);
 puts("PASS: camera suspend stops DMA, resumes sensor/frozen frame, restarts preview, handles failures and honors close; hardware is mocked");
}
