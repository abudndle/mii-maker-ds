/* Cartridge save backend: compact 8 KiB snapshots and legacy 64 KiB banks.
 * Both sizes use the type-2 EEPROM protocol (two address bytes).
 * Do not auto-detect via RDID: some emulators return zero for that opcode.
 * No flash erases. Unknown existing save contents are never initialized.
 */
#include <nds.h>
#include <string.h>
#include "save_nds.h"
#include "save_chip.h"
#include "save_compact.h"
static uint8_t image[MDS_SAVE_SIZE],verify[MDS_BANK_SIZE];
static int ready,compact;
int mds_cart_open(MdsGallery *g)
{
    ready=0;compact=0;
    if(!g)return 0;
    /* A raw cardReadHeader command is invalid after NitroFS initializes the
       gamecard; use the bootloader header copy for the launched application. */
    if(memcmp(__NDSHeader->gameCode,"MDSD",4))return 0;
    sysSetCardOwner(BUS_OWNER_ARM9);
    /* An existing valid cartridge save is readable without ever issuing
       WREN. melonDS and some flashcarts may not report WEL immediately,
       which previously hid all saved Miis before any snapshot read. */
    if(!mds_chip_read(0,image,sizeof image))return 0;
    if(mds_gallery_load(g,image,sizeof image)){ready=1;return 1;}
    if(mds_compact_load(g,image,MDS_COMPACT_SIZE)){
        compact=1;ready=1;return 1;
    }
    /* With no valid snapshot, verify a writable EEPROM exists BEFORE
       creating a new gallery. Do not reinitialize unknown save contents. */
    if(!mds_chip_present())return 0;
    int blank_ff=1,blank_00=1;
    for(unsigned i=0;i<sizeof image;i++){
        if(image[i]!=255)blank_ff=0;
        if(image[i]!=0)blank_00=0;
    }
    if(!blank_ff&&!blank_00)return 0;
    mds_gallery_new(g);compact=1;ready=1;
    return 1;
}
int mds_cart_flush(MdsGallery *g)
{
    if(!g||!ready)return 0;
    if(compact){
        if(!mds_compact_encode(g,image,MDS_COMPACT_SIZE))return 0;
        sysSetCardOwner(BUS_OWNER_ARM9);
        if(!mds_chip_write(0,image,MDS_COMPACT_SIZE)||!mds_chip_read(0,verify,MDS_COMPACT_SIZE)||memcmp(image,verify,MDS_COMPACT_SIZE))return 0;
        g->generation++;g->active_bank=2;return 1;
    }
    int prior=g->active_bank;
    uint32_t gen=g->generation;
    if(!mds_gallery_commit(g,image,sizeof image))return 0;
    unsigned address=(unsigned)g->active_bank*MDS_BANK_SIZE;
    sysSetCardOwner(BUS_OWNER_ARM9);
    int written=mds_chip_write(address,image+address,MDS_SAVE_BODY+4);
    int read=mds_chip_read(address,verify,MDS_SAVE_BODY+4);
    if(!written||!read||memcmp(image+address,verify,MDS_SAVE_BODY+4)){
        g->active_bank=prior;
        g->generation=gen;
        return 0;
    }
    return 1;
}
