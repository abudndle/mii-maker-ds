#include "save_compact.h"
#include "unicode.h"
#include <string.h>
#define RECORD 75u
#define BODY (24u+MDS_SLOTS*RECORD)
static uint32_t get32(const uint8_t*p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put32(uint8_t*p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(i*8));}
static uint32_t crc(const uint8_t*p,size_t n){uint32_t c=~0u;for(size_t i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(c&1));}return ~c;}
static unsigned width(unsigned n){unsigned w=0;do{w++;n>>=1;}while(n);return w;}
int mds_compact_encode(const MdsGallery*g,uint8_t*out,size_t n)
{
 if(!g||!out||n!=MDS_COMPACT_SIZE)return 0;
 /* Validate every slot before writing any bytes to the destination. */
 unsigned checked_personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++){
  if(g->used[i]>1)return 0;
  if(!g->used[i])continue;
  const MdsAvatar*a=&g->miis[i];
  uint8_t name[20],creator[20];
  if(!mds_valid(a)||!mds_name_to_utf16(name,a->name)||!mds_name_to_utf16(creator,a->creator))return 0;
  checked_personal+=a->value[51];
  if(checked_personal>1)return 0;
 }
 memset(out,0xff,n);memset(out,0,BODY);memcpy(out,"MDSC",4);put32(out+4,2);put32(out+8,g->generation+1);put32(out+12,BODY);memcpy(out+16,g->settings,8);
 unsigned personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++){
  if(g->used[i]>1)return 0;
  uint8_t*r=out+24+i*RECORD;r[0]=g->used[i];if(!r[0])continue;
  const MdsAvatar*a=&g->miis[i];if(!mds_valid(a))return 0;
  personal+=a->value[51];if(personal>1)return 0;
  unsigned bit=0;for(unsigned f=0;f<MDS_FIELDS;f++){unsigned w=width(mds_fields[f].maximum);for(unsigned k=0;k<w;k++,bit++)r[1+bit/8]|=((a->value[f]>>k)&1)<<(bit%8);}
  if(bit>272||!mds_name_to_utf16(r+35,a->name)||!mds_name_to_utf16(r+55,a->creator))return 0;
 }
 put32(out+BODY,crc(out,BODY));return 1;
}
int mds_compact_load(MdsGallery*g,const uint8_t*in,size_t n)
{
 if(!g||!in||n!=MDS_COMPACT_SIZE||memcmp(in,"MDSC",4)||(get32(in+4)!=1&&get32(in+4)!=2)||get32(in+12)!=BODY||get32(in+BODY)!=crc(in,BODY))return 0;
 unsigned version=get32(in+4);MdsGallery tmp;mds_gallery_new(&tmp);tmp.generation=get32(in+8);tmp.active_bank=2;memcpy(tmp.settings,in+16,8);
 unsigned personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++){
  const uint8_t*r=in+24+i*RECORD;if(r[0]>1)return 0;tmp.used[i]=r[0];if(!r[0])continue;
  MdsAvatar*a=&tmp.miis[i];unsigned bit=0;
  for(unsigned f=0;f<MDS_FIELDS;f++){unsigned w=width(version==1&&f==61?95:mds_fields[f].maximum),v=0;for(unsigned k=0;k<w;k++,bit++)v|=((r[1+bit/8]>>(bit%8))&1)<<k;a->value[f]=(uint8_t)(version==1&&f==61?0:v);}
  if(!mds_name_from_utf16(a->name,r+35)||!mds_name_from_utf16(a->creator,r+55)||!mds_valid(a))return 0;
  if(version==1&&a->value[51])a->value[46]=1;
  personal+=a->value[51];if(personal>1)return 0;
 }
 *g=tmp;return 1;
}
