#include "save_compact.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t image[MDS_COMPACT_SIZE];static MdsGallery a,b;
static uint32_t crc(const uint8_t*p,size_t n){uint32_t c=~0u;for(size_t i=0;i<n;i++){c^=p[i];for(unsigned k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(c&1));}return ~c;}
static void w32(uint8_t*p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(i*8));}
static unsigned width(unsigned x){unsigned n=0;do{n++;x>>=1;}while(x);return n;}
int main(void){
 MdsAvatar m;mds_new(&m);m.value[51]=1;m.value[46]=0;strcpy(m.creator,"Creator");mds_gallery_new(&a);assert(mds_gallery_store(&a,0,&m));assert(mds_compact_encode(&a,image,sizeof image));assert(image[4]==2);
 image[4]=1;unsigned bit=0;for(unsigned f=0;f<61;f++)bit+=width(mds_fields[f].maximum);
 for(unsigned k=0;k<7;k++){unsigned at=bit+k;image[25+at/8]=(uint8_t)((image[25+at/8]&~(1u<<(at%8)))|(((70u>>k)&1)<<(at%8)));}
 const unsigned body=24+100*75;w32(image+body,crc(image,body));
 assert(mds_compact_load(&b,image,sizeof image));assert(b.miis[0].value[61]==0&&b.miis[0].value[46]==1&&!strcmp(b.miis[0].creator,"Creator"));
 b.miis[0].value[61]=3;assert(mds_compact_encode(&b,image,sizeof image));assert(mds_compact_load(&a,image,sizeof image)&&a.miis[0].value[61]==3);
 uint8_t packet[MDS_PACKET];assert(mds_encode(&m,packet,sizeof packet));memcpy(packet,"MDS2",4);packet[68+61]=70;w32(packet+130,crc(packet,130));MdsAvatar old;assert(mds_decode(&old,packet,sizeof packet)&&old.value[61]==0&&old.value[46]==1&&!strcmp(old.creator,"Creator"));
 puts("PASS: version-1 compact and MDS2 migration clears legacy input byte, retains names, normalizes Personal favorite and persists new status flags");
}
