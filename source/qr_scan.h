#ifndef MDS_QR_SCAN_H
#define MDS_QR_SCAN_H
#include "mii_codec.h"
/* Portable image decoder; the application camera entry is DSi-only. */
int mds_qr_scan_rgb555(MdsMiiRecord *,const uint16_t *,unsigned,unsigned);
#endif
