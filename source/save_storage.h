#ifndef MDS_SAVE_STORAGE_H
#define MDS_SAVE_STORAGE_H
#include "save.h"
typedef enum {
 MDS_STORAGE_CLOSED,MDS_STORAGE_NEW,MDS_STORAGE_COMPACT,MDS_STORAGE_LEGACY,
 MDS_STORAGE_UNAVAILABLE,MDS_STORAGE_WRONG_ROM,MDS_STORAGE_READ_ERROR,
 MDS_STORAGE_UNKNOWN,MDS_STORAGE_DAMAGED,MDS_STORAGE_INVALID,
 MDS_STORAGE_WRITE_ERROR,MDS_STORAGE_VERIFY_ERROR
} MdsStorageState;
typedef int (*MdsStorageRead)(void *,unsigned,uint8_t *,size_t);
typedef int (*MdsStorageWrite)(void *,unsigned,const uint8_t *,size_t);
/* Keep one instance in static storage, not on the DS stack. */
typedef struct {
 uint8_t image[MDS_SAVE_SIZE],verify[MDS_BANK_SIZE];
 MdsStorageRead read;MdsStorageWrite write;void *context;
 int ready,compact;MdsStorageState state;
} MdsStorage;
void mds_storage_disable(MdsStorage *,MdsStorageState);
int mds_storage_open(MdsStorage *,MdsGallery *,MdsStorageRead,MdsStorageWrite,void *);
int mds_storage_flush(MdsStorage *,MdsGallery *);
const char *mds_storage_message(MdsStorageState);
#endif
