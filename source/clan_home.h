#ifndef MDS_CLAN_HOME_H
#define MDS_CLAN_HOME_H
#include <stdint.h>
/* Adapt original 3DS PlazaTop_Select pane-Y keys to a small DS outline cue.
 * This is NOT a full original CLYT pane compositor. */
int mds_clan_home_offset(int focus,uint32_t now,uint32_t started);
int mds_clan_home_running(uint32_t now,uint32_t started);
#endif
