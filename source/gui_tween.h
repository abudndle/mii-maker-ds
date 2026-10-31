#ifndef MDS_GUI_TWEEN_H
#define MDS_GUI_TWEEN_H
#include <stdint.h>
typedef struct {
 uint32_t started;
 uint16_t duration;
 int16_t from,to;
 uint8_t active;
} MdsGuiTween;
/* All times are 60 Hz VBlank ticks; no floating point or heap required. */
void mds_gui_tween_start(MdsGuiTween *,uint32_t now,uint16_t duration,int16_t from,int16_t to);
int16_t mds_gui_tween_value(const MdsGuiTween *,uint32_t now);
int mds_gui_tween_done(const MdsGuiTween *,uint32_t now);
/* Preserve RGB555 opacity bit while scaling channels with 0..16 brightness. */
uint16_t mds_gui_fade_rgb555(uint16_t pixel,unsigned brightness);
#endif
