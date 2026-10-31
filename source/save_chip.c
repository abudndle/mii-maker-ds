#include <nds.h>
#include "save_chip.h"
/* Clear HOLD on release, including when disabling SPI. Some older emulators
   only observe HOLD to end a command and ignore the enable-bit edge. */
static int spi_byte(unsigned char tx,unsigned char *rx)
{
    REG_AUXSPIDATA=tx;
    unsigned timeout=100000;
    while(REG_AUXSPICNT&CARD_SPI_BUSY)if(!--timeout)return 0;
    *rx=REG_AUXSPIDATA;
    return 1;
}
static void begin(void){REG_AUXSPICNT=0xa040;}
static void end(void){REG_AUXSPICNT=0;}
static int last_byte(unsigned char tx,unsigned char *rx)
{
    REG_AUXSPICNT=0xa000;
    return spi_byte(tx,rx);
}
static int command(unsigned char cmd,unsigned char *result)
{
    unsigned char ignore;
    begin();
    int ok=result?spi_byte(cmd,&ignore):last_byte(cmd,&ignore);
    if(ok&&result)ok=last_byte(0,result);
    end();
    return ok;
}
static int wait_ready(void)
{
    for(unsigned i=0;i<100000;i++){
        unsigned char status;
        if(!command(5,&status)||status==255)return 0;
        if(!(status&1))return 1;
    }
    return 0;
}
int mds_chip_present(void)
{
    unsigned char status;
    if(!command(6,NULL)||!command(5,&status))return 0;
    int ok=status!=255&&(status&2);
    if(!command(4,NULL))return 0;
    return ok;
}
int mds_chip_read(unsigned address,uint8_t *data,size_t size)
{
    if(address>65536u||size>65536u-address)return 0;
    unsigned char ignore;
    begin();
    int ok=spi_byte(3,&ignore)&&spi_byte(address>>8,&ignore)&&spi_byte(address,&ignore);
    for(size_t i=0;ok&&i<size;i++)ok=i+1==size?last_byte(0,data+i):spi_byte(0,data+i);
    end();
    return ok;
}
int mds_chip_write(unsigned address,const uint8_t *data,size_t size)
{
    if(address>65536u||size>65536u-address)return 0;
    while(size){
        unsigned page=32u-(address&31u);
        if(page>size)page=(unsigned)size;
        if(!wait_ready()||!command(6,NULL))return 0;
        unsigned char ignore;
        begin();
        int ok=spi_byte(2,&ignore)&&spi_byte(address>>8,&ignore)&&spi_byte(address,&ignore);
        for(unsigned i=0;ok&&i<page;i++)ok=i+1==page?last_byte(data[i],&ignore):spi_byte(data[i],&ignore);
        end();
        if(!ok||!wait_ready())return 0;
        address+=page;data+=page;size-=page;
    }
    return command(4,NULL);
}
