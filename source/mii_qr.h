#ifndef MDS_MII_QR_H
#define MDS_MII_QR_H
#include "mii_codec.h"
#include <stdio.h>
#define MDS_QR_PAYLOAD 112
#define MDS_QR_MODULES 57
#define MDS_QR_BUFFER 408
int mds_mii_qr_encrypt(const MdsMiiRecord *,uint8_t [MDS_QR_PAYLOAD]);
int mds_mii_qr_decrypt(MdsMiiRecord *,const uint8_t *,size_t);
int mds_mii_qr_matrix(const uint8_t *,uint8_t [MDS_QR_BUFFER]);
int mds_mii_qr_photo(FILE *,const uint8_t *,const uint16_t *);
#endif
