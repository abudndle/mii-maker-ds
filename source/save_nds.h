#ifndef SAVE_NDS_H
#define SAVE_NDS_H
#include "save.h"
#include "save_storage.h"
int mds_cart_open(MdsGallery *g);
int mds_cart_flush(MdsGallery *g);
MdsStorageState mds_cart_state(void);
const char *mds_cart_status(void);
#endif
