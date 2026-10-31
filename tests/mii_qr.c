#include "mii_qr.h"
#include "qr_scan.h"
#include "vendor/qr/qrcodegen.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cfs_fixture.h"
#include "qr_fixture.h"
static uint16_t camera[256*192];
int main(int argc,char**argv)
{
 assert(argc==3);MdsMiiRecord r,decoded;assert(mds_cfs_decode(&r,cfs_fixture,96));uint8_t payload[112],bad[112],matrix[MDS_QR_BUFFER];
 assert(mds_mii_qr_encrypt(&r,payload));assert(!memcmp(payload,qr_fixture,112));assert(mds_mii_qr_decrypt(&decoded,payload,112));assert(!memcmp(decoded.raw,r.raw,96));
 for(unsigned i=0;i<112;i++){memcpy(bad,payload,112);bad[i]^=1;assert(!mds_mii_qr_decrypt(&decoded,bad,112));}
 assert(!mds_mii_qr_decrypt(&decoded,payload,111));assert(!mds_mii_qr_decrypt(&decoded,payload,113));
 assert(mds_mii_qr_matrix(payload,matrix));assert(qrcodegen_getSize(matrix)==57);
 FILE*f=fopen(argv[1],"wb");assert(f);assert(fwrite(payload,1,112,f)==112);assert(!fclose(f));
 f=fopen(argv[2],"wb");assert(f);assert(mds_mii_qr_photo(f,matrix,NULL));assert(!fclose(f));
 for(unsigned y=0;y<192;y++)for(unsigned x=0;x<256;x++){int qx=((int)x-63)/2-4,qy=((int)y-31)/2-4;camera[y*256+x]=(x>=63&&y>=31&&qx>=0&&qx<57&&qy>=0&&qy<57&&qrcodegen_getModule(matrix,qx,qy))?0x8000:0xffff;}
 assert(mds_qr_scan_rgb555(&decoded,camera,256,192));assert(!memcmp(decoded.raw,r.raw,96));memset(camera,0xff,sizeof camera);assert(!mds_qr_scan_rgb555(&decoded,camera,256,192));
 r.avatar.value[47]=0;assert(!mds_mii_qr_encrypt(&r,payload));
 f=fopen("/dev/full","wb");if(f){setbuf(f,NULL);assert(!mds_mii_qr_photo(f,matrix,NULL));fclose(f);}
 puts("PASS: authenticated Mii QR wrapping/corruption, sharing policy, version-10-H matrix, streamed PNG and camera-sized QR scan");
}
