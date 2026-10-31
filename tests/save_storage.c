#include "save_storage.h"
#include "save_compact.h"
#include "editor.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static MdsStorage storage;
static MdsGallery gallery,prior,reloaded;
static uint8_t device[MDS_SAVE_SIZE],original[MDS_SAVE_SIZE];
typedef struct {unsigned reads,writes,address;size_t size,capacity;int read_fail,write_fail,mismatch;} Device;
static Device io;
static int read_device(void *ctx,unsigned address,uint8_t *out,size_t size)
{
 Device *d=ctx;d->reads++;
 assert(address<=MDS_SAVE_SIZE&&size<=MDS_SAVE_SIZE-address);
 if(d->read_fail)return 0;
 for(size_t i=0;i<size;i++)out[i]=device[(address+i)%d->capacity];
 if(d->mismatch&&size)out[size/2]^=1;
 return 1;
}
static int write_device(void *ctx,unsigned address,const uint8_t *in,size_t size)
{
 Device *d=ctx;d->writes++;d->address=address;d->size=size;
 assert(address<=MDS_SAVE_SIZE&&size<=MDS_SAVE_SIZE-address);
 /* A failed transport may already have written part of the physical save. */
 size_t written=d->write_fail?size/2:size;
 for(size_t i=0;i<written;i++)device[(address+i)%d->capacity]=in[i];
 return !d->write_fail;
}
static int persist(MdsGallery *g,void *ctx){return mds_storage_flush(ctx,g);}
static void setup(void)
{
 memset(&io,0,sizeof io);io.capacity=MDS_SAVE_SIZE;
 memset(device,255,sizeof device);mds_gallery_new(&gallery);
 MdsAvatar a;mds_new(&a);strcpy(a.name,"Retained");assert(mds_gallery_store(&gallery,17,&a));
 prior=gallery;
}
static void rejected(MdsStorageState state)
{
 memcpy(original,device,sizeof device);
 assert(!mds_storage_open(&storage,&gallery,read_device,write_device,&io));
 assert(storage.state==state&&!storage.ready&&!memcmp(&gallery,&prior,sizeof gallery));
 assert(!mds_storage_flush(&storage,&gallery)&&io.writes==0);
 assert(!memcmp(device,original,sizeof device));
}
static void failures(int legacy)
{
 setup();
 if(legacy){assert(mds_gallery_commit(&gallery,device,sizeof device));assert(mds_gallery_commit(&gallery,device,sizeof device));}
 assert(mds_storage_open(&storage,&gallery,read_device,write_device,&io));
 assert(storage.state==(legacy?MDS_STORAGE_LEGACY:MDS_STORAGE_NEW));
 MdsEditor e;mds_editor_begin(&e,&gallery);e.draft.value[5]=23;
 for(unsigned fault=0;fault<3;fault++){
  prior=gallery;
  io.write_fail=fault==0;io.read_fail=fault==1;io.mismatch=fault==2;
  assert(!mds_editor_save(&e,persist,&storage));
  assert(storage.ready&&storage.state==(fault==0?MDS_STORAGE_WRITE_ERROR:MDS_STORAGE_VERIFY_ERROR));
  assert(!memcmp(&gallery,&prior,sizeof gallery)&&e.draft.value[5]==23&&mds_editor_dirty(&e));
  io.write_fail=io.read_fail=io.mismatch=0;
 }
 assert(mds_editor_save(&e,persist,&storage)&&!mds_editor_dirty(&e));
 assert(storage.state==(legacy?MDS_STORAGE_LEGACY:MDS_STORAGE_COMPACT));
 assert(io.size==(legacy?MDS_SAVE_BODY+4:MDS_COMPACT_SIZE));
 assert(gallery.generation==prior.generation+1);
 assert(mds_storage_open(&storage,&reloaded,read_device,write_device,&io));
 assert(!memcmp(&gallery,&reloaded,sizeof gallery));
 /* Invalid avatars are refused before transport writes. */
 unsigned writes=io.writes;gallery.miis[0].value[5]=255;
 assert(!mds_storage_flush(&storage,&gallery)&&storage.state==MDS_STORAGE_INVALID&&io.writes==writes);
}
int main(void)
{
 setup();io.read_fail=1;rejected(MDS_STORAGE_READ_ERROR);
 setup();memset(device,0x5a,sizeof device);rejected(MDS_STORAGE_UNKNOWN);
 setup();memcpy(device,"MDSC",4);rejected(MDS_STORAGE_DAMAGED);
 setup();memcpy(device+MDS_BANK_SIZE,"MDSV",4);rejected(MDS_STORAGE_DAMAGED);
 setup();assert(!mds_storage_open(&storage,&gallery,NULL,write_device,&io));
 assert(storage.state==MDS_STORAGE_UNAVAILABLE&&!memcmp(&gallery,&prior,sizeof gallery));
 for(unsigned blank=0;blank<2;blank++){
  setup();memset(device,blank?255:0,sizeof device);
  assert(mds_storage_open(&storage,&gallery,read_device,write_device,&io));
  assert(storage.state==MDS_STORAGE_NEW&&io.writes==0&&!gallery.used[17]);
 }
 failures(0);failures(1);
 /* Real 8 KiB EEPROM aliases reads above its capacity. */
 setup();io.capacity=MDS_COMPACT_SIZE;
 assert(mds_compact_encode(&gallery,device,MDS_COMPACT_SIZE));
 assert(mds_storage_open(&storage,&reloaded,read_device,write_device,&io));
 assert(storage.state==MDS_STORAGE_COMPACT&&reloaded.used[17]);
 /* One damaged legacy bank must still load the valid previous generation. */
 setup();assert(mds_gallery_commit(&gallery,device,sizeof device));
 prior=gallery;gallery.miis[17].value[5]=12;assert(mds_gallery_commit(&gallery,device,sizeof device));
 device[MDS_BANK_SIZE+40]^=1;
 assert(mds_storage_open(&storage,&reloaded,read_device,write_device,&io));
 assert(!memcmp(&prior,&reloaded,sizeof prior)&&storage.state==MDS_STORAGE_LEGACY);
 /* A blocked read can succeed later without modifying the device. */
 io.read_fail=1;prior=reloaded;
 assert(!mds_storage_open(&storage,&reloaded,read_device,write_device,&io));
 assert(!memcmp(&prior,&reloaded,sizeof prior));
 io.read_fail=0;assert(mds_storage_open(&storage,&reloaded,read_device,write_device,&io));
 unsigned writes=io.writes;mds_storage_disable(&storage,MDS_STORAGE_WRONG_ROM);
 assert(!mds_storage_flush(&storage,&reloaded)&&io.writes==writes);
 for(int state=MDS_STORAGE_CLOSED;state<=MDS_STORAGE_VERIFY_ERROR;state++)assert(mds_storage_message((MdsStorageState)state)[0]);
 puts("PASS: save classification, no destructive reads, both transports, partial writes/readback errors, draft rollback/retry, EEPROM aliasing and legacy recovery");
}
