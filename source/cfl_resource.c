/* Independently authored reader using format observations in jamesrhg/cfl-mii,
 * commit b85be4d66e9c89d203840cbe7fa0f638a44cdde2. No Nintendo artwork or
 * upstream implementation is embedded. The supplied original archive is now exercised by host and DS renderer tests;
 * synthetic tests also exercise bounds and layout rules.
 */
#include "cfl_resource.h"
#include <string.h>
static unsigned u16(const uint8_t *p){return p[0]|(unsigned)p[1]<<8;}
static uint32_t u32(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static float fixed(const uint8_t *p,float scale){unsigned v=u16(p);int s=v>=32768?(int)v-65536:(int)v;return s/scale;}
static size_t section_end(const MdsCflArchive *a,unsigned s)
{
    size_t start=u32(a->data+4+s*4),end=a->size;
    for(unsigned i=0;i<MDS_CFL_SECTIONS;i++){size_t off=u32(a->data+4+i*4);if(off>start&&off<end)end=off;}
    return end;
}
int mds_cfl_open(MdsCflArchive *out,const void *bytes,size_t size)
{
    if(!out||!bytes||size<84||u16(bytes)!=20)return 0;
    MdsCflArchive a={(const uint8_t *)bytes,size};
    for(unsigned s=0;s<MDS_CFL_SECTIONS;s++){
        size_t off=u32(a.data+4+s*4);
        if(off<84||off>size||size-off<8)return 0;
    }
    for(unsigned s=0;s<MDS_CFL_SECTIONS;s++){
        size_t off=u32(a.data+4+s*4),end=section_end(&a,s);
        size_t count=u16(a.data+off),table=4+(count+1)*4;
        if(table>end-off)return 0;
    }
    *out=a;return 1;
}
unsigned mds_cfl_count(const MdsCflArchive *a,unsigned section)
{
    if(!a||!a->data||section>=20)return 0;
    return u16(a->data+u32(a->data+4+section*4));
}
int mds_cfl_item(const MdsCflArchive *a,unsigned section,unsigned item,MdsCflItem *out)
{
    if(!a||!a->data||!out||section>=20)return 0;
    size_t off=u32(a->data+4+section*4),end=section_end(a,section);
    unsigned count=u16(a->data+off),index=item;
    if(index>=count)return 0;
    const uint8_t *table=a->data+off+4;
    uint32_t entry=0;
    unsigned hops=0;
    for(;;){
        entry=u32(table+index*4);unsigned redirect=entry>>22;
        if(!redirect)break;
        if(redirect>count||++hops>count)return 0;
        index=redirect-1;
    }
    size_t start=entry&0x3fffffu,stop=u32(table+(index+1)*4)&0x3fffffu;
    size_t payload=off+4+(count+1)*4;
    if(stop<=start||start>end-payload||stop>end-payload)return 0;
    MdsCflItem result={a->data+payload+start,stop-start,section,item};*out=result;return 1;
}
int mds_cfl_geometry(const MdsCflItem *item,MdsCflGeometry *out)
{
    if(!item||!item->data||!out)return 0;
    size_t prefix=item->section==2?36:item->section==5?72:0;
    if(item->size<prefix+8)return 0;
    const uint8_t *p=item->data+prefix;size_t left=item->size-prefix;
    unsigned c=u16(p),n=u16(p+2),t=u16(p+4),indexed=u16(p+6);
    if(c<3||c>4096||(n!=0&&n!=1&&n!=c)||(t!=0&&t!=1&&t!=c)||indexed>1)return 0;
    MdsCflGeometry g={0};g.count=c;g.normals=n;g.texcoords=t;g.stride=6+(n==c?6:0)+(t==c?4:0);g.vertices=p+8;
    size_t used=8+(size_t)c*g.stride;
    if(used>left)return 0;
    if(n==1){if(left-used<6)return 0;g.common_normal=p+used;used+=6;}
    if(t==1){if(left-used<4)return 0;g.common_uv=p+used;used+=4;}
    if(indexed){
        if(left-used<4)return 0;
        g.index_count=u16(p+used+2);used+=4;
        if(g.index_count>left-used)return 0;
        g.indices=p+used;
        for(unsigned i=0;i<g.index_count;i++)if(g.indices[i]>=c)return 0;
    }
    *out=g;return 1;
}
int mds_cfl_vertex(const MdsCflGeometry *g,unsigned i,float pos[3],float normal[3],float uv[2])
{
    if(!g||!g->vertices||i>=g->count||!pos||!normal||!uv)return 0;
    const uint8_t *p=g->vertices+(size_t)i*g->stride;
    for(unsigned j=0;j<3;j++)pos[j]=fixed(p+j*2,256.0f);
    p+=6;
    const uint8_t *n=g->normals==g->count?p:g->common_normal;
    for(unsigned j=0;j<3;j++)normal[j]=n?fixed(n+j*2,256.0f):(j==2?1.0f:0.0f);
    if(g->normals==g->count)p+=6;
    const uint8_t *t=g->texcoords==g->count?p:g->common_uv;
    for(unsigned j=0;j<2;j++)uv[j]=t?fixed(t+j*2,8192.0f):0;
    return 1;
}
int mds_cfl_texture(const MdsCflItem *item,MdsCflTexture *out)
{
    static const unsigned bits[]={4,8,4,8,8,16,16,16,24,16,16,32,4,8};
    if(!item||!item->data||!out||item->size<8)return 0;
    const uint8_t *p=item->data;unsigned w=u16(p),h=u16(p+2),format=p[5];
    if(!w||!h||w>4096||h>4096||format>=14)return 0;
    unsigned pw=1,ph=1;while(pw<w)pw*=2;while(ph<h)ph*=2;
    size_t n=((size_t)pw*ph*bits[format]+7)/8;
    if(n>item->size-8)return 0;
    MdsCflTexture t={w,h,pw,ph,format,p[4],p[6],p[7],p+8,n};*out=t;return 1;
}
const char *mds_cfl_section_name(unsigned s)
{
    static const char *names[]={"goatee","cap","face","forehead","glasses","hair","mask","noseline","nose","cap_texture","eye","eyebrow","face_beard","face_lines","face_makeup","glasses_texture","mole","mouth","mustache","noseline_texture"};
    return s<20?names[s]:"invalid";
}
