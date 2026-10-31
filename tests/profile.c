#include "profile.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void){
 MdsAvatar a;mds_new(&a);MdsProfile p;mds_profile_begin(&p);
 assert(!strcmp(mds_profile_hit(0,80,29),"B_Nickname"));mds_profile_touch(&p,&a,80,29,0);assert(p.mode==MDS_PROFILE_NAME);
 memset(p.text,0,sizeof p.text);for(unsigned i=0;i<10;i++)assert(mds_profile_append(&p,'A'+i));assert(!mds_profile_append(&p,'K'));assert(mds_profile_done(&p,&a)&&!strcmp(a.name,"ABCDEFGHIJ"));
 mds_profile_open(&p,&a,MDS_PROFILE_NAME);mds_profile_backspace(&p);mds_profile_cancel(&p);assert(!strcmp(a.name,"ABCDEFGHIJ"));
 assert(!mds_profile_name_valid("",0)&&mds_profile_name_valid("",1));assert(!mds_profile_name_valid("   ",0));assert(!mds_profile_name_valid("bad\n",1));assert(!mds_profile_name_valid("\xc0\xaf",0));
 const char *unicode="\xe6\x97\xa5\xe6\x9c\xac\xf0\x9f\x98\x80";assert(mds_profile_name_valid(unicode,0));
 mds_profile_open(&p,&a,MDS_PROFILE_NAME);strcpy(p.text,unicode);mds_profile_backspace(&p);assert(!strcmp(p.text,"\xe6\x97\xa5\xe6\x9c\xac"));assert(mds_profile_done(&p,&a));
 assert(mds_profile_date_valid(2,29)&&!mds_profile_date_valid(2,30)&&!mds_profile_date_valid(4,31)&&mds_profile_date_valid(0,0)&&!mds_profile_date_valid(0,1));
 mds_profile_open(&p,&a,MDS_PROFILE_BIRTHDAY);p.month=1;p.day=31;mds_profile_date_step(&p,1,1);assert(p.month==2&&p.day==29);assert(mds_profile_done(&p,&a)&&a.value[49]==2&&a.value[50]==29);
 mds_profile_open(&p,&a,MDS_PROFILE_BIRTHDAY);p.month=4;p.day=31;assert(!mds_profile_done(&p,&a));mds_profile_cancel(&p);
 mds_profile_open(&p,&a,MDS_PROFILE_GENDER);p.choice=1;assert(mds_profile_done(&p,&a)&&a.value[0]==1);
 mds_profile_open(&p,&a,MDS_PROFILE_SHARING);p.choice=0;mds_profile_cancel(&p);assert(a.value[47]==1);
 mds_profile_open(&p,&a,MDS_PROFILE_SHARING);mds_profile_touch(&p,&a,128,147,0);assert(a.value[47]==0&&p.mode==MDS_PROFILE_ROOT);
 mds_profile_open(&p,&a,MDS_PROFILE_COPYING);mds_profile_touch(&p,&a,128,147,0);assert(a.value[48]==0);
 assert(!mds_profile_favorite(&a,10)&&a.value[46]==0);assert(mds_profile_favorite(&a,9)&&a.value[46]==1);assert(mds_profile_favorite(&a,10)&&a.value[46]==0);
 assert(!strcmp(mds_profile_hit(7,128,87),"B_BtnCommon_00"));assert(!strcmp(mds_profile_hit(7,128,127),"B_BtnCommon_01"));
 assert(!strcmp(mds_profile_hit(8,128,32),"B_Beard"));
 puts("PASS: original profile bounds, keyboard limits/UTF-8/backspace/cancel, gender, birthday validation, permissions and favorite limit");
}
