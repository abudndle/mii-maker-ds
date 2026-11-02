#include "save_compact.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static MdsGallery a,b;
static uint8_t image[MDS_COMPACT_SIZE];
int main(void){
 mds_gallery_new(&a);
 for(unsigned i=0;i<100;i++){
  MdsAvatar m;mds_new(&m);snprintf(m.name,sizeof m.name,"Mii%03u",i);strcpy(m.creator,"Creator");
  for(unsigned f=0;f<MDS_FIELDS;f++){m.value[f]=(uint8_t)(i%(mds_fields[f].maximum+1));}m.value[51]=i==0;
  assert(mds_gallery_store(&a,i,&m));
 }
 assert(mds_compact_encode(&a,image,sizeof image));assert(mds_compact_load(&b,image,sizeof image));assert(b.generation==1&&b.active_bank==2);
 assert(!memcmp(a.used,b.used,sizeof a.used));assert(!memcmp(a.miis,b.miis,sizeof a.miis));
 image[500]^=1;assert(!mds_compact_load(&b,image,sizeof image));image[500]^=1;
 assert(!mds_compact_load(&b,image,sizeof image-1));
 strcpy(a.miis[0].name,"\xe6\x97\xa5\xe6\x9c\xac\xf0\x9f\x98\x80");
 assert(mds_compact_encode(&a,image,sizeof image));assert(mds_compact_load(&b,image,sizeof image));assert(!strcmp(a.miis[0].name,b.miis[0].name));
 strcpy(a.miis[0].name,"12345678901");assert(!mds_compact_encode(&a,image,sizeof image));
 strcpy(a.miis[0].name,"\xc0\xaf");assert(!mds_compact_encode(&a,image,sizeof image));
 /* A rejected save must not partially overwrite a previous valid image. */
 mds_gallery_new(&a);
 memset(image,0xa5,sizeof image);
 a.used[99]=2;
 assert(!mds_compact_encode(&a,image,sizeof image));
 for(size_t k=0;k<sizeof image;k++)assert(image[k]==0xa5);
 a.used[99]=0;
 a.used[99]=1;
 mds_new(&a.miis[99]);
 strcpy(a.miis[99].name,"12345678901");
 assert(!mds_compact_encode(&a,image,sizeof image));
 for(size_t k=0;k<sizeof image;k++)assert(image[k]==0xa5);
 /* Overlapping the save image with live gallery RAM must be rejected
  * without corrupting any saved Mii, even after validation succeeds. */
 mds_gallery_new(&a);
 b=a;
 assert(!mds_compact_encode(&a,(uint8_t *)&a,MDS_COMPACT_SIZE));
 assert(!memcmp(&a,&b,sizeof a));
 assert((size_t)((uint8_t *)&a+sizeof a-(uint8_t *)&a.miis[0])>=MDS_COMPACT_SIZE);
 assert(!mds_compact_encode(&a,(uint8_t *)&a.miis[0],MDS_COMPACT_SIZE));
 assert(!memcmp(&a,&b,sizeof a));
 /* The opposite overlap direction (output starts just before gallery)
  * must also be rejected without modifying the live save records. */
 static struct {uint8_t prefix[MDS_COMPACT_SIZE];MdsGallery gallery;} overlap;
 mds_gallery_new(&overlap.gallery);
 b=overlap.gallery;
 assert(!mds_compact_encode(&overlap.gallery,
        overlap.prefix+MDS_COMPACT_SIZE-1u,MDS_COMPACT_SIZE));
 assert(!memcmp(&overlap.gallery,&b,sizeof b));
 assert(mds_compact_encode(&a,image,sizeof image));
 assert(!memcmp(&a,&b,sizeof a));
 puts("PASS: 100 compact slots, all fields, Unicode round trip, limits, invalid UTF-8, corruption, truncation and overlapping output");
}
