/* Cartridge ownership and fixed two-address-byte EEPROM transport.
 * Validation, error state and verified writes live in portable save_storage.c. */
#include <nds.h>
#include <string.h>
#include "save_nds.h"
#include "save_chip.h"
static MdsStorage storage;
static int read_save(void *context,unsigned address,uint8_t *data,size_t size)
{
 (void)context;sysSetCardOwner(BUS_OWNER_ARM9);return mds_chip_read(address,data,size);
}
static int write_save(void *context,unsigned address,const uint8_t *data,size_t size)
{
 (void)context;sysSetCardOwner(BUS_OWNER_ARM9);return mds_chip_write(address,data,size);
}
int mds_cart_open(MdsGallery *g)
{
 /* Use the bootloader header: raw header commands are invalid after NitroFS. */
 if(memcmp(__NDSHeader->gameCode,"MDSD",4)){
  mds_storage_disable(&storage,MDS_STORAGE_WRONG_ROM);return 0;
 }
 sysSetCardOwner(BUS_OWNER_ARM9);
 if(!mds_chip_present()){mds_storage_disable(&storage,MDS_STORAGE_UNAVAILABLE);return 0;}
 return mds_storage_open(&storage,g,read_save,write_save,NULL);
}
int mds_cart_flush(MdsGallery *g){return mds_storage_flush(&storage,g);}
MdsStorageState mds_cart_state(void){return storage.state;}
const char *mds_cart_status(void){return mds_storage_message(storage.state);}
