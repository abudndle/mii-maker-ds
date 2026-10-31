#ifndef MDS_CLAN_HOME_H
#define MDS_CLAN_HOME_H
#include <stdint.h>
/* Original PlazaTop_Select Y/color/opacity properties adapted to DS outline.
 * This is not a complete CLYT pane renderer. */
typedef struct {
 int offset_y;
 uint16_t color_rgb555;
 uint8_t alpha;
 uint8_t shadow_alpha;
} MdsClanHomeStyle;
int mds_clan_home_running(uint32_t now,uint32_t started);
int mds_clan_home_offset(int focus,uint32_t now,uint32_t started);
int mds_clan_home_style(int focus,uint32_t now,uint32_t started,MdsClanHomeStyle *out);
#endif
