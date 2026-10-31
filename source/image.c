#include "image.h"
#include <string.h>
static void word(uint8_t*p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
int mds_image_bmp(FILE*f,const uint16_t*p,unsigned w,unsigned h,uint16_t background)
{
 if(!f||!p||!w||!h||w>512||h>512)return 0;
 unsigned stride=(w*3+3)&~3u;uint8_t header[54]={0},row[512*3+3];
 header[0]='B';header[1]='M';word(header+2,54+stride*h);word(header+10,54);word(header+14,40);word(header+18,w);word(header+22,h);header[26]=1;header[28]=24;word(header+34,stride*h);
 if(fwrite(header,1,sizeof header,f)!=sizeof header)return 0;
 for(unsigned y=h;y-->0;){
  memset(row,0,stride);
  for(unsigned x=0;x<w;x++){
   unsigned c=p[y*w+x];if(!(c&0x8000))c=background;
   for(unsigned k=0;k<3;k++){unsigned v=(c>>(5*k))&31;row[x*3+2-k]=(uint8_t)((v<<3)|(v>>2));}
  }
  if(fwrite(row,1,stride,f)!=stride)return 0;
 }
 return !ferror(f);
}
