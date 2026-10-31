#include "image.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char**argv)
{
 assert(argc==2);uint16_t pixels[]={0x801f,0x83e0,0xfc00,0,0xffff,0x8000};
 FILE*f=fopen(argv[1],"wb");assert(f);assert(mds_image_bmp(f,pixels,3,2,0x83ff));assert(!fclose(f));
 f=tmpfile();assert(f);assert(!mds_image_bmp(f,pixels,0,2,0));assert(!mds_image_bmp(f,pixels,513,2,0));assert(!mds_image_bmp(NULL,pixels,3,2,0));assert(!mds_image_bmp(f,NULL,3,2,0));fclose(f);
 f=fopen("/dev/full","wb");if(f){setbuf(f,NULL);assert(!mds_image_bmp(f,pixels,3,2,0));fclose(f);}
 puts("PASS: BMP validation and write-error reporting");
}
