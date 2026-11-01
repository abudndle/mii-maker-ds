#ifndef MDS_UI_H
#define MDS_UI_H
#include "avatar.h"
#include "save.h"
#include "profile.h"
#include "exchange.h"
int mds_ui_init(void);
void mds_ui_qr_reset(void);
void mds_ui_qr(const MdsAvatar *,const char *,int,int);
int mds_ui_qr_touch(int,int,int,int);
const char *mds_ui_qr_export(const MdsAvatar *,unsigned,int);
void mds_ui_import_open(MdsImport *);
void mds_ui_import(const MdsImport *);
void mds_ui_present_top(void);
void mds_ui_home_focus_start(uint32_t now);
int mds_ui_home_focus_tick(uint32_t now);
void mds_ui_profile_transition_start(uint32_t now);
void mds_ui_profile_transition_exit(uint32_t now,int up);
int mds_ui_profile_transition_active(void);
int mds_ui_profile_transition_tick(uint32_t now);
void mds_ui_scene_transition_start(uint32_t now);
void mds_ui_scene_transition_cancel(void);
int mds_ui_scene_transition_step(uint32_t now,int redraw);
void mds_ui_set_render_clock(uint32_t (*)(void));
void mds_ui_set_render_abort(int (*)(void));
const char *mds_ui_export_image(const MdsAvatar *,unsigned);
int mds_ui_animation_tick(uint32_t);
void mds_ui_motion_scene(int);
/* Original 3DS L/R camera rotation in editor; gallery remains front-facing. */
void mds_ui_view_scene(int editing);
int mds_ui_view_step(int direction);
/* Gallery: cycle original clips; START restores six-idle automatic playback. */
int mds_ui_motion_step(int direction);
int mds_ui_motion_auto(void);
void mds_ui_room_recall(void);
void mds_ui_gallery_drag(int slot,int x,int y);
/* Move the floating actor on the BOTTOM VRAM screen without a full redraw. */
void mds_ui_gallery_drag_follow(int x,int y);
/* Original 3DS CLAN feedback: call each VBlank; redraw only for active frames. */
void mds_ui_gallery_clan_reset(void);
int mds_ui_gallery_actions_visible(uint32_t now);
int mds_ui_gallery_clan_tick(unsigned page,unsigned selected,uint32_t now);
/* Actual original EDITSelectBase ScrollL/ScrollR and SelectMii Decide
 * channel feedback; UI resource bytes are supplied only in private NitroFS. */
void mds_ui_gallery_navigation(int direction,uint32_t now);
void mds_ui_gallery_confirm(uint32_t now);
void mds_ui_gallery_invalid(int direction);
void mds_ui_gallery_top(const MdsGallery *,unsigned,unsigned,const char *);
void mds_ui_profile(const MdsProfile *,const MdsAvatar *);
void mds_ui_gender(int,int);
void mds_ui_accessories(void);
void mds_ui_confirm(const char *);
/* 3DS DialogBase02 original 21-frame W_Dialog entrance; input remains
 * anchored to its static original CLYT positions while moving visually. */
void mds_ui_confirm_reset(void);
/* Source DialogBase02_DialogOut or DialogOutUp, input locked on exit. */
int mds_ui_confirm_request_exit(int up);
int mds_ui_confirm_choose(int yes,uint32_t now);
int mds_ui_confirm_exit_done(uint32_t now);
int mds_ui_confirm_touch_ready(uint32_t now);
int mds_ui_confirm_animation_tick(uint32_t now);
int mds_ui_confirm_touch(int,int);
void mds_ui_editor_selection_update(uint32_t now,const MdsAvatar *,int field,int editing);
int mds_ui_editor_selection_tick(uint32_t now);
void mds_ui_editor_adjust_key(uint32_t now,int field,int direction);
void mds_ui_editor_adjust_invalid_key(uint32_t now,int field,int direction);
void mds_ui_editor_adjust_release(uint32_t now,int released);
int mds_ui_editor_adjust_tick(uint32_t now);
void mds_ui_draw(const MdsAvatar *a,int field);
int mds_ui_slider_active(void);
int mds_ui_slider_move(MdsAvatar *,int);
void mds_ui_slider_release(void);
int mds_ui_touch(MdsAvatar *a,int *field,int x,int y);
void mds_ui_info(const MdsAvatar *,unsigned,int,const char *,int);
void mds_ui_camera(const uint16_t *);
void mds_ui_camera_notice(const char *);
void mds_ui_restore_top(void);
void mds_ui_home(int,const char *);
void mds_ui_gallery(const MdsGallery *,unsigned,unsigned,const char *);
void mds_ui_saved(const MdsGallery *,unsigned,unsigned);
/* An interrupted slow thumbnail render should be retried once input is idle. */
int mds_ui_gallery_retry_pending(void);
#endif
