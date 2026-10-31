#include "save_compact.h"
#include <string.h>
#define RECORD 75u
#define BODY (24u+MDS_SLOTS*RECORD)
static uint32_t get32(const uint8_t*p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static void put32(uint8_t*p,uint32_t n){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(i*8));}
static uint32_t crc(const uint8_t*p,size_t n){uint32_t c=~0u;for(size_t i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(c&1));}return ~c;}
static unsigned width(unsigned n){unsigned w=0;do{w++;n>>=1;}while(n);return w;}
static int name_pack(uint8_t*out,const char*name)
{
 unsigned pos=0,i=0;memset(out,0,20);
 while(i<MDS_NAME&&name[i]){
  uint32_t c=(uint8_t)name[i++],minimum=0;unsigned more=0;
  if(c>=0xf0&&c<=0xf4){c&=7;more=3;minimum=0x10000;}
  else if(c>=0xe0&&c<=0xef){c&=15;more=2;minimum=0x800;}
  else if(c>=0xc2&&c<=0xdf){c&=31;more=1;minimum=0x80;}
  else if(c>=128)return 0;
  while(more--){if(i>=MDS_NAME||((uint8_t)name[i]&0xc0)!=0x80)return 0;c=(c<<6)|((uint8_t)name[i++]&63);}
  if(c<minimum||c>0x10ffff||(c>=0xd800&&c<=0xdfff))return 0;
  if(c>=0x10000){if(pos+2>10)return 0;c-=0x10000;unsigned hi=0xd800+(c>>10),lo=0xdc00+(c&1023);out[pos*2]=(uint8_t)hi;out[pos*2+1]=(uint8_t)(hi>>8);pos++;out[pos*2]=(uint8_t)lo;out[pos*2+1]=(uint8_t)(lo>>8);pos++;}
  else{if(pos==10)return 0;out[pos*2]=(uint8_t)c;out[pos*2+1]=(uint8_t)(c>>8);pos++;}
 }
 return i<MDS_NAME;
}
static int name_unpack(char*out,const uint8_t*data)
{
 unsigned pos=0;memset(out,0,MDS_NAME);
 for(unsigned i=0;i<10;i++){
  uint32_t c=data[2*i]|(uint32_t)data[2*i+1]<<8;
  if(!c){for(unsigned j=i+1;j<10;j++)if(data[2*j]||data[2*j+1])return 0;break;}
  if(c>=0xd800&&c<=0xdbff){if(++i>=10)return 0;unsigned lo=data[2*i]|(unsigned)data[2*i+1]<<8;if(lo<0xdc00||lo>0xdfff)return 0;c=0x10000+((c-0xd800)<<10)+(lo-0xdc00);}
  else if(c>=0xdc00&&c<=0xdfff)return 0;
  unsigned n=c<0x80?1:c<0x800?2:c<0x10000?3:4;
  if(pos+n>=MDS_NAME)return 0;
  if(n==1)out[pos++]=(char)c;
  else{unsigned shift=(n-1)*6;out[pos++]=(char)((n==2?0xc0:n==3?0xe0:0xf0)|(c>>shift));while(shift){shift-=6;out[pos++]=(char)(0x80|((c>>shift)&63));}}
 }
 return 1;
}
int mds_compact_encode(const MdsGallery*g,uint8_t*out,size_t n)
{
 if(!g||!out||n!=MDS_COMPACT_SIZE)return 0;
 memset(out,0xff,n);memset(out,0,BODY);memcpy(out,"MDSC",4);put32(out+4,1);put32(out+8,g->generation+1);put32(out+12,BODY);memcpy(out+16,g->settings,8);
 unsigned personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++){
  if(g->used[i]>1)return 0;
  uint8_t*r=out+24+i*RECORD;r[0]=g->used[i];if(!r[0])continue;
  const MdsAvatar*a=&g->miis[i];if(!mds_valid(a))return 0;
  personal+=a->value[51];if(personal>1)return 0;
  unsigned bit=0;for(unsigned f=0;f<MDS_FIELDS;f++){unsigned w=width(mds_fields[f].maximum);for(unsigned k=0;k<w;k++,bit++)r[1+bit/8]|=((a->value[f]>>k)&1)<<(bit%8);}
  if(bit>272||!name_pack(r+35,a->name)||!name_pack(r+55,a->creator))return 0;
 }
 put32(out+BODY,crc(out,BODY));return 1;
}
int mds_compact_load(MdsGallery*g,const uint8_t*in,size_t n)
{
 if(!g||!in||n!=MDS_COMPACT_SIZE||memcmp(in,"MDSC",4)||get32(in+4)!=1||get32(in+12)!=BODY||get32(in+BODY)!=crc(in,BODY))return 0;
 MdsGallery tmp;mds_gallery_new(&tmp);tmp.generation=get32(in+8);tmp.active_bank=2;memcpy(tmp.settings,in+16,8);
 unsigned personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++){
  const uint8_t*r=in+24+i*RECORD;if(r[0]>1)return 0;tmp.used[i]=r[0];if(!r[0])continue;
  MdsAvatar*a=&tmp.miis[i];unsigned bit=0;
  for(unsigned f=0;f<MDS_FIELDS;f++){unsigned w=width(mds_fields[f].maximum),v=0;for(unsigned k=0;k<w;k++,bit++)v|=((r[1+bit/8]>>(bit%8))&1)<<k;a->value[f]=(uint8_t)v;}
  if(!name_unpack(a->name,r+35)||!name_unpack(a->creator,r+55)||!mds_valid(a))return 0;
  personal+=a->value[51];if(personal>1)return 0;
 }
 *g=tmp;return 1;
}
