/* Exercise real source/camera_ds.c with mocked DSi sensor/NDMA APIs.
 * Synthetic RGB555 only; never relies on proprietary photographs. */
#include <nds.h>
#include "camera_ds.h"
#include <assert.h>
#include <string.h>

uint32_t mock_ndma_cr[1]={1u};
static int dsi=1,init_ok=1,select_ok=1,start_ok=1,busy;
static int selected_sensor=-1,starts,stops,deinits,invalidates;
static uint16_t *dma_ptr;
static int low_exposure;
int isDSiMode(void){return dsi;}
int cameraInit(void){return init_ok;}
void cameraDeinit(void){deinits++;}
int cameraSelect(CameraDevice sensor){selected_sensor=(int)sensor;return select_ok;}
void cameraStopTransfer(void){stops++;}
int ndmaBusy(int channel){assert(channel==0);return busy;}
int cameraTransferActive(void){return busy;}
void DC_InvalidateRange(void *address,size_t length)
{
 assert(address&&length==256u*192u*sizeof(uint16_t));invalidates++;
}
int cameraStartTransfer(void *dest,int command,int channel)
{
 assert(dest&&command==MCUREG_APT_SEQ_CMD_PREVIEW&&channel==0);
 if(!start_ok)return 0;
 starts++;dma_ptr=dest;
 for(unsigned y=0;y<192u;y++)for(unsigned x=0;x<256u;x++){
  unsigned g=low_exposure?0u:((y/8u)%2u?12u:26u);
  dma_ptr[y*256u+x]=(uint16_t)(g|(g<<5u)|(g<<10u));
 }
 return 1;
}
static void closed_and_scrubbed(const uint16_t *snapshot)
{
 assert(!mds_camera_has_frame());
 assert(!mds_camera_photo_frozen());
 assert(mds_camera_frame()==0);
 assert(snapshot&&dma_ptr);
 for(unsigned i=0;i<256u*192u;i++){
  assert(snapshot[i]==0u);
  assert(dma_ptr[i]==0u);
 }
 assert(stops&&deinits);
}
int main(void)
{
 assert(!mds_camera_open_for((MdsCameraPurpose)77));
 dsi=0;
 assert(!mds_camera_open());
 assert(strstr(mds_camera_status(),"DSi"));
 dsi=1;init_ok=0;assert(!mds_camera_open());init_ok=1;
 select_ok=0;int old_deinit=deinits;
 assert(!mds_camera_open());assert(deinits==old_deinit+1);
 select_ok=1;
 assert(mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW));
 assert(selected_sensor==CAMERA_INNER);
 assert(!mds_camera_has_frame());
 mds_camera_freeze();
 assert(!mds_camera_photo_frozen());
 assert(mds_camera_update()); /* DMA start; no completed snapshot yet. */
 assert(starts==1);
 assert(!mds_camera_has_frame());
 assert(mds_camera_update()); /* Copy one finished DMA frame. */
 assert(mds_camera_has_frame());
 const uint16_t *photo=mds_camera_frame();
 assert(photo&&photo[0]);
 mds_camera_freeze();
 assert(mds_camera_photo_frozen());
 assert(strstr(mds_camera_status(),"X suggest"));
 assert(photo[0]);
 mds_camera_close();
 closed_and_scrubbed(photo);

 /* Retake must not make a stale snapshot accessible. */
 assert(mds_camera_open());
 assert(mds_camera_update());
 assert(mds_camera_update());
 photo=mds_camera_frame();
 assert(photo&&photo[0]);
 mds_camera_freeze();assert(mds_camera_photo_frozen());
 mds_camera_freeze();assert(!mds_camera_photo_frozen());
 assert(!mds_camera_has_frame()&&mds_camera_frame()==0);
 /* The pointer from the previous, valid capture is no longer usable, and
  * even a stale pointer must not retain the portrait after retaking. */
 for(unsigned i=0;i<256u*192u;i++)assert(photo[i]==0u);
 for(unsigned i=0;i<256u*192u;i++)assert(dma_ptr[i]==0u);
 assert(mds_camera_update()); /* Start a new transfer after scrubbing. */
 assert(!mds_camera_has_frame());
 assert(mds_camera_update()); /* Fresh photo becomes visible only now. */
 assert(mds_camera_has_frame());
 assert(mds_camera_frame()[0]!=0u);
 mds_camera_close();closed_and_scrubbed(photo);

 /* The rear QR camera cannot freeze or claim photo readiness. */
 assert(mds_camera_open_for(MDS_CAMERA_QR_SCAN));
 assert(selected_sensor==CAMERA_OUTER);
 assert(!mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW));
 assert(mds_camera_update());assert(mds_camera_update());
 photo=mds_camera_frame();assert(photo&&photo[0]);
 mds_camera_freeze();assert(!mds_camera_photo_frozen());
 mds_camera_close();closed_and_scrubbed(photo);

 /* Exposure rejection still leaves the live preview; close scrubs it. */
 low_exposure=1;
 assert(mds_camera_open());assert(mds_camera_update());
 assert(mds_camera_update());
 photo=mds_camera_frame();
 mds_camera_freeze();assert(!mds_camera_photo_frozen());
 assert(strstr(mds_camera_status(),"dark"));
 mds_camera_close();closed_and_scrubbed(photo);
 low_exposure=0;

 /* A failed transfer must close and scrub the last completed snapshot. */
 assert(mds_camera_open());assert(mds_camera_update());
 assert(mds_camera_update());photo=mds_camera_frame();
 start_ok=0;
 assert(!mds_camera_update());
 assert(strstr(mds_camera_status(),"failed"));
 closed_and_scrubbed(photo);start_ok=1;

 /* Timed-out in-flight capture closes without leaving raw DMA behind. */
 assert(mds_camera_open());assert(mds_camera_update());
 const uint16_t *raw=dma_ptr;assert(raw[0]);
 busy=1;
 for(unsigned i=0;i<180u;i++)assert(mds_camera_update());
 assert(!mds_camera_update());
 assert(strstr(mds_camera_status(),"timed out"));
 assert(!mds_camera_has_frame());
 for(unsigned i=0;i<256u*192u;i++)assert(raw[i]==0u);
 busy=0;
 assert(invalidates>0);
 return 0;
}
