/* Independent explicit-bit codec. Format references: libctru mii.h, and the
 * recovered eyebrow word in jamesrhg/cfl-mii (see reference/MII_EXCHANGE.md).
 * No compiler-dependent C bitfield layout, Nintendo code or database import. */
#include "mii_codec.h"
#include "unicode.h"
#include <string.h>
typedef struct {uint8_t field,byte,shift,width;} Field;
static const Field fields[]={
 {0,24,0,1},{49,24,1,4},{50,24,5,5},{45,24,10,4},{46,24,14,1},
 {48,1,0,1},{47,48,0,1},{2,48,1,4},{1,48,5,3},{3,49,0,4},{4,49,4,4},
 {43,46,0,8},{44,47,0,8},{5,50,0,8},{6,51,0,3},{7,51,3,1},
 {8,52,0,6},{9,52,6,3},{10,52,9,4},{11,52,13,3},{12,52,16,5},{13,52,21,4},{14,52,25,5},
 {15,56,0,5},{16,56,5,3},{17,56,8,4},{18,56,12,3},
 {19,58,0,5},{20,58,5,4},{21,58,9,5},
 {22,60,0,5},{23,60,5,4},{24,60,9,5},
 {25,62,0,6},{26,62,6,3},{27,62,9,4},{28,62,13,3},
 {29,64,0,5},{34,64,5,3},{35,66,0,3},{36,66,3,3},{37,66,6,4},{38,66,10,5},
 {30,68,0,4},{31,68,4,3},{32,68,7,4},{33,68,11,5},
 {39,70,0,1},{40,70,1,4},{41,70,5,5},{42,70,10,5}
};
uint16_t mds_mii_crc(const uint8_t*p,size_t n)
{
 uint16_t crc=0;
 for(size_t i=0;i<n;i++){crc^=(uint16_t)p[i]<<8;for(unsigned k=0;k<8;k++)crc=(uint16_t)((crc<<1)^((crc&0x8000)?0x1021:0));}
 return crc;
}
static unsigned bits(const uint8_t*p,unsigned start,unsigned width)
{
 unsigned v=0;for(unsigned i=0;i<width;i++)v|=((p[(start+i)/8]>>((start+i)%8))&1u)<<i;return v;
}
static void put(uint8_t*p,unsigned start,unsigned width,unsigned value)
{
 for(unsigned i=0;i<width;i++){unsigned at=start+i;p[at/8]=(uint8_t)((p[at/8]&~(1u<<(at%8)))|(((value>>i)&1u)<<(at%8)));}
}
static int valid(const MdsAvatar*a)
{
 static const unsigned days[]={0,31,29,31,30,31,30,31,31,30,31,30,31};
 if(!mds_valid(a))return 0;
 unsigned m=a->value[49],d=a->value[50];
 if((m||d)&&(!m||!d||d>days[m]))return 0;
 uint8_t name[20];if(!a->name[0]||!mds_name_to_utf16(name,a->name)||!mds_name_to_utf16(name,a->creator))return 0;
 return 1;
}
int mds_cfs_decode(MdsMiiRecord*out,const void*bytes,size_t size)
{
 if(!out||!bytes||size!=MDS_CFSD_SIZE)return 0;
 const uint8_t*p=bytes;
 if(p[0]!=3||mds_mii_crc(p,94)!=((unsigned)p[94]<<8|p[95]))return 0;
 MdsMiiRecord r;memcpy(r.raw,p,sizeof r.raw);mds_new(&r.avatar);
 for(unsigned i=0;i<sizeof fields/sizeof fields[0];i++){
  const Field*f=&fields[i];unsigned v=bits(p,f->byte*8+f->shift,f->width);
  r.avatar.value[f->field]=(uint8_t)(f->field==47?!v:v);
 }
 if(!mds_name_from_utf16(r.avatar.name,p+26)||!mds_name_from_utf16(r.avatar.creator,p+72)||!valid(&r.avatar))return 0;
 /* Personal ownership is local to a gallery, not inferred from a foreign ID. */
 r.avatar.value[51]=0;r.avatar.value[61]=(p[12]&0x80)?0:2;*out=r;return 1;
}
int mds_cfs_encode(const MdsMiiRecord*r,void*bytes,size_t size)
{
 if(!r||!bytes||size!=MDS_CFSD_SIZE||!valid(&r->avatar))return 0;
 MdsMiiRecord original;if(!mds_cfs_decode(&original,r->raw,sizeof r->raw))return 0;
 uint8_t p[MDS_CFSD_SIZE];memcpy(p,r->raw,sizeof p);
 for(unsigned i=0;i<sizeof fields/sizeof fields[0];i++){
  const Field*f=&fields[i];unsigned v=r->avatar.value[f->field];put(p,f->byte*8+f->shift,f->width,f->field==47?!v:v);
 }
 if(!mds_name_to_utf16(p+26,r->avatar.name)||!mds_name_to_utf16(p+72,r->avatar.creator))return 0;
 unsigned crc=mds_mii_crc(p,94);p[94]=(uint8_t)(crc>>8);p[95]=(uint8_t)crc;memcpy(bytes,p,sizeof p);return 1;
}

int mds_cfs_create(MdsMiiRecord*out,const MdsAvatar*a,uint32_t creation,uint64_t serial)
{
 if(!out||!a||!valid(a)||(a->value[61]&2))return 0;
 MdsMiiRecord r;memset(&r,0,sizeof r);r.avatar=*a;r.raw[0]=3;r.raw[3]=0x20;
 memcpy(r.raw+4,"MDSDMAKE",8);
 /* Normal DS-family copy with a software-assigned ID and locally administered
  * synthetic MAC. This does not impersonate a 3DS hardware identity. */
 r.raw[12]=(uint8_t)(0xc0|((creation>>24)&15));r.raw[13]=(uint8_t)(creation>>16);r.raw[14]=(uint8_t)(creation>>8);r.raw[15]=(uint8_t)creation;
 for(unsigned k=0;k<6;k++){r.raw[16+k]=(uint8_t)(serial>>(8*k));}
 r.raw[16]=(r.raw[16]&0xfc)|2;
 for(unsigned i=0;i<sizeof fields/sizeof fields[0];i++){const Field*f=&fields[i];unsigned v=a->value[f->field];put(r.raw,f->byte*8+f->shift,f->width,f->field==47?!v:v);}
 if(!mds_name_to_utf16(r.raw+26,a->name)||!mds_name_to_utf16(r.raw+72,a->creator))return 0;
 unsigned crc=mds_mii_crc(r.raw,94);r.raw[94]=(uint8_t)(crc>>8);r.raw[95]=(uint8_t)crc;*out=r;return 1;
}
