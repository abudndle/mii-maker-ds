#include "head.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint16_t pixels[128*128];
static unsigned hash(void){unsigned h=2166136261u;for(unsigned i=0;i<128*128;i++)h=(h^pixels[i])*16777619u;return h;}
static void ppm(const char*path){FILE*f=fopen(path,"wb");assert(f);fprintf(f,"P6\n128 128\n255\n");for(unsigned i=0;i<128*128;i++){unsigned c=pixels[i];unsigned char b[3]={230,240,235};if(c)for(unsigned k=0;k<3;k++)b[k]=(unsigned char)(((c>>(k*5))&31)*255/31);fwrite(b,1,3,f);}fclose(f);}
int main(int argc,char**argv){
 assert(argc>=2);FILE*f=fopen(argv[1],"rb");assert(f);assert(!fseek(f,0,SEEK_END));long size=ftell(f);rewind(f);void*bytes=malloc((size_t)size);assert(bytes);assert(fread(bytes,1,(size_t)size,f)==(size_t)size);fclose(f);
 MdsCflArchive a;assert(mds_cfl_open(&a,bytes,(size_t)size));assert(mds_cfl_count(&a,2)==12);assert(mds_cfl_count(&a,5)==264);
 MdsAvatar m;mds_new(&m);assert(mds_head_render(&a,&m,pixels));unsigned baseline=hash();unsigned visible=0;for(unsigned i=0;i<128*128;i++)if(pixels[i])visible++;assert(visible>1500&&visible<15000);
 if(argc>2)ppm(argv[2]);
 for(unsigned i=0;i<132;i++){m.value[5]=(uint8_t)i;assert(mds_head_render(&a,&m,pixels));}
 mds_new(&m);m.value[5]=1;assert(mds_head_render(&a,&m,pixels));assert(hash()!=baseline);
 for(unsigned field=0;field<52;field++){mds_new(&m);m.value[field]=mds_fields[field].maximum;assert(mds_head_render(&a,&m,pixels));}
 for(unsigned i=0;i<12;i++){mds_new(&m);m.value[2]=(uint8_t)i;assert(mds_head_render(&a,&m,pixels));}
 mds_new(&m);m.value[1]=255;assert(!mds_head_render(&a,&m,pixels));assert(!mds_head_render(NULL,&m,pixels));
 /* The full-body renderer must reject malformed per-vertex material/bone
  * metadata before rasterizing a BOD3 body alongside the genuine CFL head. */
 uint8_t body[56+3*18]={0};memcpy(body,"BOD3",4);body[4]=3;
 float identity[12]={1,0,0,0,0,1,0,0,0,0,1,0};memcpy(body+8,identity,sizeof identity);
 for(unsigned i=0;i<3;i++){uint8_t *v=body+56+i*18;int32_t x=(int32_t)(i==1?1200:-1200),y=(int32_t)(i==2?1800:-900);memcpy(v,&x,4);memcpy(v+4,&y,4);v[14]=127;v[15]=0;v[16]=0;}
 mds_new(&m);assert(mds_mii_render(&a,&m,body,sizeof body,pixels,1)==1);
 body[56+15]=2;assert(!mds_mii_render(&a,&m,body,sizeof body,pixels,1));body[56+15]=0;
 body[56+16]=18;assert(!mds_mii_render(&a,&m,body,sizeof body,pixels,1));
 free(bytes);puts("PASS: genuine archive, 132 hairstyles, 12 face meshes, all appearance-field maxima, changed pixels and invalid input");
}
