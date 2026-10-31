#ifndef MDS_CLAN_SCENE_H
#define MDS_CLAN_SCENE_H
#include <stdint.h>
/* Original clip metadata drives timing only. Visual CLAN curves are pending. */
unsigned mds_clan_scene_duration(const char *archive,const char *clip,unsigned fallback);
#endif
