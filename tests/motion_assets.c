#include "motion.h"
#include "head.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static void*load(const char*path,size_t*size){FILE*f=fopen(path,"rb");assert(f);assert(!fseek(f,0,SEEK_END));*size=(size_t)ftell(f);rewind(f);void*b=malloc(*size);assert(b&&fread(b,1,*size,f)==*size);fclose(f);return b;}
static int coord(const unsigned char*p){uint32_t v=p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;return (int32_t)v;}
int main(int argc,char**argv)
{
 assert(argc==7);MdsMotion motions[2];FILE*files[2];void*base[2];size_t sizes[2];unsigned total=0;
 unsigned char result[56+1440*18],expected[sizeof result];
 for(unsigned gender=0;gender<2;gender++){
  base[gender]=load(argv[1+gender*2],&sizes[gender]);files[gender]=fopen(argv[2+gender*2],"rb");assert(files[gender]&&mds_motion_open(&motions[gender],files[gender]));assert(motions[gender].count==53);
  for(unsigned c=0;c<53;c++)for(unsigned f=0;f<motions[gender].clips[c].count;f++){
   if(!mds_motion_pose(&motions[gender],c,f,base[gender],sizes[gender],result,sizeof result)){fprintf(stderr,"Pose rejected: %u %s %u\n",gender,motions[gender].clips[c].name,f);abort();}
   total++;
  }
 }
 size_t cfl_size;void*cfl_bytes=load(argv[6],&cfl_size);MdsCflArchive cfl;assert(mds_cfl_open(&cfl,cfl_bytes,cfl_size));
 FILE*oracle=fopen(argv[5],"rb");assert(oracle);unsigned records=0,maxcoord=0,maxnormal=0;uint16_t pixels[128*128];
 unsigned h[4];while(fread(h,sizeof h,1,oracle)==1){
  unsigned g=h[0],c=h[1],f=h[2],n=h[3];assert(g<2&&c<53&&n==56+(sizes[g]-56)/12*18&&n<=sizeof result);assert(fread(expected,1,n,oracle)==n);
  assert(mds_motion_pose(&motions[g],c,f,base[g],sizes[g],result,sizeof result));assert(!memcmp(result,expected,56));
  for(unsigned i=56;i<n;i+=18){
   assert(!memcmp(result+i+15,expected+i+15,3));
   for(unsigned k=0;k<3;k++){unsigned e=(unsigned)abs(coord(result+i+k*4)-coord(expected+i+k*4));if(e>maxcoord)maxcoord=e;assert(e<=2);}
   for(unsigned k=12;k<15;k++){unsigned e=(unsigned)abs((int)(int8_t)result[i+k]-(int)(int8_t)expected[i+k]);if(e>maxnormal)maxnormal=e;assert(e<=3);}
  }
  MdsAvatar a;mds_new(&a);a.value[0]=g;assert(mds_mii_render(&cfl,&a,result,n,pixels,1));records++;
 }
 assert(feof(oracle)&&records>=314);fclose(oracle);for(unsigned g=0;g<2;g++){fclose(files[g]);free(base[g]);}free(cfl_bytes);
 printf("PASS: %u original source frames transformed; %u full geometry reference poses/renderings, max position error %u/128, normal error %u/127\n",total,records,maxcoord,maxnormal);
}
