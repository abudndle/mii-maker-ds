#ifndef MDS_EXCHANGE_H
#define MDS_EXCHANGE_H
#include "mii_codec.h"
#define MDS_IMPORT_FILES 100
#define MDS_IMPORT_FILENAME 96
typedef struct {
 char directory[96],files[MDS_IMPORT_FILES][MDS_IMPORT_FILENAME];
 unsigned count,selected;
 int valid,truncated;
 MdsMiiRecord record;
 const char *status;
} MdsImport;
void mds_import_reset(MdsImport *);
int mds_import_scan(MdsImport *,const char *);
int mds_import_select(MdsImport *,unsigned);
int mds_import_step(MdsImport *,int);
#endif
