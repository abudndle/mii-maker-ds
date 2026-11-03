#include "profile.h"
#include <string.h>
#include <ctype.h>
#include "profile_generated.h"
static unsigned days(unsigned month){static const unsigned d[]={0,31,29,31,30,31,30,31,31,30,31,30,31};return month<=12?d[month]:0;}
int mds_profile_date_valid(unsigned month,unsigned day){return (!month&&!day)||(month>=1&&month<=12&&day>=1&&day<=days(month));}
int mds_profile_name_valid(const char *s,int allow_empty)
{
 if(!s||!memchr(s,0,MDS_NAME))return 0;
 unsigned i=0,units=0,nonspace=0;
 while(s[i]){
  uint32_t c=(uint8_t)s[i++],minimum=0;unsigned n=0;
  if(c>=0xf0&&c<=0xf4){c&=7;n=3;minimum=0x10000;}
  else if(c>=0xe0&&c<=0xef){c&=15;n=2;minimum=0x800;}
  else if(c>=0xc2&&c<=0xdf){c&=31;n=1;minimum=0x80;}
  else if(c>=128)return 0;
  while(n--){if(i>=MDS_NAME||((uint8_t)s[i]&0xc0)!=0x80)return 0;c=(c<<6)|((uint8_t)s[i++]&63);}
  if(c<minimum||c>0x10ffff||(c>=0xd800&&c<=0xdfff)||c<32||c==127)return 0;
  units+=c>=0x10000?2:1;if(units>10)return 0;if(c!=32)nonspace++;
 }
 return nonspace||allow_empty;
}
void mds_profile_begin(MdsProfile*p){memset(p,0,sizeof *p);p->upper=1;p->status="";}
void mds_profile_open(MdsProfile*p,const MdsAvatar*a,int mode)
{
 p->mode=mode;p->status="";
 p->choice=mode==MDS_PROFILE_GENDER?a->value[0]:mode==MDS_PROFILE_COLOR?a->value[45]:mode==MDS_PROFILE_SHARING?a->value[47]:mode==MDS_PROFILE_COPYING?a->value[48]:0;
 if(mode==MDS_PROFILE_NAME||mode==MDS_PROFILE_CREATOR){memcpy(p->text,mode==MDS_PROFILE_NAME?a->name:a->creator,MDS_NAME);p->upper=1;}
 if(mode==MDS_PROFILE_BIRTHDAY){p->month=a->value[49]?a->value[49]:1;p->day=a->value[50]?a->value[50]:1;if(!mds_profile_date_valid((unsigned)p->month,(unsigned)p->day))p->day=1;}
}
int mds_profile_append(MdsProfile*p,unsigned ch)
{
 if(!p||ch<32||ch>126)return 0;
 size_t n=strlen(p->text);if(n+1>=MDS_NAME)return 0;
 char candidate[MDS_NAME];memcpy(candidate,p->text,MDS_NAME);candidate[n]=(char)ch;candidate[n+1]=0;
 if(!mds_profile_name_valid(candidate,1)){p->status="Use up to 10 characters.";return 0;}
 memcpy(p->text,candidate,MDS_NAME);p->status="";return 1;
}
void mds_profile_backspace(MdsProfile*p){size_t n=strlen(p->text);if(n){do{n--;}while(n&&((uint8_t)p->text[n]&0xc0)==0x80);memset(p->text+n,0,MDS_NAME-n);}p->status="";}
int mds_profile_done(MdsProfile*p,MdsAvatar*a)
{
 if((p->mode==MDS_PROFILE_GENDER||p->mode==MDS_PROFILE_SHARING||p->mode==MDS_PROFILE_COPYING)&&(p->choice<0||p->choice>1))return 0;
 if(p->mode==MDS_PROFILE_COLOR&&(p->choice<0||p->choice>11))return 0;
 if(p->mode==MDS_PROFILE_NAME||p->mode==MDS_PROFILE_CREATOR){
  if(!mds_profile_name_valid(p->text,p->mode==MDS_PROFILE_CREATOR)){p->status="Please enter a nickname.";return 0;}
  int creator=p->mode==MDS_PROFILE_CREATOR;char *dest=creator?a->creator:a->name;memset(dest,0,MDS_NAME);memcpy(dest,p->text,strlen(p->text));
  for(unsigned i=0;i<(creator?4u:5u);i++){unsigned c=(unsigned char)dest[i];a->value[(creator?57:52)+i]=(uint8_t)(c>=32&&c<=127?c-32:0);}
 }else if(p->mode==MDS_PROFILE_BIRTHDAY){
  if(!mds_profile_date_valid((unsigned)p->month,(unsigned)p->day)){p->status="Choose a valid birthday.";return 0;}
  a->value[49]=(uint8_t)p->month;a->value[50]=(uint8_t)p->day;
 }
 if(p->mode==MDS_PROFILE_GENDER)a->value[0]=(uint8_t)p->choice;
 if(p->mode==MDS_PROFILE_COLOR)a->value[45]=(uint8_t)p->choice;
 if(p->mode==MDS_PROFILE_SHARING)a->value[47]=(uint8_t)p->choice;
 if(p->mode==MDS_PROFILE_COPYING)a->value[48]=(uint8_t)p->choice;
 p->mode=MDS_PROFILE_ROOT;p->status="";return 1;
}
void mds_profile_cancel(MdsProfile*p){p->mode=MDS_PROFILE_ROOT;p->status="";memset(p->text,0,sizeof p->text);}
/* Normalize before wrapping: corrupt dates and large negative steps must not divide by zero. */
static int wrap_date(int current,int delta,int count)
{
 int step=delta%count;
 int index=(current-1+step)%count;
 return (index<0?index+count:index)+1;
}
void mds_profile_date_step(MdsProfile*p,int month,int delta)
{
 if(!p)return;
 if(p->month<1||p->month>12)p->month=1;
 if(month){
  p->month=wrap_date(p->month,delta,12);
  if(p->day>(int)days((unsigned)p->month))p->day=(int)days((unsigned)p->month);
  if(p->day<1)p->day=1;
 }else{
  int n=(int)days((unsigned)p->month);
  if(p->day<1||p->day>n)p->day=1;
  p->day=wrap_date(p->day,delta,n);
 }
 p->status="";
}
int mds_profile_favorite(MdsAvatar*a,unsigned other_favorites){
 if(a->value[51]){a->value[46]=1;return 0;}if(!a->value[46]&&other_favorites>=10)return 0;a->value[46]^=1;return 1;}

const char *mds_profile_hit(unsigned page,int x,int y)
{
 for(unsigned i=0;i<PROFILE_HIT_COUNT;i++){const ProfileHit*h=&profile_hits[i];if((unsigned)h->page==page&&x>=h->x&&x<h->x+h->w&&y>=h->y&&y<h->y+h->h)return h->name;}
 return "";
}
void mds_profile_choice_step(MdsProfile*p,int delta){int n=p->mode==MDS_PROFILE_COLOR?12:2;p->choice=(p->choice+delta+n)%n;}
int mds_profile_touch(MdsProfile*p,MdsAvatar*a,int x,int y,unsigned favorites)
{
 if(p->mode==MDS_PROFILE_NAME||p->mode==MDS_PROFILE_CREATOR){
  static const char *rows[]={"1234567890","QWERTYUIOP","ASDFGHJKL","ZXCVBNM.-"};
  for(int row=0;row<4;row++){
   int count=(int)strlen(rows[row]),left=(256-count*24+2)/2;
   if(y<50+row*23||y>=71+row*23)continue;
   int col=(x-left)/24;if(x>=left&&col<count&&x<left+col*24+22){unsigned ch=(unsigned char)rows[row][col];if(!p->upper&&ch>='A'&&ch<='Z')ch+=32;mds_profile_append(p,ch);return 0;}
  }
  if(y>=144&&y<164){if(x>=8&&x<56)p->upper^=1;else if(x>=60&&x<164)mds_profile_append(p,' ');else if(x>=168&&x<248)mds_profile_backspace(p);return 0;}
 }else if(p->mode==MDS_PROFILE_ROOT){
  const char *hit=mds_profile_hit(0,x,y);int mode=-1;
  if(!strcmp(hit,"B_Nickname"))mode=MDS_PROFILE_NAME;
  else if(!strcmp(hit,"B_Makeup"))mode=MDS_PROFILE_CREATOR;
  else if(!strcmp(hit,"B_Gender"))mode=MDS_PROFILE_GENDER;
  else if(!strcmp(hit,"B_Color"))mode=MDS_PROFILE_COLOR;
  else if(!strcmp(hit,"B_Birthday"))mode=MDS_PROFILE_BIRTHDAY;
  else if(!strcmp(hit,"B_Open"))mode=MDS_PROFILE_SHARING;
  else if(!strcmp(hit,"B_Admission"))mode=MDS_PROFILE_COPYING;
  else if(!strcmp(hit,"B_Favorite")){if(a->value[51]){a->value[46]=1;p->status="Your Personal Mii is always a Favorite.";}else if(!mds_profile_favorite(a,favorites))p->status="You can save up to ten favorites.";return 0;}
  if(mode>=0){mds_profile_open(p,a,mode);return 0;}
 }else{
  unsigned page=p->mode==MDS_PROFILE_GENDER?1:p->mode==MDS_PROFILE_COLOR?4:p->mode==MDS_PROFILE_BIRTHDAY?3:p->mode==MDS_PROFILE_SHARING?5:6;
  const char*hit=mds_profile_hit(page,x,y);
  if(p->mode==MDS_PROFILE_GENDER&&(!strcmp(hit,"B_Male")||!strcmp(hit,"B_Female"))){p->choice=!strcmp(hit,"B_Female");mds_profile_done(p,a);return 0;}
  if(p->mode==MDS_PROFILE_COLOR&&!strncmp(hit,"B_Color_",8)){p->choice=(hit[8]-'0')*10+hit[9]-'0';mds_profile_done(p,a);return 0;}
  if((p->mode==MDS_PROFILE_SHARING||p->mode==MDS_PROFILE_COPYING)&&!strncmp(hit,"B_BtnCommon_",12)){p->choice=hit[13]=='0';mds_profile_done(p,a);return 0;}
  if(p->mode==MDS_PROFILE_BIRTHDAY){
   if(!strcmp(hit,"B_ArrowUpL"))mds_profile_date_step(p,1,1);
   if(!strcmp(hit,"B_ArrowDownL"))mds_profile_date_step(p,1,-1);
   if(!strcmp(hit,"B_ArrowUpR"))mds_profile_date_step(p,0,1);
   if(!strcmp(hit,"B_ArrowDownR"))mds_profile_date_step(p,0,-1);
  }
 }
 if(y>=168&&y<190){
  if(x>=8&&x<120){if(p->mode==MDS_PROFILE_ROOT)return 1;mds_profile_cancel(p);}
  if(x>=136&&x<248){if(p->mode==MDS_PROFILE_ROOT)return 2;mds_profile_done(p,a);}
 }
 return 0;
}
