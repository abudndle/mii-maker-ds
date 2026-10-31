#include "mii_codec.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cfs_fixture.h"
int main(void){
 assert(mds_mii_crc((const uint8_t*)"123456789",9)==0x31c3);
 MdsMiiRecord r,guard,decoded;assert(mds_cfs_decode(&r,cfs_fixture,96));assert(!strcmp(r.avatar.name,"CodecTest")&&!strcmp(r.avatar.creator,"DS Test"));
 const unsigned expected[52]={1,4,7,6,3,84,6,1,35,2,5,4,6,9,11,19,5,6,4,10,7,14,13,6,10,24,3,7,4,8,4,2,3,13,3,2,4,6,10,1,5,10,20,89,37,9,1,1,1,2,29,0};
 for(unsigned f=0;f<52;f++)assert(r.avatar.value[f]==expected[f]);
 uint8_t out[96];assert(mds_cfs_encode(&r,out,96));assert(!memcmp(out,cfs_fixture,96));guard=r;
 for(unsigned i=0;i<96;i++){uint8_t bad[96];memcpy(bad,cfs_fixture,96);bad[i]^=1;decoded=guard;assert(!mds_cfs_decode(&decoded,bad,96));assert(!memcmp(&decoded,&guard,sizeof guard));}
 for(unsigned n=0;n<96;n++){assert(!mds_cfs_decode(&decoded,cfs_fixture,n));}
 assert(!mds_cfs_decode(&decoded,cfs_fixture,97));
 for(unsigned f=0;f<51;f++){
  r=guard;r.avatar.value[f]=mds_fields[f].maximum;if(f==49)r.avatar.value[50]=29;if(f==50)r.avatar.value[49]=12;
  assert(mds_cfs_encode(&r,out,96));assert(mds_cfs_decode(&decoded,out,96));assert(decoded.avatar.value[f]==r.avatar.value[f]);
  assert(!memcmp(out,guard.raw,1)&&!memcmp(out+2,guard.raw+2,22)&&out[92]==guard.raw[92]&&out[93]==guard.raw[93]);
 }
 r=guard;strcpy(r.avatar.name,"\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e");strcpy(r.avatar.creator,"\xf0\x9f\x98\x80");assert(mds_cfs_encode(&r,out,96));assert(mds_cfs_decode(&decoded,out,96));assert(!strcmp(r.avatar.name,decoded.avatar.name)&&!strcmp(r.avatar.creator,decoded.avatar.creator));
 r=guard;r.avatar.value[50]=30;assert(!mds_cfs_encode(&r,out,96));r=guard;r.avatar.name[0]=0;assert(!mds_cfs_encode(&r,out,96));
 puts("PASS: reference CFSD mapping, metadata-preserving encode, CRC, all corrupt/truncated records, field extrema, UTF-16/surrogates and profile validation");
}
