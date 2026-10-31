#ifndef MDS_UNICODE_H
#define MDS_UNICODE_H
#include "avatar.h"
int mds_name_to_utf16(uint8_t *,const char *);
int mds_name_from_utf16(char *,const uint8_t *);
#endif
