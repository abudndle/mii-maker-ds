#ifndef MDS_MENU_H
#define MDS_MENU_H
typedef enum {MDS_SCREEN_HOME,MDS_SCREEN_EDITOR,MDS_SCREEN_GALLERY,MDS_SCREEN_PROFILE,MDS_SCREEN_GENDER,MDS_SCREEN_ACCESSORIES,MDS_SCREEN_IMPORT,MDS_SCREEN_QR,MDS_SCREEN_SAVED} MdsScreen;
typedef enum {MDS_HOME_NONE,MDS_HOME_VIEW,MDS_HOME_CREATE,MDS_HOME_TRANSFER,MDS_HOME_QR,MDS_HOME_HELP} MdsHomeAction;
/* Gallery A recalls walkers; SELECT+A edits the selected Mii.
 * A plain SELECT release exports its image without firing during a chord. */
typedef enum {
 MDS_GALLERY_CONTROL_NONE=0,
 MDS_GALLERY_CONTROL_RECALL=1,
 MDS_GALLERY_CONTROL_EDIT=2,
 MDS_GALLERY_CONTROL_EXPORT=4
} MdsGalleryControlAction;
typedef struct { unsigned char select_used,select_active; } MdsGalleryControls;
/* A recall, edit or export excludes same-frame copy/delete/favorite. */
int mds_gallery_controls_secondary_allowed(unsigned primary_action);
void mds_gallery_controls_reset(MdsGalleryControls *controls);
/* Any stylus interaction while SELECT is active consumes standalone export,
 * including box selection, room navigation and drags (not only balloon taps). */
void mds_gallery_controls_consume_touch(MdsGalleryControls *controls,int touch_active);
/* Other physical gallery keys used during a SELECT chord consume its image
 * export, including a key edge simultaneous with SELECT release. */
unsigned mds_gallery_controls_consume_physical(MdsGalleryControls *controls,
    unsigned action,int other_key_active);
unsigned mds_gallery_controls_step(MdsGalleryControls *controls,
 int a_down,int a_held,int select_down,int select_held,int select_up);
int mds_home_touch(int,int);
int mds_gallery_touch(int,int,unsigned);
/* Temporary accessible touch actions below the original ten-box grid.
 * The authentic SelectBalloonButton art and layout still require the private
 * source pane transform; these bounds must never overlap a box or arrow. */
typedef enum {
 MDS_GALLERY_ACTION_NONE=0,
 MDS_GALLERY_ACTION_FAVORITE=1,
 MDS_GALLERY_ACTION_COPY=2,
 MDS_GALLERY_ACTION_EDIT=3
} MdsGalleryTouchAction;
MdsGalleryTouchAction mds_gallery_action_touch(int x,int y);
/* An action activates only on release over its original pressed button.
 * Leaving its bounds cancels; sliding back does not re-arm the action. */
typedef struct { MdsGalleryTouchAction pressed; int target_slot; } MdsGalleryActionPress;
void mds_gallery_action_press_reset(MdsGalleryActionPress *gesture);
/* A physical button's press OR release cancels a pending stylus command. */
void mds_gallery_action_press_cancel_for_physical(
    MdsGalleryActionPress *gesture,int physical_down,int physical_up);
/* A key already held before stylus-down has no new edge; it still must
 * prevent a concurrent Favorite/Copy/Edit touch transaction. */
void mds_gallery_action_press_cancel_for_held(
    MdsGalleryActionPress *gesture,int physical_held);
/* SELECT-up must not export an image while a touch gesture is in progress. */
unsigned mds_gallery_controls_suppress_export_on_touch(
    unsigned action,int touch_active);
void mds_gallery_action_press_begin(MdsGalleryActionPress *gesture,
                                    MdsGalleryTouchAction action);
/* Bind the selected save slot at stylus-down: delayed release must not act
 * on a different Mii after an intervening selection or room transition. */
void mds_gallery_action_press_bind_slot(MdsGalleryActionPress *gesture,unsigned slot);
void mds_gallery_action_press_hold(MdsGalleryActionPress *gesture,int x,int y);
MdsGalleryTouchAction mds_gallery_action_press_release(
    MdsGalleryActionPress *gesture,int x,int y);
/* Release is also gated on the current source balloon's visibility. */
MdsGalleryTouchAction mds_gallery_action_press_release_for_slot(
    MdsGalleryActionPress *gesture,int x,int y,unsigned slot,int visible);
/* All ten boxes are selectable; only occupied boxes can begin a drag. */
typedef enum {
 MDS_GALLERY_BOX_NONE=0,
 MDS_GALLERY_BOX_SELECT=1,
 MDS_GALLERY_BOX_DRAG=2
} MdsGalleryBoxAction;
MdsGalleryBoxAction mds_gallery_box_press(int slot,int occupied);
/* Room tabs from original EDITSelectBase, independent of Mii destination boxes. */
int mds_gallery_room_touch(int x,int y);
/* Touchscreen room navigation: -1 left, +1 right, 0 elsewhere. */
int mds_gallery_room_arrow(int x,int y,unsigned page);
int mds_gallery_slot_step(unsigned page,unsigned selected,int direction);
/* Move to the next ten-slot page without losing the cursor position. */
int mds_gallery_page_step(unsigned page,unsigned selected,int direction);
/* Drag gesture retains its source in global 0..99 slot space across rooms. */
typedef struct { int source; } MdsGalleryDrag;
void mds_gallery_drag_reset(MdsGalleryDrag *drag);
int mds_gallery_drag_begin(MdsGalleryDrag *drag,unsigned page,int source,int occupied);
int mds_gallery_drag_end(MdsGalleryDrag *drag,unsigned page,int destination,unsigned *source);
/* Physical gallery commands are ignored throughout a stylus drag, including
 * the release event where drag_end has already cleared the source. */
int mds_gallery_drag_blocks_actions(int was_dragging,int dragging);
/* Cancel all gallery input state atomically before returning Home. */
void mds_gallery_cancel_for_exit(MdsGalleryDrag *drag,
    MdsGalleryControls *controls,MdsGalleryActionPress *press,int *arrow_latch);
/* Iterate the cartridge's 100-slot save gallery without file selection. */
int mds_gallery_next_saved(const unsigned char *used,unsigned current,int direction);
int mds_home_focus_step(int,int);
#endif
