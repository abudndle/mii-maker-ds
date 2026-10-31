#include "save.h"
#include "save_compact.h"
#include <stdio.h>
#include <assert.h>
static unsigned char image[MDS_SAVE_SIZE+1];
static MdsGallery g;
int main(int argc,char **argv){assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);size_t n=fread(image,1,sizeof image,f);fclose(f);assert(n==MDS_SAVE_SIZE||n==MDS_COMPACT_SIZE);assert((n==MDS_SAVE_SIZE&&mds_gallery_load(&g,image,n))||mds_compact_load(&g,image,MDS_COMPACT_SIZE));assert(g.used[0]&&g.miis[0].value[5]==1);puts("PASS: native emulator EEPROM save loads in portable core with hair style 1");}
