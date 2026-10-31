#ifndef MDS_THUMBNAIL_H
#define MDS_THUMBNAIL_H
#include "avatar.h"
#include <stddef.h>
#include <stdint.h>
#define MDS_THUMBNAIL_SLOTS 10u
#define MDS_THUMBNAIL_WIDTH 42u
#define MDS_THUMBNAIL_HEIGHT 46u
#define MDS_THUMBNAIL_SOURCE_SIDE 128u
typedef struct {
 uint8_t appearance[MDS_FIELDS];
 uint16_t pixels[MDS_THUMBNAIL_WIDTH*MDS_THUMBNAIL_HEIGHT];
 uint8_t valid;
} MdsThumbnail;
typedef struct {
 unsigned page;
 MdsThumbnail slots[MDS_THUMBNAIL_SLOTS];
} MdsThumbnailCache;
/* Keeps just one DS gallery page in memory (~39 KiB), not all 100 Miis. */
void mds_thumbnail_page(MdsThumbnailCache *,unsigned page);
int mds_thumbnail_matches(const MdsThumbnailCache *,unsigned page,unsigned local,const MdsAvatar *);
int mds_thumbnail_capture(MdsThumbnailCache *,unsigned page,unsigned local,const MdsAvatar *,const uint16_t *head);
int mds_thumbnail_blit(const MdsThumbnailCache *,unsigned page,unsigned local,uint16_t *dest,unsigned width,unsigned height,int x,int y);
#endif
