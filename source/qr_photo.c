/* Streaming RGB PNG, stored DEFLATE blocks. No full photo allocation is needed.
 * A 400x240 photo combines the original-resource Mii with a 3x QR and four
 * quiet modules on every edge. PNG CRC/Adler checksums protect file integrity. */
#include "mii_qr.h"
#include "vendor/qr/qrcodegen.h"
#include <string.h>
static uint32_t crc_update(uint32_t c,const uint8_t*p,size_t n){for(size_t i=0;i<n;i++){c^=p[i];for(unsigned k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(c&1));}return c;}
static void be(uint8_t*p,uint32_t v){for(unsigned k=0;k<4;k++)p[k]=(uint8_t)(v>>(24-8*k));}
static int write_bytes(FILE*f,const void*p,size_t n){return !n||fwrite(p,1,n,f)==n;}
static int chunk(FILE*f,const char*type,const uint8_t*p,unsigned n){uint8_t b[4];be(b,n);if(!write_bytes(f,b,4)||!write_bytes(f,type,4)||!write_bytes(f,p,n))return 0;uint32_t c=crc_update(crc_update(~0u,(const uint8_t*)type,4),p,n);be(b,~c);return write_bytes(f,b,4);}
int mds_mii_qr_photo(FILE*f,const uint8_t*qr,const uint16_t*head)
{
 if(!f||(qr&&qrcodegen_getSize(qr)!=57))return 0;
 const unsigned width=400,height=240,rowbytes=1201,total=rowbytes*height,blocks=(total+65534)/65535;
 static const uint8_t signature[]={137,80,78,71,13,10,26,10};uint8_t ihdr[13]={0};be(ihdr,width);be(ihdr+4,height);ihdr[8]=8;ihdr[9]=2;
 if(!write_bytes(f,signature,8)||!chunk(f,"IHDR",ihdr,13))return 0;
 uint8_t b[5],row[1201];be(b,2+blocks*5+total+4);if(!write_bytes(f,b,4)||!write_bytes(f,"IDAT",4))return 0;
 uint32_t crc=crc_update(~0u,(const uint8_t*)"IDAT",4),a1=1,a2=0;unsigned remaining=0,emitted=0;
 uint8_t zlib[2]={0x78,0x01};crc=crc_update(crc,zlib,2);if(!write_bytes(f,zlib,2))return 0;
 for(unsigned y=0;y<height;y++){
  row[0]=0;memset(row+1,255,width*3);
  for(unsigned x=0;x<width;x++){
   uint8_t*pixel=row+1+x*3;
   unsigned left=qr?16:120;
   if(head&&x>=left&&x<left+160&&y>=32&&y<192){unsigned c=head[((y-32)*128/160)*128+(x-left)*128/160];if(c&0x8000)for(unsigned k=0;k<3;k++){unsigned v=(c>>(5*k))&31;pixel[k]=(uint8_t)((v<<3)|(v>>2));}}
   if(qr&&x>=195&&x<390&&y>=16&&y<211){int qx=(int)(x-195)/3-4,qy=(int)(y-16)/3-4;if(qx>=0&&qx<57&&qy>=0&&qy<57&&qrcodegen_getModule(qr,qx,qy))memset(pixel,0,3);}
  }
  for(unsigned pos=0;pos<rowbytes;){
   if(!remaining){remaining=total-emitted;if(remaining>65535)remaining=65535;unsigned inverse=remaining^65535;b[0]=emitted+remaining==total?1:0;b[1]=(uint8_t)remaining;b[2]=(uint8_t)(remaining>>8);b[3]=(uint8_t)inverse;b[4]=(uint8_t)(inverse>>8);crc=crc_update(crc,b,5);if(!write_bytes(f,b,5))return 0;}
   unsigned n=rowbytes-pos;if(n>remaining)n=remaining;crc=crc_update(crc,row+pos,n);
   for(unsigned k=0;k<n;k++){a1=(a1+row[pos+k])%65521;a2=(a2+a1)%65521;}
   if(!write_bytes(f,row+pos,n))return 0;
   pos+=n;remaining-=n;emitted+=n;
  }
 }
 be(b,(a2<<16)|a1);crc=crc_update(crc,b,4);if(!write_bytes(f,b,4))return 0;be(b,~crc);
 return write_bytes(f,b,4)&&chunk(f,"IEND",NULL,0)&&!ferror(f);
}
