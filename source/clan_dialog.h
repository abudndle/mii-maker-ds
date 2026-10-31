#ifndef MDS_CLAN_DIALOG_H
#define MDS_CLAN_DIALOG_H
#include <stdint.h>
/* Three source-derived 21-frame clips at provisional 30fps on 60Hz DS.
 * Only W_Dialog pane Y is adapted; full CLYT composition is pending. */
#define MDS_CLAN_DIALOG_VBLANKS 40u
int mds_clan_dialog_active(uint32_t now,uint32_t started);
int mds_clan_dialog_y(uint32_t now,uint32_t started);
int mds_clan_dialog_exit_y(uint32_t now,uint32_t started,int up);
/* Translate a 256x192 RGB555 bitmap safely in-place. */
void mds_clan_dialog_translate(uint16_t *screen,int offset,uint16_t background);
#endif
