#include "profile.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void controller(void)
{
 MdsProfile p;MdsAvatar a;mds_new(&a);mds_profile_begin(&p);
 const int modes[]={MDS_PROFILE_NAME,MDS_PROFILE_ROOT,MDS_PROFILE_GENDER,MDS_PROFILE_SHARING,MDS_PROFILE_COLOR,MDS_PROFILE_COPYING,MDS_PROFILE_BIRTHDAY,MDS_PROFILE_CREATOR};
 for(int focus=0;focus<10;focus++){
  mds_profile_begin(&p);p.focus=focus;
  int x,y,w,h;assert(mds_profile_focus_rect(&p,&x,&y,&w,&h));
  assert(x>=0&&y>=0&&x+w<=256&&y+h<=192);
  mds_profile_move(&p,1,0);mds_profile_move(&p,-1,0);assert(p.focus==focus);
  mds_profile_move(&p,0,1);mds_profile_move(&p,0,-1);assert(p.focus==focus);
  MdsProfile touch=p;MdsAvatar touched=a;
  int result=mds_profile_activate(&p,&a,0);
  assert(mds_profile_touch(&touch,&touched,x+w/2,y+h/2,0)==result);
  assert(p.mode==touch.mode&&!memcmp(&a,&touched,sizeof a));
  if(focus<8)assert(p.mode==modes[focus]);else assert(result==focus-7);
 }
 mds_profile_begin(&p);mds_profile_move(&p,0,-1);assert(p.focus==8);
 mds_profile_move(&p,-1,0);assert(p.focus==9);
 /* Every character key can be reached, highlighted and activated without touch. */
 mds_profile_open(&p,&a,MDS_PROFILE_NAME);
 for(int row=0;row<4;row++)for(int col=0;mds_profile_key_row((unsigned)row)[col];col++){
  p.key_row=row;p.key_column=col;p.text[0]=0;p.upper=1;
  int x,y,w,h;assert(mds_profile_focus_rect(&p,&x,&y,&w,&h));
  assert(x>=0&&y>=0&&x+w<=256&&y+h<=192);
  MdsProfile touch=p;
  mds_profile_activate(&p,&a,0);mds_profile_touch(&touch,&a,x+1,y+1,0);
  assert(p.text[0]==mds_profile_key_row((unsigned)row)[col]&&p.text[1]==0);
  assert(!strcmp(p.text,touch.text)&&touch.key_row==row&&touch.key_column==col);
  mds_profile_move(&p,1,0);mds_profile_move(&p,-1,0);assert(p.key_column==col);
 }
 p.key_row=0;p.key_column=9;mds_profile_move(&p,0,-1);assert(p.key_row==4&&p.key_column==2);
 mds_profile_move(&p,0,1);assert(p.key_row==0&&p.key_column==2);
 p.key_row=4;p.key_column=0;p.upper=1;mds_profile_activate(&p,&a,0);assert(!p.upper);
 p.key_row=1;p.key_column=0;p.text[0]=0;mds_profile_activate(&p,&a,0);assert(!strcmp(p.text,"q"));
 p.key_row=4;p.key_column=1;mds_profile_activate(&p,&a,0);assert(!strcmp(p.text,"q "));
 p.key_column=2;mds_profile_activate(&p,&a,0);assert(!strcmp(p.text,"q"));
 memset(p.text,'x',10);p.text[10]=0;p.key_row=1;p.key_column=0;mds_profile_activate(&p,&a,0);assert(strlen(p.text)==10&&p.status[0]);
 strcpy(a.name,"Original");strcpy(p.text,"Changed");mds_profile_cancel(&p);assert(!strcmp(a.name,"Original"));
 mds_profile_open(&p,&a,MDS_PROFILE_CREATOR);strcpy(p.text,"Author");assert(mds_profile_done(&p,&a)&&!strcmp(a.creator,"Author"));
 for(int choice=0;choice<12;choice++){
  mds_profile_open(&p,&a,MDS_PROFILE_COLOR);p.choice=choice;
  mds_profile_move(&p,0,1);assert(p.choice==(choice+6)%12);
  mds_profile_move(&p,0,-1);assert(p.choice==choice);
  mds_profile_move(&p,1,0);assert(p.choice/6==choice/6);
 }
 mds_profile_begin(&p);p.focus=1;a.value[46]=0;
 mds_profile_activate(&p,&a,10);assert(!a.value[46]&&p.status[0]);
 a.value[51]=1;mds_profile_activate(&p,&a,0);assert(a.value[46]&&p.status[0]);
}
int main(void){
 controller();
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
 a.value[61]=1;mds_profile_open(&p,&a,MDS_PROFILE_CREATOR);strcpy(p.text,"CODEX");assert(mds_profile_done(&p,&a)&&a.value[61]==1&&mds_valid(&a));
 puts("PASS: original profile bounds, keyboard limits/UTF-8/backspace/cancel, gender, birthday validation, permissions and favorite limit");
}
