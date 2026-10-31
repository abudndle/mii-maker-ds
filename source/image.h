#ifndef MDS_IMAGE_H
#define MDS_IMAGE_H
#include <stdint.h>
#include <stdio.h>
/* Portable RGB555+A1 to uncompressed 24-bit BMP, bottom-up rows. */
int mds_image_bmp(FILE *,const uint16_t *,unsigned,unsigned,uint16_t);
#endif
