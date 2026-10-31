#ifndef MDS_CLAN_DIALOG_H
#define MDS_CLAN_DIALOG_H
#include <stdint.h>
/* Original DialogBase00_DialogIn: 21 source frames at provisional 30 fps
 * on a 60-Hz DS VBlank clock. This adapts only the W_Dialog Y property. */
#define MDS_CLAN_DIALOG_VBLANKS 40u
int mds_clan_dialog_active(uint32_t now,uint32_t started);
int mds_clan_dialog_y(uint32_t now,uint32_t started);
/* In-place clipped vertical translation of RGB555 256x192 screen. */
void mds_clan_dialog_translate(uint16_t *screen,int offset,uint16_t background);
#endif
