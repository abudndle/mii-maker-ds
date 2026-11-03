#ifndef MDS_CAMERA_HOST_NDS_H
#define MDS_CAMERA_HOST_NDS_H
#include <stddef.h>
#include <stdint.h>
typedef enum {CAMERA_INNER=0,CAMERA_OUTER=1} CameraDevice;
#define MCUREG_APT_SEQ_CMD_PREVIEW 3
extern uint32_t mock_ndma_cr[1];
#define REG_NDMA_CR(channel) (mock_ndma_cr[(channel)])
int isDSiMode(void);
int cameraInit(void);
void cameraDeinit(void);
int cameraSelect(CameraDevice selected);
void cameraStopTransfer(void);
int ndmaBusy(int channel);
int cameraTransferActive(void);
int cameraStartTransfer(void *dest,int command,int channel);
void DC_InvalidateRange(void *address,size_t len);
#endif
