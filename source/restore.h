#ifndef MDS_RESTORE_H
#define MDS_RESTORE_H
#include "editor.h"
#include "save_compact.h"
typedef struct {
 MdsGallery gallery;uint8_t image[MDS_COMPACT_SIZE];char path[128];int prepared;
} MdsRestore;
typedef enum {MDS_RESTORE_OK,MDS_RESTORE_CANCELLED,MDS_RESTORE_INVALID,
 MDS_RESTORE_BLOCKED,MDS_RESTORE_CHANGED,MDS_RESTORE_SAFETY_FAILED,
 MDS_RESTORE_WRITE_FAILED,MDS_RESTORE_MEMORY} MdsRestoreResult;
MdsRestoreResult mds_restore_prepare(MdsRestore *,const char *path);
MdsRestoreResult mds_restore_apply(MdsRestore *,MdsEditor *,int accept,
                                 const char *safety_directory,MdsPersist,void *context);
const char *mds_restore_message(MdsRestoreResult);
#endif
