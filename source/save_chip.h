#ifndef MDS_SAVE_CHIP_H
#define MDS_SAVE_CHIP_H
#include <stdint.h>
#include <stddef.h>
/* Fixed 64 KiB / two-address-byte EEPROM transport. */
int mds_chip_present(void);
int mds_chip_read(unsigned address,uint8_t *data,size_t size);
int mds_chip_write(unsigned address,const uint8_t *data,size_t size);
#endif
