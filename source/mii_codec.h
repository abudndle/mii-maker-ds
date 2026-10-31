#ifndef MDS_MII_CODEC_H
#define MDS_MII_CODEC_H
#include "avatar.h"
#define MDS_CFSD_SIZE 96
/* Raw identity/options remain attached to a decoded exchange record. The compact
 * gallery stores appearance/profile only; it does not preserve this identity. */
typedef struct {MdsAvatar avatar;uint8_t raw[MDS_CFSD_SIZE];} MdsMiiRecord;
uint16_t mds_mii_crc(const uint8_t *,size_t);
int mds_cfs_create(MdsMiiRecord *,const MdsAvatar *,uint32_t,uint64_t);
int mds_cfs_decode(MdsMiiRecord *,const void *,size_t);
int mds_cfs_encode(const MdsMiiRecord *,void *,size_t);
#endif
