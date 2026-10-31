#include "motion.h"
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
static void word(unsigned char*p,unsigned n){for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(n>>(i*8));}
static FILE*fixture(unsigned char**data,size_t*size)
{
 *size=72+3*MDS_MOTION_FRAME_BYTES;unsigned char*b=calloc(1,*size);assert(b);*data=b;
 memcpy(b,"MSP1",4);word(b+4,1);word(b+8,1);word(b+12,18);word(b+16,MDS_MOTION_FRAME_BYTES);word(b+20,32);word(b+24,(unsigned)*size);
 memcpy(b+32,"Wait00",7);word(b+56,72);word(b+60,3);word(b+64,1);word(b+68,30);
 for(unsigned f=0;f<3;f++){
  float head[12]={1,0,0,0,0,1,0,100,0,0,1,0};memcpy(b+72+f*MDS_MOTION_FRAME_BYTES,head,48);
  for(unsigned bone=0;bone<18;bone++)for(unsigned k=0;k<3;k++)word(b+72+f*MDS_MOTION_FRAME_BYTES+48+bone*48+(k*4+k)*4,65536);
  word(b+72+f*MDS_MOTION_FRAME_BYTES+48+3*4,f*65536);
 }
 FILE*file=tmpfile();assert(file);assert(fwrite(b,1,*size,file)==*size);rewind(file);return file;
}
int main(void)
{
 unsigned char*b;size_t size;FILE*f=fixture(&b,&size);MdsMotion m;assert(mds_motion_open(&m,f));assert(m.count==1&&mds_motion_find(&m,"Wait00")==0&&mds_motion_find(&m,"Other")==-1);
 int ended;assert(mds_motion_frame(&m.clips[0],5,&ended)==2&&!ended);assert(mds_motion_frame(&m.clips[0],6,&ended)==0&&!ended);assert(mds_motion_frame(&m.clips[0],UINT32_MAX,NULL)<3);
 m.clips[0].loop=0;assert(mds_motion_frame(&m.clips[0],6,&ended)==2&&ended);m.clips[0].loop=1;
 unsigned char base[92]={0},out[110];memcpy(base,"BOD2",4);word(base+4,3);
 for(unsigned i=0;i<3;i++){base[56+i*12]=128;base[56+i*12+8]=127;}
 assert(mds_motion_pose(&m,0,2,base,sizeof base,out,sizeof out));assert(out[56]==128&&out[57]==1&&out[70]==127);assert(!memcmp(out+56+15,base+56+9,3));
 assert(!mds_motion_pose(&m,1,0,base,sizeof base,out,sizeof out));assert(!mds_motion_pose(&m,0,3,base,sizeof base,out,sizeof out));assert(!mds_motion_pose(&m,0,0,base,sizeof base,out,109));assert(!mds_motion_pose(&m,0,0,base,sizeof base,base,sizeof base));
 base[66]=18;assert(!mds_motion_pose(&m,0,0,base,sizeof base,out,sizeof out));base[66]=0;
 fclose(f);
 /* Every header/table byte truncated; invalid matrix and non-finite head. */
 for(unsigned n=0;n<72;n++){f=tmpfile();assert(fwrite(b,1,n,f)==n);assert(!mds_motion_open(&m,f));fclose(f);}
 f=tmpfile();b[64]=2;assert(fwrite(b,1,size,f)==size);assert(!mds_motion_open(&m,f));fclose(f);b[64]=1;
 word(b+72,0x7fc00000);f=tmpfile();assert(fwrite(b,1,size,f)==size);assert(mds_motion_open(&m,f));assert(!mds_motion_pose(&m,0,0,base,sizeof base,out,sizeof out));fclose(f);free(b);
 puts("PASS: streamed motion bounds, source-frame clock, looping/one-shot endpoint, rigid original geometry transform and invalid frames");
}
