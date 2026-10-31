/* Host-side preflight for an independently supplied original CFL_Res.dat. */
#include "cfl_resource.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv)
{
    if(argc!=2){fprintf(stderr,"usage: cfl_inspect CFL_Res.dat\n");return 2;}
    FILE *f=fopen(argv[1],"rb");if(!f){perror(argv[1]);return 2;}
    if(fseek(f,0,SEEK_END)){fclose(f);return 2;}
    long n=ftell(f);if(n<84||n>16*1024*1024){fprintf(stderr,"unsupported archive length\n");fclose(f);return 1;}
    rewind(f);unsigned char *bytes=malloc((size_t)n);if(!bytes){fclose(f);return 2;}
    size_t got=fread(bytes,1,(size_t)n,f);fclose(f);MdsCflArchive a;
    if(got!=(size_t)n||!mds_cfl_open(&a,bytes,got)){fprintf(stderr,"invalid CFL archive structure\n");free(bytes);return 1;}
    puts("{\"sections\":[");
    for(unsigned s=0;s<20;s++){
        unsigned count=mds_cfl_count(&a,s),items=0,meshes=0,textures=0;
        for(unsigned i=0;i<count;i++){
            MdsCflItem item;if(!mds_cfl_item(&a,s,i,&item))continue;items++;
            if(s<9){MdsCflGeometry g;if(mds_cfl_geometry(&item,&g))meshes++;}
            else{MdsCflTexture t;if(mds_cfl_texture(&item,&t))textures++;}
        }
        printf("{\"id\":%u,\"name\":\"%s\",\"declared_items\":%u,\"readable_items\":%u,\"geometry_headers\":%u,\"texture_headers\":%u}%s\n",s,mds_cfl_section_name(s),count,items,meshes,textures,s==19?"":",");
    }
    puts("]}");free(bytes);return 0;
}
