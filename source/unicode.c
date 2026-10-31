#include "unicode.h"
#include <string.h>
int mds_name_to_utf16(uint8_t*out,const char*name)
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
int mds_name_from_utf16(char*out,const uint8_t*data)
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
