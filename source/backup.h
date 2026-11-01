#ifndef MDS_BACKUP_H
#define MDS_BACKUP_H
#include "save.h"
typedef enum {MDS_BACKUP_OK,MDS_BACKUP_INVALID,MDS_BACKUP_MEMORY,MDS_BACKUP_PATH,
 MDS_BACKUP_FOLDER,MDS_BACKUP_FULL,MDS_BACKUP_WRITE,MDS_BACKUP_VERIFY} MdsBackupResult;
/* Export a verified MDSC snapshot. Unique files are created exclusively; an
 * error removes only the incomplete file created by this call. */
MdsBackupResult mds_backup_export(const MdsGallery *,const char *directory,char *path,size_t path_size);
const char *mds_backup_message(MdsBackupResult);
#endif
