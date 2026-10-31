#ifndef MDS_SAVE_COMPACT_H
#define MDS_SAVE_COMPACT_H
#include "save.h"
#define MDS_COMPACT_SIZE 8192u
/* 100 slots, all 62 fields, original 10-UTF16-unit name/creator limits.
 * Single checksummed snapshot; unlike the legacy 64 KiB format, no second bank. */
int mds_compact_encode(const MdsGallery *,uint8_t *,size_t);
int mds_compact_load(MdsGallery *,const uint8_t *,size_t);
#endif
