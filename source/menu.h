#ifndef MDS_MENU_H
#define MDS_MENU_H
typedef enum {MDS_SCREEN_HOME,MDS_SCREEN_EDITOR,MDS_SCREEN_GALLERY,MDS_SCREEN_PROFILE,MDS_SCREEN_GENDER,MDS_SCREEN_ACCESSORIES} MdsScreen;
typedef enum {MDS_HOME_NONE,MDS_HOME_VIEW,MDS_HOME_CREATE,MDS_HOME_TRANSFER,MDS_HOME_QR,MDS_HOME_HELP} MdsHomeAction;
int mds_home_touch(int,int);
int mds_gallery_touch(int,int,unsigned);
int mds_home_focus_step(int,int);
#endif
