#include "avatar.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(void){MdsAvatar a,b,guard;uint8_t packet[MDS_PACKET],copy[MDS_PACKET];mds_new(&a);assert(mds_valid(&a));
 /* Invalid pointers from import/save call chains must fail safely. */
 assert(!mds_valid(NULL));
 mds_new(NULL);mds_adjust(NULL,0,1);
 assert(!mds_encode(NULL,packet,sizeof packet));
 assert(!mds_encode(&a,NULL,sizeof packet));
 assert(!mds_decode(NULL,packet,sizeof packet));
 assert(!mds_decode(&b,NULL,sizeof packet));
 assert(!mds_write(&a,NULL));
 assert(!mds_read(&b,NULL));
 assert(!mds_read(NULL,"/tmp/missing-mii.dat"));
 for(unsigned f=0;f<MDS_FIELDS;f++){for(unsigned v=0;v<=mds_fields[f].maximum;v++){a.value[f]=(uint8_t)v;assert(mds_encode(&a,packet,sizeof packet));assert(mds_decode(&b,packet,sizeof packet));assert(!memcmp(&a,&b,sizeof a));}a.value[f]=0;mds_adjust(&a,f,-1);assert(a.value[f]==mds_fields[f].maximum);mds_adjust(&a,f,1);assert(!a.value[f]);}
 mds_new(&a);assert(mds_encode(&a,packet,sizeof packet));guard=a;
 for(unsigned i=0;i<sizeof packet;i++){memcpy(copy,packet,sizeof copy);copy[i]^=1;b=guard;assert(!mds_decode(&b,copy,sizeof copy));assert(!memcmp(&b,&guard,sizeof b));}
 for(unsigned n=0;n<MDS_PACKET;n++){assert(!mds_decode(&b,packet,n));}assert(!mds_decode(&b,packet,MDS_PACKET+1));
 a.value[5]=132;assert(!mds_encode(&a,packet,sizeof packet));mds_new(&a);memset(a.name,'A',32);assert(!mds_valid(&a));
 assert(!mds_service_available(MDS_DS,MDS_CAMERA,15));assert(mds_service_available(MDS_DSI,MDS_CAMERA,1));for(int s=0;s<4;s++)assert(!mds_service_available(MDS_DSI,(MdsService)s,0));
 mds_new(&a);assert(mds_write(&a,"/tmp/mds-core-test.dat"));assert(mds_read(&b,"/tmp/mds-core-test.dat"));assert(!memcmp(&a,&b,sizeof a));remove("/tmp/mds-core-test.dat");puts("PASS: fields, roundtrip, corruption, truncation, validation, DSi gating, file IO");}
