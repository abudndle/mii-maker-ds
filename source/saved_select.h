#ifndef MDS_SAVED_SELECT_H
#define MDS_SAVED_SELECT_H
#include "save.h"
/* Pick directly from cartridge save data; no SD card or file browser. */
int mds_saved_first(const MdsGallery *);
int mds_saved_next(const MdsGallery *,int current,int direction);
unsigned mds_saved_count(const MdsGallery *);
#endif
