#include "clan_scene.h"
#include "clan_catalog_generated.h"
#include <string.h>
unsigned mds_clan_scene_duration(const char *archive,const char *clip,unsigned fallback)
{
 if(!archive||!clip)return fallback;
 for(unsigned i=0;i<MDS_CLAN_CLIP_COUNT;i++){
  const MdsClanClip *c=&mds_clan_clips[i];
  if(!strcmp(c->archive,archive)&&!strcmp(c->name,clip)){
   /* Last source frame is shown at two DS VBlanks per frame. */
   unsigned ticks=(unsigned)(c->frames>1?c->frames-1u:1u)*2u;
   return ticks>65535u?65535u:ticks;
  }
 }
 return fallback;
}
