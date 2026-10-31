#include "qr_scan.h"
#include "mii_qr.h"
#include "vendor/quirc/quirc.h"
int mds_qr_scan_rgb555(MdsMiiRecord*out,const uint16_t*image,unsigned w,unsigned h)
{
 if(!out||!image||w<64||h<64||w>640||h>480)return 0;
 struct quirc*q=quirc_new();if(!q)return 0;
 if(quirc_resize(q,(int)w,(int)h)){quirc_destroy(q);return 0;}
 uint8_t*gray=quirc_begin(q,NULL,NULL);
 for(unsigned i=0;i<w*h;i++){unsigned c=image[i],r=c&31,g=(c>>5)&31,b=(c>>10)&31;gray[i]=(uint8_t)((r*77+g*150+b*29)*255/(31*256));}
 quirc_end(q);int found=0;
 for(int i=0;i<quirc_count(q);i++){
  struct quirc_code code;struct quirc_data data;quirc_extract(q,i,&code);
  quirc_decode_error_t error=quirc_decode(&code,&data);
  if(error==QUIRC_ERROR_DATA_ECC){quirc_flip(&code);error=quirc_decode(&code,&data);}
  if(!error&&mds_mii_qr_decrypt(out,data.payload,(size_t)data.payload_len)){found=1;break;}
 }
 quirc_destroy(q);return found;
}
