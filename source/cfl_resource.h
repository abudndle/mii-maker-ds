#ifndef MDS_CFL_RESOURCE_H
#define MDS_CFL_RESOURCE_H
#include <stddef.h>
#include <stdint.h>
#define MDS_CFL_SECTIONS 20u
/* Portable archive views; caller owns the backing bytes. No 3DS filesystem/GPU APIs. */
typedef struct {const uint8_t *data;size_t size;} MdsCflArchive;
typedef struct {const uint8_t *data;size_t size;unsigned section,item;} MdsCflItem;
typedef struct {const uint8_t *vertices,*common_normal,*common_uv,*indices;unsigned count,normals,texcoords,stride,index_count;} MdsCflGeometry;
typedef struct {unsigned width,height,padded_width,padded_height,format,mipmaps,wrap_u,wrap_v;const uint8_t *pixels;size_t pixel_bytes;} MdsCflTexture;
int mds_cfl_open(MdsCflArchive *,const void *,size_t);
unsigned mds_cfl_count(const MdsCflArchive *,unsigned);
int mds_cfl_item(const MdsCflArchive *,unsigned,unsigned,MdsCflItem *);
int mds_cfl_geometry(const MdsCflItem *,MdsCflGeometry *);
int mds_cfl_vertex(const MdsCflGeometry *,unsigned,float[3],float[3],float[2]);
int mds_cfl_texture(const MdsCflItem *,MdsCflTexture *);
const char *mds_cfl_section_name(unsigned);
#endif
