#ifndef MDS_MENU_H
#define MDS_MENU_H
typedef enum {MDS_SCREEN_HOME,MDS_SCREEN_EDITOR,MDS_SCREEN_GALLERY,MDS_SCREEN_PROFILE,MDS_SCREEN_GENDER,MDS_SCREEN_ACCESSORIES,MDS_SCREEN_IMPORT,MDS_SCREEN_QR,MDS_SCREEN_SAVED,MDS_SCREEN_BACKUP,MDS_SCREEN_BACKUP_BROWSE,MDS_SCREEN_BACKUP_CONFIRM} MdsScreen;
typedef enum {MDS_HOME_NONE,MDS_HOME_VIEW,MDS_HOME_CREATE,MDS_HOME_TRANSFER,MDS_HOME_QR,MDS_HOME_HELP} MdsHomeAction;
int mds_home_touch(int,int);
int mds_gallery_touch(int,int,unsigned);
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
/* Iterate the cartridge's 100-slot save gallery without file selection. */
int mds_gallery_next_saved(const unsigned char *used,unsigned current,int direction);
int mds_home_focus_step(int,int);
#endif
