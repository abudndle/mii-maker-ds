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
void mds_gallery_controls_reset(MdsGalleryControls *controls);
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
typedef struct { MdsGalleryTouchAction pressed; } MdsGalleryActionPress;
void mds_gallery_action_press_reset(MdsGalleryActionPress *gesture);
void mds_gallery_action_press_begin(MdsGalleryActionPress *gesture,
                                    MdsGalleryTouchAction action);
void mds_gallery_action_press_hold(MdsGalleryActionPress *gesture,int x,int y);
MdsGalleryTouchAction mds_gallery_action_press_release(
    MdsGalleryActionPress *gesture,int x,int y);
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
/* Iterate the cartridge's 100-slot save gallery without file selection. */
int mds_gallery_next_saved(const unsigned char *used,unsigned current,int direction);
int mds_home_focus_step(int,int);
#endif
