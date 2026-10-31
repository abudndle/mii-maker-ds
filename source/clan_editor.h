#ifndef MDS_CLAN_EDITOR_H
#define MDS_CLAN_EDITOR_H
#include <stdint.h>
#define MDS_CLAN_EDITOR_TAB_TICKS 2u
#define MDS_CLAN_EDITOR_PART_TICKS 10u
/* Original EditorCommon_Select RGB and EditFace/Hair_Select scaling
 * adapted to DS bitmap widgets, not full original CLYT composition. */
typedef struct {
 uint32_t started;
 unsigned category, tab, selected;
 unsigned duration;
 uint8_t active, painted, tab_changed;
} MdsClanEditorAnim;
typedef struct {
 int32_t part_scale_q16;
 uint16_t tab_pane_rgb555, tab_icon_rgb555;
 uint8_t tab_active;
} MdsClanEditorStyle;
unsigned mds_clan_editor_tab(unsigned category);
void mds_clan_editor_begin(MdsClanEditorAnim *,uint32_t now,
                           unsigned category,unsigned part,int tab_changed);
int mds_clan_editor_tick(MdsClanEditorAnim *,uint32_t now);
int mds_clan_editor_style(MdsClanEditorAnim *,uint32_t now,MdsClanEditorStyle *);
#endif
