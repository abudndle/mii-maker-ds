#include "head.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint16_t pixels[128*128];
static void*load(const char*path,size_t*n){FILE*f=fopen(path,"rb");assert(f);assert(!fseek(f,0,SEEK_END));*n=(size_t)ftell(f);rewind(f);void*p=malloc(*n);assert(p);assert(fread(p,1,*n,f)==*n);fclose(f);return p;}
static unsigned hash(void){unsigned h=2166136261u;for(unsigned i=0;i<128*128;i++)h=(h^pixels[i])*16777619u;return h;}
int main(int argc,char**argv){
 assert(argc>=4);size_t n,m,f;void*bytes=load(argv[1],&n),*male=load(argv[2],&m),*female=load(argv[3],&f);MdsCflArchive a;assert(mds_cfl_open(&a,bytes,n));MdsAvatar v;mds_new(&v);
 assert(mds_mii_render(&a,&v,male,m,pixels,1));unsigned base=hash();
 if(argc>4){FILE*out=fopen(argv[4],"wb");assert(out);fwrite(pixels,2,128*128,out);fclose(out);}
 for(unsigned field=43;field<=45;field++){MdsAvatar altered=v;altered.value[field]=mds_fields[field].maximum;assert(mds_mii_render(&a,&altered,male,m,pixels,1));assert(hash()!=base);}
 v.value[0]=1;assert(mds_mii_render(&a,&v,female,f,pixels,1));assert(hash()!=base);
 assert(mds_mii_render(&a,&v,female,f,pixels,0));assert(hash()!=base);
 assert(!mds_mii_render(&a,&v,male,m-1,pixels,1));
 for(unsigned i=0;i<12;i++){v.value[2]=(uint8_t)i;assert(mds_mii_render(&a,&v,female,f,pixels,1));}
 free(bytes);free(male);free(female);puts("PASS: original posed male/female body, full/portrait framing, live height/build/shirt and malformed body rejection");
}
