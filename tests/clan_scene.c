#include "clan_scene.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 assert(mds_clan_scene_duration("Plaza.arc.files","PlazaTop_Select",99)==10);
 assert(mds_clan_scene_duration("Plaza.arc.files","PlazaTop_Unselect",99)==10);
 assert(mds_clan_scene_duration("Editor.arc.files","EditAutoPhoto_Up_SceneIn",99)==22);
 assert(mds_clan_scene_duration("Editor.arc.files","EditAutoPhoto_Up_SceneOut",99)==22);
 assert(mds_clan_scene_duration("Plaza.arc.files","Missing",7)==7);
 assert(mds_clan_scene_duration(NULL,"PlazaTop_Select",7)==7);
 assert(mds_clan_scene_duration("Plaza.arc.files",NULL,7)==7);
 puts("PASS: original CLAN frame-count timing and unknown-clip fallback");
 return 0;
}
