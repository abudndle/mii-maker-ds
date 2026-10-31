/* Independently authored fixed-size 3DS CCM wrapping. Published format/key:
 * jaames/96ce8daa11b61b758b6b0227b55f9f78; rounded B0 length observation
 * Genwald/MiiPort include/ccm_3ds.h. AES: public-domain tiny-AES-c.
 * A QR record has 8 nonce bytes, 88 ciphertext bytes and a 16-byte tag. */
#include "mii_qr.h"
#include "vendor/aes/aes.h"
#include "vendor/qr/qrcodegen.h"
#include <string.h>
static const uint8_t key[16]={0x59,0xfc,0x81,0x7e,0x64,0x46,0xea,0x61,0x90,0x34,0x7b,0x20,0xe9,0xbd,0xce,0x52};
static void ccm(const uint8_t*input,const uint8_t*nonce,uint8_t*output,uint8_t*tag,int decrypt)
{
 struct AES_ctx aes;AES_init_ctx(&aes,key);
 uint8_t mac[16]={0x3a},ctr[16]={2},stream[16],block[16];
 memcpy(mac+1,nonce,8);mac[15]=96; /* 3DS authenticates the padded length. */
 AES_ECB_encrypt(&aes,mac);memcpy(ctr+1,nonce,8);
 for(unsigned offset=0;offset<88;offset+=16){
  unsigned n=88-offset<16?88-offset:16;ctr[15]=(uint8_t)(offset/16+1);memcpy(stream,ctr,16);AES_ECB_encrypt(&aes,stream);
  memset(block,0,16);
  for(unsigned k=0;k<n;k++){output[offset+k]=input[offset+k]^stream[k];block[k]=decrypt?output[offset+k]:input[offset+k];}
  for(unsigned k=0;k<16;k++){mac[k]^=block[k];}AES_ECB_encrypt(&aes,mac);
 }
 ctr[15]=0;AES_ECB_encrypt(&aes,ctr);for(unsigned k=0;k<16;k++)tag[k]=mac[k]^ctr[k];
 memset(&aes,0,sizeof aes);
}
int mds_mii_qr_encrypt(const MdsMiiRecord*r,uint8_t out[MDS_QR_PAYLOAD])
{
 if(!r||!out||!r->avatar.value[47])return 0;
 uint8_t raw[96],plain[88],payload[112];if(!mds_cfs_encode(r,raw,sizeof raw))return 0;
 memcpy(payload,raw+12,8);memcpy(plain,raw,12);memcpy(plain+12,raw+20,76);
 ccm(plain,payload,payload+8,payload+96,0);memcpy(out,payload,sizeof payload);return 1;
}
int mds_mii_qr_decrypt(MdsMiiRecord*out,const uint8_t*p,size_t n)
{
 if(!out||!p||n!=112)return 0;
 uint8_t plain[88],tag[16],raw[96];ccm(p+8,p,plain,tag,1);unsigned difference=0;for(unsigned k=0;k<16;k++)difference|=tag[k]^p[96+k];
 if(difference){memset(plain,0,sizeof plain);return 0;}
 memcpy(raw,plain,12);memcpy(raw+12,p,8);memcpy(raw+20,plain+12,76);return mds_cfs_decode(out,raw,sizeof raw);
}
int mds_mii_qr_matrix(const uint8_t*p,uint8_t out[MDS_QR_BUFFER])
{
 if(!p||!out)return 0;
 uint8_t data[qrcodegen_BUFFER_LEN_FOR_VERSION(10)],qr[qrcodegen_BUFFER_LEN_FOR_VERSION(10)];
 memcpy(data,p,112);
 if(!qrcodegen_encodeBinary(data,112,qr,qrcodegen_Ecc_HIGH,10,10,qrcodegen_Mask_AUTO,false))return 0;
 if(qrcodegen_getSize(qr)!=57||sizeof qr>MDS_QR_BUFFER)return 0;
 memcpy(out,qr,sizeof qr);return 1;
}
