#include "clan_dialog.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static void clocks(void)
{
 assert(mds_clan_dialog_active(100,100));
 assert(mds_clan_dialog_active(139,100));
 assert(!mds_clan_dialog_active(140,100));
 assert(mds_clan_dialog_y(100,100)==-192);
 assert(mds_clan_dialog_y(134,100)==2);
 assert(mds_clan_dialog_y(140,100)==0);
 assert(mds_clan_dialog_active(0,UINT32_MAX-1));
 assert(mds_clan_dialog_y(0,UINT32_MAX-1)<0);
 assert(!mds_clan_dialog_active(41,UINT32_MAX-1));
}
static void frame_safety(void)
{
 enum {N=256*192};
 static uint16_t buffer[N+2];
 buffer[0]=0x1234;buffer[N+1]=0x5678;
 uint16_t *img=buffer+1;
 for(int y=0;y<192;y++)for(int x=0;x<256;x++)img[y*256+x]=(uint16_t)(0x8000|y);
 mds_clan_dialog_translate(img,-2,0xffff);
 assert(img[0]==(0x8000|2));
 assert(img[189*256]==(0x8000|191));
 assert(img[190*256]==0xffff&&img[191*256]==0xffff);
 assert(buffer[0]==0x1234&&buffer[N+1]==0x5678);
 for(int y=0;y<192;y++)for(int x=0;x<256;x++)img[y*256+x]=(uint16_t)(0x8000|y);
 mds_clan_dialog_translate(img,2,0x8000);
 assert(img[0]==0x8000&&img[256]==0x8000);
 assert(img[2*256]==0x8000);
 assert(img[3*256]==(0x8000|1));
 for(int n=-10000;n<10000;n+=143)mds_clan_dialog_translate(img,n,0x8000);
 assert(buffer[0]==0x1234&&buffer[N+1]==0x5678);
 mds_clan_dialog_translate(NULL,-192,0);
}
int main(void)
{
 clocks();frame_safety();
 puts("PASS: source CLAN dialog motion, DS scale, VBlank wrap, RGB555 clipping");
 return 0;
}
