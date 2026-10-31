#include "cfl_resource.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static uint8_t bytes[4096];
static void w16(size_t at,unsigned v){bytes[at]=(uint8_t)v;bytes[at+1]=(uint8_t)(v>>8);}
static void w32(size_t at,unsigned v){w16(at,v);w16(at+2,v>>16);}
int main(void)
{
    w16(0,20);unsigned off=84;
    for(unsigned i=0;i<20;i++){w32(4+i*4,off);off+=i==2?128:8;}
    size_t s=100;w16(s,2);w32(s+4,0);w32(s+8,(1u<<22)|80);w32(s+12,64);
    size_t g=s+16+36;w16(g,3);w16(g+2,0);w16(g+4,0);w16(g+6,1);
    w16(g+8,256);w16(g+10,512);w16(g+12,0xff00);w16(g+26,0);w16(g+28,3);bytes[g+30]=0;bytes[g+31]=1;bytes[g+32]=2;
    /* item end must cover the complete geometry stream */
    w32(s+12,80);
    MdsCflArchive a;assert(mds_cfl_open(&a,bytes,off));assert(mds_cfl_count(&a,2)==2);
    MdsCflItem item;assert(mds_cfl_item(&a,2,0,&item));assert(item.size==80);MdsCflItem redirected;assert(mds_cfl_item(&a,2,1,&redirected));assert(redirected.data==item.data);
    MdsCflGeometry geom;assert(mds_cfl_geometry(&item,&geom));float p[3],n[3],uv[2];assert(mds_cfl_vertex(&geom,0,p,n,uv));assert(p[0]==1&&p[1]==2&&p[2]==-1&&n[2]==1);
    bytes[g+32]=3;assert(!mds_cfl_geometry(&item,&geom));bytes[g+32]=2;
    w32(s+4,2u<<22);assert(!mds_cfl_item(&a,2,0,&item));w32(s+4,0);
    w32(s+8,3u<<22);assert(!mds_cfl_item(&a,2,1,&item));w32(s+8,(1u<<22)|80);
    assert(!mds_cfl_item(&a,20,0,&item));assert(!mds_cfl_item(&a,2,2,&item));
    for(unsigned i=0;i<off;i++)assert(!mds_cfl_open(&a,bytes,i));
    uint8_t tex[40]={2,0,2,0,1,0,0,0};MdsCflItem ti={tex,sizeof tex,10,0};MdsCflTexture t;assert(mds_cfl_texture(&ti,&t)&&t.pixel_bytes==2);ti.size=9;assert(!mds_cfl_texture(&ti,&t));
    puts("PASS: CFL synthetic section bounds, aliases, cycles, geometry, fixed point, indices, textures, truncation");
}
