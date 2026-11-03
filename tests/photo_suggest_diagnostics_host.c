#include "photo_suggest.h"
#include <assert.h>
#include <string.h>
static uint16_t frame[256u*192u];
static uint16_t rgb(unsigned x){return (uint16_t)(x|(x<<5)|(x<<10));}
static void scene(void)
{
 for(unsigned y=0;y<192u;y++)for(unsigned x=0;x<256u;x++)
  frame[y*256u+x]=rgb(20u);
 for(unsigned y=64u;y<84u;y++)
  for(unsigned x=72u;x<108u;x++)frame[y*256u+x]=rgb(8u);
 for(unsigned y=64u;y<84u;y++)
  for(unsigned x=148u;x<184u;x++)frame[y*256u+x]=rgb(8u);
}
int main(void)
{
 MdsAvatar seed,out[3],sentinel[3];mds_new(&seed);
 memset(out,0x75,sizeof out);memcpy(sentinel,out,sizeof out);
 scene();
 assert(mds_photo_suggest_diagnose(0,256,192,&seed,out)==MDS_PHOTO_SUGGEST_INVALID);
 assert(mds_photo_suggest_diagnose(frame,255,192,&seed,out)==MDS_PHOTO_SUGGEST_INVALID);
 assert(mds_photo_suggest_diagnose(frame,256,192,&seed,0)==MDS_PHOTO_SUGGEST_INVALID);
 assert(!memcmp(out,sentinel,sizeof out));
 seed.value[5]=255;
 assert(mds_photo_suggest_diagnose(frame,256,192,&seed,out)==MDS_PHOTO_SUGGEST_BAD_DRAFT);
 assert(!memcmp(out,sentinel,sizeof out));
 seed.value[5]=0;
 for(unsigned i=0;i<256u*192u;i++)frame[i]=rgb(0u);
 assert(mds_photo_suggest_diagnose(frame,256,192,&seed,out)==MDS_PHOTO_SUGGEST_BAD_QUALITY);
 assert(!memcmp(out,sentinel,sizeof out));
 for(unsigned i=0;i<256u*192u;i++)frame[i]=rgb(20u);
 /* Make a usable exposure distribution with only one dark patch. */
 for(unsigned y=64u;y<84u;y++)
  for(unsigned x=72u;x<108u;x++)frame[y*256u+x]=rgb(8u);
 assert(mds_photo_suggest_diagnose(frame,256,192,&seed,out)==MDS_PHOTO_SUGGEST_NO_PAIR);
 assert(!memcmp(out,sentinel,sizeof out));
 scene();
 assert(mds_photo_suggest_diagnose(frame,256,192,&seed,out)==MDS_PHOTO_SUGGEST_READY);
 assert(mds_photo_suggest(frame,256,192,&seed,out));
 for(unsigned i=0;i<3u;i++)assert(mds_valid(&out[i]));
 return 0;
}
