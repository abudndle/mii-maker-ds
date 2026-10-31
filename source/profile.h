#ifndef MDS_PROFILE_H
#define MDS_PROFILE_H
#include "avatar.h"
typedef enum {MDS_PROFILE_ROOT,MDS_PROFILE_NAME,MDS_PROFILE_CREATOR,MDS_PROFILE_GENDER,MDS_PROFILE_COLOR,MDS_PROFILE_BIRTHDAY,MDS_PROFILE_SHARING,MDS_PROFILE_COPYING} MdsProfileMode;
typedef struct {int mode,upper,month,day,choice;char text[MDS_NAME];const char *status;int focus,key_row,key_column;} MdsProfile;
const char *mds_profile_hit(unsigned,int,int);
int mds_profile_touch(MdsProfile *,MdsAvatar *,int,int,unsigned);
void mds_profile_choice_step(MdsProfile *,int);
void mds_profile_begin(MdsProfile *);
void mds_profile_open(MdsProfile *,const MdsAvatar *,int);
int mds_profile_append(MdsProfile *,unsigned);
void mds_profile_backspace(MdsProfile *);
int mds_profile_done(MdsProfile *,MdsAvatar *);
void mds_profile_cancel(MdsProfile *);
int mds_profile_date_valid(unsigned,unsigned);
int mds_profile_name_valid(const char *,int);
void mds_profile_date_step(MdsProfile *,int,int);
int mds_profile_favorite(MdsAvatar *,unsigned);
void mds_profile_move(MdsProfile *,int horizontal,int vertical);
int mds_profile_activate(MdsProfile *,MdsAvatar *,unsigned favorites);
const char *mds_profile_key_row(unsigned);
int mds_profile_focus_rect(const MdsProfile *,int *x,int *y,int *w,int *h);
#endif
