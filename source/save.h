#ifndef MDS_SAVE_H
#define MDS_SAVE_H
#include "avatar.h"
#define MDS_SAVE_SIZE 65536u
#define MDS_BANK_SIZE 32768u
#define MDS_SAVE_BODY (24u+MDS_SLOTS*(MDS_PACKET+1u))
/* ROM save image: 64 KiB, two checksummed generations. */
typedef struct { uint8_t used[MDS_SLOTS];MdsAvatar miis[MDS_SLOTS];uint8_t settings[8];uint32_t generation;int active_bank; } MdsGallery;
void mds_gallery_new(MdsGallery *g);
/* True only for a valid, entirely empty gallery (first-boot setup). */
int mds_gallery_empty(const MdsGallery *g);
int mds_gallery_load(MdsGallery *g,const uint8_t *image,size_t n);
int mds_gallery_commit(MdsGallery *g,uint8_t *image,size_t n);
int mds_gallery_store(MdsGallery *g,unsigned slot,const MdsAvatar *a);
int mds_gallery_delete(MdsGallery *g,unsigned slot);
#endif
