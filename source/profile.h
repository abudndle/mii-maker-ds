#ifndef MDS_PROFILE_H
#define MDS_PROFILE_H
#include "avatar.h"
typedef enum {MDS_PROFILE_ROOT,MDS_PROFILE_NAME,MDS_PROFILE_CREATOR,MDS_PROFILE_GENDER,MDS_PROFILE_COLOR,MDS_PROFILE_BIRTHDAY,MDS_PROFILE_SHARING,MDS_PROFILE_COPYING} MdsProfileMode;
typedef struct {int mode,upper,month,day,choice;char text[MDS_NAME];const char *status;} MdsProfile;
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
#endif
