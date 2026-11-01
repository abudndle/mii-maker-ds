/* Host-only camera transport doubles. Never included by the BlocksDS build. */
#ifndef MDS_TEST_NDS_H
#define MDS_TEST_NDS_H
#include <stdint.h>
#include <stddef.h>
typedef enum {CAMERA_INNER,CAMERA_OUTER} CameraDevice;
enum {MCUREG_APT_SEQ_CMD_PREVIEW=1};
extern unsigned mock_ndma_cr[4];
#define REG_NDMA_CR(channel) mock_ndma_cr[channel]
int isDSiMode(void);
int cameraInit(void);
int cameraSelect(CameraDevice);
void cameraDeinit(void);
void cameraStopTransfer(void);
int ndmaBusy(unsigned);
int cameraTransferActive(void);
void DC_InvalidateRange(const void *,size_t);
int cameraStartTransfer(uint16_t *,int,unsigned);
#endif
