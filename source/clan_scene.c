#include "clan_scene.h"
#include <string.h>
/* Source-derived CLAN clip frame counts; no copyrighted animation payload.
 * Only timing is used. Curves and widget positions are NOT ported here. */
typedef struct {const char *archive,*clip;unsigned frames;} MdsSceneClip;
static const MdsSceneClip clips[]={
 {"Plaza.arc.files","PlazaTop_Select",6},
 {"Plaza.arc.files","PlazaTop_Unselect",6},
 {"Editor.arc.files","EditAutoPhoto_Up_SceneIn",12},
 {"Editor.arc.files","EditAutoPhoto_Up_SceneOut",12}
};
unsigned mds_clan_scene_duration(const char *archive,const char *clip,unsigned fallback)
{
 if(!archive||!clip)return fallback;
 for(unsigned i=0;i<sizeof clips/sizeof clips[0];i++)
  if(!strcmp(archive,clips[i].archive)&&!strcmp(clip,clips[i].clip)){
   unsigned frames=clips[i].frames;
   /* Two DS VBlanks per source frame: provisional 30 fps. */
   return (frames-1u)*2u;
  }
 return fallback;
}
