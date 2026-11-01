/* Host mocks exercise the real DS cartridge save opening logic, including
 * emulator SPI devices that support READ but do not echo WREN status. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "nds.h"
#include "save_nds.h"
#include "save_chip.h"
#include "save_compact.h"
static MdsHostNdsHeader header={{'M','D','S','D'}};
MdsHostNdsHeader *__NDSHeader=&header;
static int probe_ok,read_ok,content,loads,compact_loads,probes,reset_count,read_count;
static uint8_t marker;
int mds_chip_present(void){probes++;return probe_ok;}
int mds_chip_read(unsigned addr,uint8_t *out,size_t n)
{
 read_count++;
 if(!read_ok)return 0;
 assert(addr==0&&n==MDS_SAVE_SIZE);
 memset(out,content==0?0xff:content==1?0:0x33,n);
 out[0]=marker;
 return 1;
}
int mds_chip_write(unsigned addr,const uint8_t *p,size_t n){(void)addr;(void)p;(void)n;return 1;}
int mds_gallery_load(MdsGallery *g,const uint8_t *p,size_t n)
{
 assert(n==MDS_SAVE_SIZE);loads++;
 if(p[0]!='V')return 0;
 g->used[0]=1;return 1;
}
int mds_compact_load(MdsGallery *g,const uint8_t *p,size_t n)
{
 assert(n==MDS_COMPACT_SIZE);compact_loads++;
 if(p[0]!='C')return 0;
 g->used[3]=1;return 1;
}
void mds_gallery_new(MdsGallery *g){reset_count++;memset(g,0,sizeof *g);}
int mds_gallery_commit(MdsGallery *g,uint8_t *p,size_t n)
{(void)g;(void)p;(void)n;return 1;}
int mds_compact_encode(const MdsGallery *g,uint8_t *p,size_t n)
{(void)g;(void)p;(void)n;return 1;}
static void reset(void)
{
 probe_ok=read_ok=1;content=2;marker='V';
 loads=compact_loads=probes=reset_count=read_count=0;
 memcpy(header.gameCode,"MDSD",4);
}
int main(void)
{
 MdsGallery g;
 reset();probe_ok=0;memset(&g,0,sizeof g);
 assert(mds_cart_open(&g));assert(g.used[0]);
 assert(probes==0&&read_count==1&&loads==1&&compact_loads==0&&reset_count==0);
 reset();probe_ok=0;marker='C';memset(&g,0,sizeof g);
 assert(mds_cart_open(&g));assert(g.used[3]);
 assert(probes==0&&loads==1&&compact_loads==1);
 reset();marker=0xff;content=0;memset(&g,3,sizeof g);
 assert(mds_cart_open(&g));assert(probes==1&&reset_count==1);
 reset();marker=0xff;content=0;probe_ok=0;
 assert(!mds_cart_open(&g));assert(reset_count==0&&probes==1);
 reset();marker='X';content=2;
 assert(!mds_cart_open(&g));assert(reset_count==0);
 reset();read_ok=0;
 assert(!mds_cart_open(&g));assert(loads==0&&probes==0);
 reset();memcpy(header.gameCode,"FAIL",4);
 assert(!mds_cart_open(&g));assert(read_count==0);
 puts("PASS: readable valid 64K/8K saves load without WREN; unknown data never initialized");
 return 0;
}
