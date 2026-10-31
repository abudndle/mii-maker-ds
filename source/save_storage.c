#include "save_storage.h"
#include "save_compact.h"
#include <string.h>
void mds_storage_disable(MdsStorage *s,MdsStorageState state)
{
 s->ready=0;s->state=state;
}
int mds_storage_open(MdsStorage *s,MdsGallery *g,MdsStorageRead read,MdsStorageWrite write,void *context)
{
 s->ready=0;s->compact=0;s->read=read;s->write=write;s->context=context;
 if(!read||!write){s->state=MDS_STORAGE_UNAVAILABLE;return 0;}
 if(!read(context,0,s->image,sizeof s->image)){s->state=MDS_STORAGE_READ_ERROR;return 0;}
 /* Both decoders validate completely before replacing the caller's gallery. */
 if(mds_gallery_load(g,s->image,sizeof s->image))s->state=MDS_STORAGE_LEGACY;
 else if(mds_compact_load(g,s->image,MDS_COMPACT_SIZE)){s->compact=1;s->state=MDS_STORAGE_COMPACT;}
 else{
  int blank_ff=1,blank_00=1;
  for(unsigned i=0;i<sizeof s->image;i++){
   if(s->image[i]!=255)blank_ff=0;
   if(s->image[i]!=0)blank_00=0;
  }
  if(!blank_ff&&!blank_00){
   s->state=(!memcmp(s->image,"MDSC",4)||!memcmp(s->image,"MDSV",4)||
             !memcmp(s->image+MDS_BANK_SIZE,"MDSV",4))?MDS_STORAGE_DAMAGED:MDS_STORAGE_UNKNOWN;
   return 0;
  }
  mds_gallery_new(g);s->compact=1;s->state=MDS_STORAGE_NEW;
 }
 s->ready=1;return 1;
}
int mds_storage_flush(MdsStorage *s,MdsGallery *g)
{
 if(!s->ready)return 0;
 int prior=g->active_bank;uint32_t generation=g->generation;
 unsigned address=0;size_t size=MDS_COMPACT_SIZE;
 if(s->compact){
  if(!mds_compact_encode(g,s->image,MDS_COMPACT_SIZE)){s->state=MDS_STORAGE_INVALID;return 0;}
 }else{
  if(!mds_gallery_commit(g,s->image,sizeof s->image)){s->state=MDS_STORAGE_INVALID;return 0;}
  address=(unsigned)g->active_bank*MDS_BANK_SIZE;size=MDS_SAVE_BODY+4;
 }
 int written=s->write(s->context,address,s->image+address,size);
 int verified=written&&s->read(s->context,address,s->verify,size)&&!memcmp(s->image+address,s->verify,size);
 if(!verified){
  g->active_bank=prior;g->generation=generation;
  s->state=written?MDS_STORAGE_VERIFY_ERROR:MDS_STORAGE_WRITE_ERROR;return 0;
 }
 if(s->compact){g->generation++;g->active_bank=2;}
 s->state=s->compact?MDS_STORAGE_COMPACT:MDS_STORAGE_LEGACY;return 1;
}
const char *mds_storage_message(MdsStorageState state)
{
 switch(state){
 case MDS_STORAGE_NEW:return "Blank save: ready for first Mii.";
 case MDS_STORAGE_COMPACT:return "8 KiB cartridge save ready.";
 case MDS_STORAGE_LEGACY:return "64 KiB cartridge save ready.";
 case MDS_STORAGE_UNAVAILABLE:return "Cartridge save is unavailable.";
 case MDS_STORAGE_WRONG_ROM:return "Unsupported cartridge game code.";
 case MDS_STORAGE_READ_ERROR:return "Could not read cartridge save.";
 case MDS_STORAGE_UNKNOWN:return "Unrecognized save: kept intact.";
 case MDS_STORAGE_DAMAGED:return "Damaged save: writes blocked.";
 case MDS_STORAGE_INVALID:return "Invalid Mii data: save refused.";
 case MDS_STORAGE_WRITE_ERROR:return "Cartridge write failed.";
 case MDS_STORAGE_VERIFY_ERROR:return "Save readback failed.";
 default:return "Cartridge save is closed.";
 }
}
