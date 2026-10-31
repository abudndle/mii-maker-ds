#ifndef AVATAR_H
#define AVATAR_H
#include <stdint.h>
#include <stddef.h>
#define MDS_SLOTS 100
#define MDS_NAME 32
#define MDS_FIELDS 62
#define MDS_PACKET 134
/* This is a private demake format, not Nintendo Mii serialization. */
typedef struct { char name[MDS_NAME],creator[MDS_NAME]; uint8_t value[MDS_FIELDS]; } MdsAvatar;
typedef struct { const char *name; uint8_t maximum,initial; } MdsField;
extern const MdsField mds_fields[MDS_FIELDS];
void mds_new(MdsAvatar *a);
int mds_valid(const MdsAvatar *a);
void mds_adjust(MdsAvatar *a,unsigned field,int delta);
int mds_encode(const MdsAvatar *a,uint8_t *out,size_t size);
int mds_decode(MdsAvatar *a,const uint8_t *in,size_t size);
int mds_write(const MdsAvatar *a,const char *path);
int mds_read(MdsAvatar *a,const char *path);
/* A backend is unavailable until implemented, even when hardware is capable. */
typedef enum { MDS_DS, MDS_DSI } MdsMode;
typedef enum { MDS_CAMERA, MDS_DS_LINK, MDS_3DS_LINK, MDS_WII_LINK } MdsService;
int mds_service_available(MdsMode mode,MdsService service,unsigned ready_mask);
#endif
