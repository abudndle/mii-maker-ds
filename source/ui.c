#include <nds.h>
#include <filesystem.h>
#include <stdio.h>
#include <string.h>
#include "ui.h"
#include "head.h"
#include "animation.h"
#include "motion.h"
#include "gui_tween.h"
#include "image.h"
#include "mii_qr.h"
#include "qr_generated.h"
#include "vendor/qr/qrcodegen.h"
#include <time.h>
#include <fat.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include "transform.h"
#include "profile_generated.h"
#include <stdlib.h>
#include <errno.h>
static int init_error;
#include "ui_generated.h"
#include "ui_hits.h"
#include "menu_generated.h"
static u16 *top,*bottom,*top_vram;
static u16 transition_base[256*192];
static MdsGuiTween scene_fade;
static int scene_fade_enabled,scene_fade_base_valid,scene_fade_clock_started;
static u16 top_canvas[256*192],top_backgrounds[2][256*192],body_background[256*192];
static int slider_field=-1;
static UiRect slider_track;
static u16 scratch[128*128];
static unsigned category;
static int ok;
static int show_profile_hint=1;
static MdsCflArchive cfl;
static uint8_t *cfl_bytes;
static uint16_t head_cache[3][MDS_HEAD_SIDE*MDS_HEAD_SIDE];
static uint16_t *head_pixels=head_cache[0];
static uint16_t render_pixels[MDS_HEAD_SIDE*MDS_HEAD_SIDE];
static MdsAvatar head_avatars[3];
static int preview_cached[3],preview_ready[3];
static uint8_t *body_bytes[2];
static size_t body_sizes[2];
static uint8_t *animation_bytes[2];
static MdsAnimation animations[2];
static unsigned animation_index,animation_female_index=UINT32_MAX,preview_pose[3];
static uint32_t animation_clock;
static unsigned rendered_animation_frames;
static MdsMotion motions[2];
static unsigned motion_clip,motion_frame,motion_clip_ticks,motion_scene;
static int motion_clip_valid;
static const char*const gallery_idle_names[]={"Wait00","Wait01","Wait02","Wait03Pre","Wait03","Wait04"};
static int gallery_idle_indices[6];
static int gallery_female_by_male[MDS_MOTION_CLIPS];
static int gallery_selected_clip=-1; /* -1: automatic six-idle playback */
static uint32_t motion_started;
static uint8_t motion_pose_bytes[2][56+1440*18];
static unsigned motion_cached_key[2];
static int motion_cached[2];
static uint32_t (*render_clock)(void);
static uint32_t render_ticks,render_completed,render_cancelled_count;
static void load_bodies(void)
{
 const char *paths[]={"nitro:/models/MaleBody.bin","nitro:/models/FemaleBody.bin"};
 for(unsigned i=0;i<2;i++){
  FILE *f=fopen(paths[i],"rb");if(!f)continue;
  if(fseek(f,0,SEEK_END)){fclose(f);continue;}long n=ftell(f);rewind(f);
  if(n>=56&&n<=200000){body_bytes[i]=malloc((size_t)n);if(body_bytes[i]){if(fread(body_bytes[i],1,(size_t)n,f)==(size_t)n)body_sizes[i]=(size_t)n;else{free(body_bytes[i]);body_bytes[i]=NULL;}}}
  fclose(f);
 }
}
static void load_animations(void)
{
 const char *packs[]={"nitro:/models/MaleBody.msp","nitro:/models/FemaleBody.msp"};
 for(unsigned i=0;i<2;i++){
  FILE*f=fopen(packs[i],"rb");
  if(f&&!mds_motion_open(&motions[i],f))fclose(f);
 }
 /* Resolve the original clip names once instead of scanning all 53 entries
  * on every VBlank. -1 preserves the existing missing-clip behavior. */
 for(unsigned i=0;i<6;i++)
  gallery_idle_indices[i]=mds_motion_find(&motions[0],gallery_idle_names[i]);
 /* Original female/male pack indices differ. Resolve each clip by name. */
 for(unsigned i=0;i<MDS_MOTION_CLIPS;i++)gallery_female_by_male[i]=-1;
 for(unsigned i=0;i<motions[0].count;i++)
  gallery_female_by_male[i]=mds_motion_find(&motions[1],motions[0].clips[i].name);
 /* Keep the older sampled files as a fallback for older resource bundles. */
 const char *paths[]={"nitro:/models/MaleBody.ani","nitro:/models/FemaleBody.ani"};
 for(unsigned i=0;i<2;i++){
  if(motions[i].file)continue;
  FILE*f=fopen(paths[i],"rb");if(!f)continue;
  if(fseek(f,0,SEEK_END)){fclose(f);continue;}long n=ftell(f);rewind(f);
  if(n>=24&&n<=1024*1024){
   animation_bytes[i]=malloc((size_t)n);
   if(animation_bytes[i]&&(fread(animation_bytes[i],1,(size_t)n,f)!=(size_t)n||!mds_animation_open(&animations[i],animation_bytes[i],(size_t)n))){free(animation_bytes[i]);animation_bytes[i]=NULL;}
  }
  fclose(f);
 }
}
void mds_ui_motion_scene(int gallery)
{
 unsigned scene=gallery!=0;
 if(scene!=motion_scene){motion_scene=scene;motion_started=animation_clock;gallery_selected_clip=-1;animation_index=UINT32_MAX;animation_female_index=UINT32_MAX;}
}
int mds_ui_motion_step(int direction)
{
 if(!motion_scene)return 0;
 int next=mds_motion_cycle(&motions[0],gallery_selected_clip,direction);
 if(next<0||next==gallery_selected_clip)return 0;
 gallery_selected_clip=next;motion_started=animation_clock;
 animation_index=UINT32_MAX;animation_female_index=UINT32_MAX;
 return 1;
}
int mds_ui_motion_auto(void)
{
 if(!motion_scene||gallery_selected_clip<0)return 0;
 gallery_selected_clip=-1;motion_started=animation_clock;
 animation_index=UINT32_MAX;animation_female_index=UINT32_MAX;
 return 1;
}
int mds_ui_animation_tick(uint32_t ticks)
{
 animation_clock=ticks;
 if(motions[0].file){
  unsigned elapsed=ticks-motion_started,key=UINT32_MAX;
  int clip=gallery_idle_indices[0];
  if(motion_scene&&gallery_selected_clip>=0)clip=gallery_selected_clip;
  else if(motion_scene){
   unsigned total=0;
   for(unsigned i=0;i<6;i++){int c=gallery_idle_indices[i];if(c>=0)total+=(motions[0].clips[c].count*60u+motions[0].clips[c].fps-1)/motions[0].clips[c].fps;}
   if(total)elapsed%=total;
   for(unsigned i=0;i<6;i++){
    int c=gallery_idle_indices[i];if(c<0)continue;
    unsigned duration=(motions[0].clips[c].count*60u+motions[0].clips[c].fps-1)/motions[0].clips[c].fps;
    if(elapsed<duration){clip=c;break;}elapsed-=duration;
   }
  }
  motion_clip_valid=clip>=0;
  if(clip>=0){motion_clip=(unsigned)clip;motion_clip_ticks=elapsed;motion_frame=mds_motion_frame(&motions[0].clips[clip],elapsed,NULL);key=motion_clip*7200+motion_frame;}
  /* Either rig can advance on a different VBlank when source FPS differs.
   * Refresh the visible Mii if either original animation advances. */
  unsigned female_key=UINT32_MAX;
  if(clip>=0&&motions[1].file){
   int female_clip=gallery_female_by_male[clip];
   if(female_clip>=0)female_key=(unsigned)female_clip*7200u+
    mds_motion_frame(&motions[1].clips[female_clip],motion_clip_ticks,NULL);
  }else if(!motions[1].file){
   /* Mixed resource bundles may contain the male MSP1 stream but only the
    * older female ANI1 poses. Track female samples independently so a slow
    * male clip never freezes the female gallery preview. */
   unsigned sampled=0;
   if(mds_animation_pose(&animations[1],ticks,&sampled))female_key=sampled;
  }
  int changed=key!=animation_index||female_key!=animation_female_index;
  animation_index=key;animation_female_index=female_key;return changed;
 }
 /* Legacy ANI1 fallback can use different pose timing on each gender.
  * Invalidate the preview when either sampled timeline advances. */
 unsigned male_index=UINT32_MAX,female_index=UINT32_MAX,frame=0;
 if(mds_animation_pose(&animations[0],ticks,&frame))male_index=frame;
 if(mds_animation_pose(&animations[1],ticks,&frame))female_index=frame;
 int changed=male_index!=animation_index||female_index!=animation_female_index;
 animation_index=male_index;animation_female_index=female_index;
 return changed;
}
static void load_head_resource(void)
{
 FILE *f=fopen("nitro:/cfl/CFL_Res.dat","rb");if(!f)return;
 if(fseek(f,0,SEEK_END)){fclose(f);return;}long n=ftell(f);rewind(f);
 if(n<84||n>2*1024*1024){fclose(f);return;}
 cfl_bytes=malloc((size_t)n);
 if(cfl_bytes&&(fread(cfl_bytes,1,(size_t)n,f)!=(size_t)n||!mds_cfl_open(&cfl,cfl_bytes,(size_t)n))){free(cfl_bytes);cfl_bytes=NULL;}
 fclose(f);
}
static int preview(const MdsAvatar *a,int mode)
{
 if(!a||!cfl.data||mode<0||mode>2)return 0;
 head_pixels=head_cache[mode];
 unsigned gender=a->value[0],pose_index=0;
 /* Corrupt or imported profile bytes must never index beyond the two rigs. */
 if(gender>=2)return 0;
 const void*body=mode?mds_animation_pose(&animations[gender],animation_clock,&pose_index):NULL;
 size_t size=body?animations[gender].pose_bytes:body_sizes[gender];
 if(mode&&motions[gender].file&&body_bytes[gender]&&body_sizes[gender]<=sizeof motion_pose_bytes[gender]){
  /* The gallery timeline is based on the male rig. Resolve the source
   * clip name on each gender's original rig, not its numeric table index. */
  int selected=-1;
  if(motion_clip_valid&&gender==0&&motion_clip<motions[0].count)selected=(int)motion_clip;
  else if(motion_clip_valid&&gender==1&&motion_clip<motions[0].count)
   selected=gallery_female_by_male[motion_clip];
  if(selected>=0){
   unsigned clip=(unsigned)selected;
   /* Recompute from clip-local VBlank time; the two original rigs may
    * have different source FPS or frame counts. */
   unsigned frame=mds_motion_frame(&motions[gender].clips[clip],motion_clip_ticks,NULL);
   unsigned key=clip*7200+frame;
   if(!motion_cached[gender]||motion_cached_key[gender]!=key){
    /* A failed NitroFS read must remain retryable on a later preview. */
    motion_cached[gender]=mds_motion_pose(&motions[gender],clip,frame,body_bytes[gender],body_sizes[gender],motion_pose_bytes[gender],sizeof motion_pose_bytes[gender]);
    if(motion_cached[gender])motion_cached_key[gender]=key;
   }
   if(motion_cached[gender]){body=motion_pose_bytes[gender];size=56+(body_sizes[gender]-56)/12*18;pose_index=key;}
  }
 }
 if(!body)body=body_bytes[gender];
 if(!preview_cached[mode]||memcmp(a->value,head_avatars[mode].value,sizeof a->value)||(mode&&preview_pose[mode]!=pose_index)){
  uint32_t started=render_clock?render_clock():0;
  int result=mode&&body?mds_mii_render(&cfl,a,body,size,render_pixels,mode==2):mds_head_render(&cfl,a,render_pixels);
  if(result<0){
   render_cancelled_count++;
   /* A cancelled redraw may reuse the previous pose only for the same
    * appearance. Never present a different Mii's cached pixels. */
   return preview_cached[mode]&&
     !memcmp(a->value,head_avatars[mode].value,sizeof a->value)&&
     (!mode||preview_pose[mode]==pose_index)
     ?preview_ready[mode]:0;
  }
  if(result&&render_clock){render_ticks+=render_clock()-started;render_completed++;}
  if(!result){
   /* A missing or temporarily unreadable resource must not poison the
    * appearance cache: retry on the next preview request. */
   preview_ready[mode]=0;
   preview_cached[mode]=0;
   return 0;
  }
  memcpy(head_pixels,render_pixels,sizeof render_pixels);
  preview_ready[mode]=1;
  preview_pose[mode]=pose_index;if(mode)rendered_animation_frames++;
  head_avatars[mode]=*a;preview_cached[mode]=1;
 }
 return preview_ready[mode];
}
static void paint_head(uint16_t *dest,int x,int y,int w,int h)
{
 for(int j=0;j<h;j++)for(int i=0;i<w;i++){
  int dx=x+i,dy=y+j;if(dx<0||dx>=256||dy<0||dy>=192)continue;
  uint16_t c=head_pixels[(j*128/h)*128+i*128/w];if(c&BIT(15))dest[dy*256+dx]=c;
 }
}
const char *mds_ui_export_image(const MdsAvatar*a,unsigned slot)
{
 if(!a)return "Choose a saved Mii first.";
 if(!preview(a,2)||memcmp(a->value,head_avatars[2].value,sizeof a->value))return "Mii image is unavailable.";
 if(!fatInitDefault())return "SD card is unavailable.";
 const char *drive=isDSiMode()?"sd:":"fat:";
 char directory[64],path[96];
 snprintf(directory,sizeof directory,"%s/MiiMaker",drive);
 if(mkdir(directory,0777)&&errno!=EEXIST)return "Could not create image folder.";
 snprintf(directory,sizeof directory,"%s/MiiMaker/Images",drive);
 if(mkdir(directory,0777)&&errno!=EEXIST)return "Could not create image folder.";
 int fd=-1;
 for(unsigned i=0;i<10000;i++){
  snprintf(path,sizeof path,"%s/Mii%03u_%04u.bmp",directory,slot+1,i);
  fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0666);
  if(fd>=0)break;
  if(errno!=EEXIST)return "Could not create image file.";
 }
 if(fd<0)return "Image filenames are occupied.";
 FILE*f=fdopen(fd,"wb");
 if(!f){close(fd);remove(path);return "Could not open image file.";}
 int success=mds_image_bmp(f,head_pixels,128,128,RGB15(27,30,28));
 if(fflush(f))success=0;
 if(fclose(f))success=0;
 if(!success){remove(path);return "Image write failed.";}
 return "BMP saved in MiiMaker/Images.";
}
static unsigned pick(int field){unsigned c=0;for(unsigned i=0;i<UI_CATEGORY_COUNT;i++)if(ui_categories[i].field<=field)c=i;return c;}
static int bitmap(const char *name,u16 *dest){FILE *f=fopen(name,"rb");if(!f)return 0;int n=fread(dest,2,256*192,f)==256*192;fclose(f);return n;}
int mds_ui_init(void){
 videoSetMode(MODE_5_2D);vramSetBankA(VRAM_A_MAIN_BG);int a=bgInit(3,BgType_Bmp16,BgSize_B16_256x256,0,0);top_vram=bgGetGfxPtr(a);top=top_canvas;
 videoSetModeSub(MODE_5_2D);vramSetBankC(VRAM_C_SUB_BG);int b=bgInitSub(3,BgType_Bmp16,BgSize_B16_256x256,0,0);bottom=bgGetGfxPtr(b);
 ok=nitroFSInit(NULL);if(!ok)init_error=errno;for(unsigned i=0;i<256*192;i++)top[i]=bottom[i]=RGB15(26,29,27)|BIT(15);
 if(ok){bitmap("nitro:/ui/top.rgb555",top_backgrounds[0]);bitmap("nitro:/ui/home-top.rgb555",top_backgrounds[1]);bitmap("nitro:/ui/EditBody.rgb555",body_background);memcpy(top,top_backgrounds[0],sizeof top_canvas);load_head_resource();load_bodies();load_animations();}
 mds_ui_present_top();
 return ok;
}
void mds_ui_set_render_clock(uint32_t (*callback)(void)){render_clock=callback;}
void mds_ui_set_render_abort(int (*callback)(void)){mds_render_set_abort(callback);}
/* A short native DS fade-in for home/gallery changes. Original CLAN
   timelines are still separate work: this does not claim their timing. */
void mds_ui_scene_transition_start(uint32_t now)
{
 if(!ok)return;
 mds_gui_tween_start(&scene_fade,now,10,0,16);
 scene_fade_enabled=1;
 scene_fade_base_valid=0;
 scene_fade_clock_started=0;
}
void mds_ui_scene_transition_cancel(void)
{
 scene_fade_enabled=0;
 scene_fade_base_valid=0;
 scene_fade_clock_started=0;
}
int mds_ui_scene_transition_step(uint32_t now,int redraw)
{
 if(!scene_fade_enabled||!ok)return 0;
 /* Expensive gallery model draws may take many VBlanks; begin at first
    presentation rather than letting the fade expire during rendering. */
 if(!scene_fade_clock_started){
  mds_gui_tween_start(&scene_fade,now,10,0,16);
  scene_fade_clock_started=1;
 }
 if(redraw||!scene_fade_base_valid){
  memcpy(transition_base,bottom,sizeof transition_base);
  scene_fade_base_valid=1;
 }
 unsigned light=(unsigned)mds_gui_tween_value(&scene_fade,now);
 if(light>16)light=16;
 if(light==16){
  memcpy(bottom,transition_base,sizeof transition_base);
  scene_fade_enabled=0;
  return 1;
 }
 for(unsigned i=0;i<256*192;i++){
  bottom[i]=mds_gui_fade_rgb555(transition_base[i],light);
 }
 return 1;
}

void mds_ui_present_top(void)
{
 DC_FlushRange(top_canvas,sizeof top_canvas);dmaCopy(top_canvas,top_vram,sizeof top_canvas);
}
static void feature(const char *prefix,int digits,int index,UiRect r){char path[96];snprintf(path,sizeof path,"nitro:/art/%s%0*d.bin",prefix,digits,index);FILE *f=fopen(path,"rb");if(!f)return;unsigned char b[4];if(fread(b,1,4,f)!=4){fclose(f);return;}int w=b[0]|b[1]<<8,h=b[2]|b[3]<<8;if(w<1||h<1||w*h>128*128){fclose(f);return;}int read=fread(scratch,2,(size_t)(w*h),f)==(size_t)(w*h);fclose(f);if(!read)return;
 for(int y=0;y<r.h;y++)for(int x=0;x<r.w;x++){int dx=r.x+x,dy=r.y+y;if(dx<0||dx>=256||dy<0||dy>=192)continue;u16 color=scratch[(y*h/r.h)*w+x*w/r.w];if(color&BIT(15))bottom[dy*256+dx]=color;}
}
void mds_ui_draw(const MdsAvatar *a,int field)
{
 if(!ok)return;
 show_profile_hint=1;
 category=pick(field);const UiCategory *c=&ui_categories[category];char path[96];
 snprintf(path,sizeof path,"nitro:/ui/%s.rgb555",c->layout);
 if(category==12)memcpy(bottom,body_background,sizeof body_background);else bitmap(path,bottom);
 if(category==12){
  for(unsigned i=0;i<UI_HIT_COUNT;i++){
   const UiHit *hit=&ui_hits[i];if(hit->category!=12||strncmp(hit->name,"B_BgSlide_",10))continue;
   int f=43+(hit->name[11]-'0');if(f<43||f>44)continue;
   UiRect track=hit->rect;
   UiRect knob={track.x+a->value[f]*(track.w-1)/127-UI_BODY_SLIDER_W/2,track.y+(track.h-UI_BODY_SLIDER_H)/2,UI_BODY_SLIDER_W,UI_BODY_SLIDER_H};
   feature("BodySlider",1,0,knob);
  }
  return;
 }
 if(!c->prefix||!c->count)return;
 int page=a->value[c->field]/c->count;
 for(int i=0;i<c->count;i++){
  int n=page*c->count+i;if(n<=mds_fields[c->field].maximum)feature(c->prefix,c->digits,n,c->slots[i]);
 }
}
int mds_ui_slider_active(void){return slider_field>=0;}
void mds_ui_slider_release(void){slider_field=-1;}
int mds_ui_slider_move(MdsAvatar*a,int x)
{
 if(slider_field<0||slider_track.w<2)return 0;
 int dx=x-slider_track.x;if(dx<0)dx=0;if(dx>=slider_track.w)dx=slider_track.w-1;
 unsigned value=(unsigned)(dx*127+(slider_track.w-1)/2)/(slider_track.w-1);
 int changed=a->value[slider_field]!=value;a->value[slider_field]=(uint8_t)value;return changed;
}
int mds_ui_touch(MdsAvatar *a,int *field,int x,int y){
 static const int tabs[]={2,5,15,8,22,25,30,43};
 if(x>=0&&x<30&&y>=2&&y<170){int i=(y-2)/21;if(i>=0&&i<8){*field=tabs[i];return 1;}}
 const UiCategory *c=&ui_categories[category];
 static const int color_fields[]={1,-1,-1,6,9,16,-1,26,31,36,36,-1,-1};
 for(unsigned i=0;i<UI_HIT_COUNT;i++){
  const UiHit *hit=&ui_hits[i];UiRect r=hit->rect;
  if(hit->category!=category||x<r.x||x>=r.x+r.w||y<r.y||y>=r.y+r.h)continue;
  if(!strcmp(hit->name,"B_Faceline")){*field=2;return 1;}
  if(!strcmp(hit->name,"B_FaceTMake")){*field=4;return 1;}
  if(!strcmp(hit->name,"B_FaceTLine")){*field=3;return 1;}
  if(!strncmp(hit->name,"B_Color_",8)&&color_fields[category]>=0){
   unsigned n=(unsigned)(hit->name[8]-'0')*10u+(unsigned)(hit->name[9]-'0');
   int f=color_fields[category];if(n<=mds_fields[f].maximum){a->value[f]=(uint8_t)n;*field=f;}return 1;
  }
  if(mds_transform_touch(a,field,category,hit->name))return 1;
  if(category==3&&!strcmp(hit->name,"B_Change_04")){mds_adjust(a,7,1);*field=7;return 1;}
  if(category==12&&!strncmp(hit->name,"B_BgSlide_",10)){
   int f=43+(hit->name[11]-'0');if(f>=43&&f<=44){slider_field=f;slider_track=r;mds_ui_slider_move(a,x);*field=f;}return 1;
  }
  if(c->count&&(!strcmp(hit->name,"B_ArrowR")||!strcmp(hit->name,"B_ArrowL"))){
   mds_adjust(a,(unsigned)c->field,hit->name[7]=='R'?c->count:-c->count);*field=c->field;return 1;
  }
 }
 if(c->prefix&&c->count){int page=a->value[c->field]/c->count;
 for(int i=0;i<c->count;i++){UiRect r=c->slots[i];if(x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h){int n=page*c->count+i;if(n<=mds_fields[c->field].maximum){*field=c->field;a->value[*field]=(uint8_t)n;}return 1;}}
}
 return 0;
}

#include "ui_font.h"
static int text_width(const char *s)
{
 int w=0;for(;*s;s++){unsigned c=(unsigned char)*s;if(c<32||c>126)c='?';w+=ui_font_width[c-32];}return w;
}
static void text_at(uint16_t *dest,int x,int y,const char *text)
{
 for(;*text;text++){
  unsigned c=(unsigned char)*text;if(c<32||c>126)c='?';
  for(int j=0;j<14;j++)for(int i=0;i<12;i++){
   unsigned a=ui_font_alpha[c-32][j][i];int dx=x+i,dy=y+j;
   if(a&&dx>=0&&dx<256&&dy>=0&&dy<192){unsigned old=dest[dy*256+dx],color=0x8000;for(unsigned k=0;k<3;k++)color|=(((old>>(5*k)&31)*(15-a)+8*a)/15)<<(5*k);dest[dy*256+dx]=(uint16_t)color;}
  }
  x+=ui_font_width[c-32];
 }
}
static void label(int x,int y,const char *text){text_at(top,x,y,text);}
static uint16_t status_pixels[2][32*32];
static unsigned status_width[2],status_height[2];
static int status_loaded;
static void status_icon(uint16_t*dest,int x,int y,const MdsAvatar*a)
{
 if(!status_loaded){
  status_loaded=1;const char*paths[]={"nitro:/art/StatusPersonal.bin","nitro:/art/StatusFavorite.bin"};
  for(unsigned i=0;i<2;i++){
   FILE*f=fopen(paths[i],"rb");if(!f)continue;uint8_t h[4];
   if(fread(h,1,4,f)==4){unsigned w=h[0]|h[1]<<8,ht=h[2]|h[3]<<8;if(w&&ht&&w<=32&&ht<=32&&fread(status_pixels[i],2,w*ht,f)==w*ht){status_width[i]=w;status_height[i]=ht;}}
   fclose(f);
  }
 }
 int icon=a->value[51]?0:a->value[46]?1:-1;if(icon<0)return;
 for(unsigned j=0;j<status_height[icon];j++)for(unsigned i=0;i<status_width[icon];i++){
  uint16_t c=status_pixels[icon][j*status_width[icon]+i];int dx=x+(int)i,dy=y+(int)j;if((c&0x8000)&&dx>=0&&dx<256&&dy>=0&&dy<192)dest[dy*256+dx]=c;
 }
}
static const char *display_status(const char *status)
{
 if(!status||!status[0]||!strcmp(status,"Ready")||!strcmp(status,"New draft: START to store")||!strcmp(status,"New draft: START to save"))return "";
 if(!strcmp(status,"ROM save written"))return "Saved.";
 return status;
}
void mds_ui_info(const MdsAvatar *a,unsigned slot,int field,const char *status,int dirty)
{
    if(ok)memcpy(top,top_backgrounds[0],sizeof top_canvas);
    else for(unsigned i=0;i<256*192;i++)top[i]=RGB15(27,30,28)|BIT(15);
    (void)slot;
    int mode=(field>=43&&field<=51)?2:1;
    if(preview(a,mode))paint_head(top,48,12,160,160);else label(42,86,"Face resource unavailable");
    status_icon(top,7,7,a);
    char name[40];snprintf(name,sizeof name,"%.30s%s",a->name,dirty?" *":"");label((256-text_width(name))/2,3,name);
    const char *message=display_status(status);
    if(dirty&&status&&!strcmp(status,"ROM save written"))message="";
    if(message[0])label((256-text_width(message))/2,173,message);else if(show_profile_hint)label(91,176,"SELECT: Profile");

}

void mds_ui_camera(const uint16_t *frame)
{
    if(frame)memcpy(top,frame,256*192*2);
}
void mds_ui_restore_top(void)
{
    if(ok)memcpy(top,top_backgrounds[0],sizeof top_canvas);
}

static void outline(const MdsMenuHit *r)
{
    for(int j=0;j<r->h;j++)for(int i=0;i<r->w;i++){
        int x=r->x+i,y=r->y+j;
        if(x<0||x>=256||y<0||y>=192)continue;
        if(i<2||j<2||i>=r->w-2||j>=r->h-2)bottom[y*256+x]=RGB15(1,14,8)|BIT(15);
    }
}
void mds_ui_home(int focus,const char *notice)
{
    if(!ok){
        for(unsigned i=0;i<256*192;i++)top[i]=bottom[i]=RGB15(27,30,28)|BIT(15);
        label(8,20,"Mii Maker could not load its assets");
        label(8,42,"Use the corrected ROM build.");
        label(8,62,"melonDS: DS mode + Direct Boot");
        char error[40];snprintf(error,sizeof error,"Asset read error: %d",init_error);label(8,90,error);
        return;
    }
    memcpy(top,top_backgrounds[1],sizeof top_canvas);bitmap("nitro:/ui/home-bottom.rgb555",bottom);
    if(focus>0)for(unsigned i=0;i<sizeof home_hits/sizeof home_hits[0];i++)if(home_hits[i].action==focus+1)outline(&home_hits[i]);
    if(notice&&notice[0])label(8,156,notice);
}
void mds_ui_gallery_top(const MdsGallery *g,unsigned page,unsigned selected,const char *notice)
{
    if(!ok)return;
    memcpy(top,top_backgrounds[1],sizeof top_canvas);
    char text[48];
    if(g->used[selected]&&preview(&g->miis[selected],2)){
        paint_head(top,48,12,160,160);
        const char *name=g->miis[selected].name;label((256-text_width(name))/2,3,name);
    }else if(g->used[selected])label(75,83,"Preview unavailable.");
    else label(82,83,"A: Create a Mii");
    if(motion_scene&&motions[0].file){
        const char*clip_name=gallery_selected_clip<0?"Auto":motions[0].clips[gallery_selected_clip].name;
        snprintf(text,sizeof text,"Motion: %s",clip_name);label(8,150,text);
        label(8,163,"UP/DOWN: Clip   START: Auto");
    }
    snprintf(text,sizeof text,"%u / 10",page+1);label(222-text_width(text),177,text);
    if(notice&&notice[0]&&strcmp(notice,"Ready"))label(8,177,display_status(notice));else label(8,177,"Y: Copy  X: Erase  SELECT: Image");
}
void mds_ui_gallery(const MdsGallery *g,unsigned page,unsigned selected,const char *notice)
{
    if(!ok)return;
    mds_ui_gallery_top(g,page,selected,notice);
    bitmap("nitro:/ui/gallery-bottom.rgb555",bottom);
    for(unsigned i=0;i<10;i++){
        unsigned slot=page*10+i;
        /* Original resource thumbnails; full original gallery labels are pending. */
        if(g->used[slot]&&preview(&g->miis[slot],0)){
            const MdsMenuHit *r=&gallery_hits[i];paint_head(bottom,r->x,r->y-2,r->w,r->h);status_icon(bottom,r->x,r->y+r->h-13,&g->miis[slot]);
        }
        if(slot==selected)outline(&gallery_hits[i]);
    }
}

static const uint8_t profile_colors[12][3]={{210,30,20},{255,110,25},{255,216,32},{120,210,32},{0,120,48},{10,72,180},{60,170,222},{245,90,125},{115,40,173},{72,56,24},{224,224,224},{24,24,20}};
static uint16_t widget[160*32];
static unsigned widget_w,widget_h;
static uint8_t number_pixels[14*25*34],number_codes[14],number_metrics[42];
static unsigned number_w,number_h,number_count;
static int widgets_loaded;
static void load_widgets(void)
{
 if(widgets_loaded)return;
 widgets_loaded=1;
 FILE *f=fopen("nitro:/art/ProfileButton0.bin","rb");
 if(f){uint8_t h[4];if(fread(h,1,4,f)==4){unsigned w=h[0]|h[1]<<8,ht=h[2]|h[3]<<8;if(w<=160&&ht<=32&&w>10&&ht>6&&fread(widget,2,w*ht,f)==w*ht){widget_w=w;widget_h=ht;}}fclose(f);}
 f=fopen("nitro:/font/number.bin","rb");
 if(f){uint8_t h[10];if(fread(h,1,10,f)==10&&!memcmp(h,"NUM1",4)){unsigned w=h[4]|h[5]<<8,ht=h[6]|h[7]<<8,n=h[8]|h[9]<<8;if(w==25&&ht==34&&n==14&&fread(number_codes,1,n,f)==n&&fread(number_metrics,3,n,f)==n&&fread(number_pixels,1,w*ht*n,f)==w*ht*n){number_w=w;number_h=ht;number_count=n;}}fclose(f);}
}
static void center_bottom(int cx,int y,const char *s){text_at(bottom,cx-text_width(s)/2,y,s);}
static void button(int x,int y,int w,int h,const char *s)
{
 if(widget_w&&widget_h)for(int j=0;j<h;j++)for(int i=0;i<w;i++){
  int sx=i<5?i:i>=w-5?(int)widget_w-(w-i):5+(i-5)*((int)widget_w-10)/(w-10);
  int sy=j<3?j:j>=h-3?(int)widget_h-(h-j):3+(j-3)*((int)widget_h-6)/(h-6);
  uint16_t c=widget[sy*widget_w+sx];if(c&0x8000)bottom[(y+j)*256+x+i]=c;
 }
 center_bottom(x+w/2,y+(h-12)/2,s);
}
static void numbers(int cx,int y,const char *s)
{
 if(!number_count){center_bottom(cx,y,s);return;}
 int width=0;for(const char *p=s;*p;p++)for(unsigned k=0;k<number_count;k++)if(number_codes[k]==(unsigned char)*p)width+=number_metrics[k*3+2]*4/5;
 int x=cx-width/2;
 for(;*s;s++)for(unsigned k=0;k<number_count;k++)if(number_codes[k]==(unsigned char)*s){
  for(unsigned j=0;j<number_h*4/5;j++)for(unsigned i=0;i<number_w*4/5;i++){
   unsigned alpha=number_pixels[(k*number_h+j*5/4)*number_w+i*5/4];int dx=x+(int)i,dy=y+(int)j;
   if(alpha&&dx>=0&&dx<256&&dy>=0&&dy<192){unsigned old=bottom[dy*256+dx],c=0x8000;for(unsigned ch=0;ch<3;ch++)c|=(((old>>(ch*5)&31)*(255-alpha)+8*alpha)/255)<<(ch*5);bottom[dy*256+dx]=(uint16_t)c;}
  }
  x+=number_metrics[k*3+2]*4/5;break;
 }
}
void mds_ui_profile(const MdsProfile *p,const MdsAvatar *a)
{
 show_profile_hint=0;load_widgets();
 if(p->mode==MDS_PROFILE_NAME||p->mode==MDS_PROFILE_CREATOR){
  bitmap("nitro:/ui/profile.rgb555",bottom);
  for(unsigned i=0;i<256*192;i++)bottom[i]=RGB15(26,29,27)|0x8000;
  center_bottom(128,3,p->mode==MDS_PROFILE_NAME?"Nickname":"Creator");button(8,20,240,25,p->text);
  static const char *rows[]={"1234567890","QWERTYUIOP","ASDFGHJKL","ZXCVBNM.-"};
  for(int row=0;row<4;row++){int n=(int)strlen(rows[row]),left=(256-n*24+2)/2;for(int col=0;col<n;col++){char str[2]={rows[row][col],0};if(!p->upper&&str[0]>='A'&&str[0]<='Z')str[0]+=32;button(left+col*24,50+row*23,22,21,str);}}
  button(8,144,48,20,p->upper?"ABC":"abc");button(60,144,104,20,"Space");button(168,144,80,20,"Backspace");
 }else if(p->mode==MDS_PROFILE_ROOT){
  bitmap("nitro:/ui/profile.rgb555",bottom);center_bottom(80,23,a->name);if(a->value[51]||a->value[46])status_icon(bottom,194,18,a);else center_bottom(203,23,"No");center_bottom(62,64,a->value[0]?"Female":"Male");center_bottom(199,64,a->value[47]?"Allow":"Don't Allow");center_bottom(199,105,a->value[48]?"Allow":"Don't Allow");
  uint16_t color=RGB15(profile_colors[a->value[45]][0]>>3,profile_colors[a->value[45]][1]>>3,profile_colors[a->value[45]][2]>>3)|0x8000;for(int y=106;y<118;y++)for(int x=53;x<72;x++)bottom[y*256+x]=color;
  char date[16];if(a->value[49]&&a->value[50])snprintf(date,sizeof date,"%02u/%02u",a->value[49],a->value[50]);else strcpy(date,"--/--");center_bottom(52,146,date);center_bottom(175,146,a->creator);
 }else{
  const char *name=p->mode==MDS_PROFILE_GENDER?"gender":p->mode==MDS_PROFILE_COLOR?"shirt":p->mode==MDS_PROFILE_BIRTHDAY?"birthday":p->mode==MDS_PROFILE_SHARING?"sharing":"copying";char path[64];snprintf(path,sizeof path,"nitro:/ui/%s.rgb555",name);bitmap(path,bottom);
  if(p->mode==MDS_PROFILE_GENDER||p->mode==MDS_PROFILE_COLOR||p->mode==MDS_PROFILE_SHARING||p->mode==MDS_PROFILE_COPYING){
   unsigned page=p->mode==MDS_PROFILE_GENDER?1:p->mode==MDS_PROFILE_COLOR?4:p->mode==MDS_PROFILE_SHARING?5:6;char target[32];
   if(page==1)strcpy(target,p->choice?"B_Female":"B_Male");else if(page==4)snprintf(target,sizeof target,"B_Color_%02d",p->choice);else strcpy(target,p->choice?"B_BtnCommon_00":"B_BtnCommon_01");
   for(unsigned i=0;i<PROFILE_HIT_COUNT;i++){const ProfileHit*h=&profile_hits[i];if((unsigned)h->page==page&&!strcmp(h->name,target))for(int y=h->y;y<h->y+h->h;y++)for(int x=h->x;x<h->x+h->w;x++)if(x<h->x+2||x>=h->x+h->w-2||y<h->y+2||y>=h->y+h->h-2)bottom[y*256+x]=RGB15(4,16,11)|0x8000;}
  }
  if(p->mode==MDS_PROFILE_BIRTHDAY){char value[16];snprintf(value,sizeof value,"%02d",p->month);numbers(92,78,value);snprintf(value,sizeof value,"%02d",p->day);numbers(164,78,value);center_bottom(128,151,"X: Clear birthday");}
 }
 button(8,168,112,22,p->mode==MDS_PROFILE_ROOT?"Back":"Cancel");button(136,168,112,22,p->mode==MDS_PROFILE_ROOT?"Save":"OK");
}
void mds_ui_gender(int create,int choice)
{
 show_profile_hint=0;bitmap(create?"nitro:/ui/create-gender.rgb555":"nitro:/ui/gender.rgb555",bottom);
 const char *target=choice?"B_Female":"B_Male";
 unsigned page=create?2u:1u;
 for(unsigned i=0;i<PROFILE_HIT_COUNT;i++){
  const ProfileHit *hit=&profile_hits[i];
  if((unsigned)hit->page!=page||strcmp(hit->name,target))continue;
  for(int y=hit->y;y<hit->y+hit->h;y++)for(int x=hit->x;x<hit->x+hit->w;x++){
   if(x<0||x>=256||y<0||y>=192)continue;
   if(x<hit->x+2||x>=hit->x+hit->w-2||y<hit->y+2||y>=hit->y+hit->h-2)
    bottom[y*256+x]=RGB15(4,16,11)|0x8000;
  }
 }
}
void mds_ui_accessories(void){show_profile_hint=0;bitmap("nitro:/ui/accessories.rgb555",bottom);center_bottom(128,70,"Choose a feature to edit.");}
void mds_ui_confirm(const char *message){bitmap("nitro:/ui/confirm.rgb555",bottom);center_bottom(128,27,message);}
int mds_ui_confirm_touch(int x,int y){const char *h=mds_profile_hit(7,x,y);if(!strcmp(h,"B_BtnCommon_00"))return 1;if(!strcmp(h,"B_BtnCommon_01"))return 0;return -1;}

void mds_ui_import_open(MdsImport*b)
{
#ifdef MDS_IMPORT_TEST_FILES
 mds_import_scan(b,"nitro:/test-import");return;
#endif
 mds_import_reset(b);
 if(!fatInitDefault()){b->status="SD card is unavailable.";return;}
 const char*drive=isDSiMode()?"sd:":"fat:";char path[96];
 snprintf(path,sizeof path,"%s/MiiMaker",drive);
 if(mkdir(path,0777)&&errno!=EEXIST){b->status="Could not open MiiMaker folder.";return;}
 snprintf(path,sizeof path,"%s/MiiMaker/Import",drive);
 if(mkdir(path,0777)&&errno!=EEXIST){b->status="Could not open Import folder.";return;}
 mds_import_scan(b,path);
}
void mds_ui_import(const MdsImport*b)
{
 show_profile_hint=0;load_widgets();bitmap("nitro:/ui/import-bottom.rgb555",bottom);
 center_bottom(96,7,"Import a Mii file");button(184,3,64,22,"Rescan");
 unsigned first=b->selected/5*5;
 for(unsigned i=0;i<5&&first+i<b->count;i++){
  char name[32];snprintf(name,sizeof name,"%.27s",b->files[first+i]);button(16,32+i*23,224,21,name);
  if(first+i==b->selected){MdsMenuHit r={.x=16,.y=32+(int)i*23,.w=224,.h=21};outline(&r);}
 }
 char count[40];snprintf(count,sizeof count,"%u / %u%s",b->count?b->selected+1:0,b->count,b->truncated?" (first 100)":"");center_bottom(128,149,count);
 button(8,168,112,21,"Back");button(132,168,116,21,"Import");
 if(b->valid)mds_ui_info(&b->record.avatar,0,45,b->status,0);
 else{memcpy(top,top_backgrounds[0],sizeof top_canvas);label(16,78,b->status);label(16,101,"Folder: MiiMaker/Import");label(16,122,"96-byte .cfsd / .ffsd files");}
}
static uint8_t qr_matrix[MDS_QR_BUFFER];
static int qr_matrix_valid;
void mds_ui_qr_reset(void){qr_matrix_valid=0;}
const char *mds_ui_qr_export(const MdsAvatar*a,unsigned slot,int kind)
{
 if(!a)return "Choose a saved Mii first.";
 if(kind==1&&!a->value[47]){qr_matrix_valid=0;return "Sharing is not allowed.";}
 if(kind==1&&(a->value[61]&2)){qr_matrix_valid=0;return "Special Mii QR export is unavailable.";}
 if(kind==1){
  MdsMiiRecord record;uint8_t encoded[MDS_PACKET],payload[112];
  if(!mds_encode(a,encoded,sizeof encoded))return "Invalid Mii data.";
  uint64_t serial=1469598103934665603ULL;for(unsigned k=0;k<sizeof encoded;k++)serial=(serial^encoded[k])*1099511628211ULL;
  time_t now=time(NULL);uint32_t creation=now>1262304000?(uint32_t)((now-1262304000)/2):1;
  if(!mds_cfs_create(&record,a,creation,serial)||!mds_mii_qr_encrypt(&record,payload)||!mds_mii_qr_matrix(payload,qr_matrix)){qr_matrix_valid=0;return "QR generation failed.";}
  qr_matrix_valid=1;
 }
 int mode=kind==3?0:2;
 if(!preview(a,mode)||memcmp(a->value,head_avatars[mode].value,46))return "Preview loading; try again.";
 if(!fatInitDefault())return kind==1?"QR ready. SD card unavailable.":"SD card is unavailable.";
 const char*drive=isDSiMode()?"sd:":"fat:";char directory[64],path[112];
 snprintf(directory,sizeof directory,"%s/MiiMaker",drive);if(mkdir(directory,0777)&&errno!=EEXIST)return "Could not create photo folder.";
 snprintf(directory,sizeof directory,"%s/MiiMaker/Photos",drive);if(mkdir(directory,0777)&&errno!=EEXIST)return "Could not create photo folder.";
 const char*prefix=kind==1?"QR_Mii":kind==3?"Face_Mii":"Mii";int fd=-1;
 for(unsigned i=0;i<10000;i++){
  snprintf(path,sizeof path,"%s/%s%03u_%04u.png",directory,prefix,slot+1,i);fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0666);
  if(fd>=0)break;
  if(errno!=EEXIST)return "Could not create photo file.";
 }
 if(fd<0)return "Photo filenames are occupied.";
 FILE*f=fdopen(fd,"wb");if(!f){close(fd);remove(path);return "Could not open photo file.";}
 int success=mds_mii_qr_photo(f,kind==1?qr_matrix:NULL,head_pixels);if(fflush(f))success=0;if(fclose(f))success=0;
 if(!success){remove(path);return "Photo write failed.";}
 return "PNG saved in MiiMaker/Photos.";
}
int mds_ui_qr_touch(int x,int y,int choose,int dsi)
{
 for(unsigned i=0;i<MDS_QR_HITS;i++){const MdsQrHit*h=&qr_hits[i];if(h->page==choose&&x>=h->x&&x<h->x+h->w&&y>=h->y&&y<h->y+h->h&&(h->action!=4||dsi))return h->action;}return 0;
}
void mds_ui_qr(const MdsAvatar*a,const char*status,int dsi,int choose)
{
 load_widgets();show_profile_hint=0;bitmap(choose?"nitro:/ui/photo-select.rgb555":dsi?"nitro:/ui/qr-menu-dsi.rgb555":"nitro:/ui/qr-menu-ds.rgb555",bottom);
 button(8,168,240,21,"Back (B)");memcpy(top,top_backgrounds[0],sizeof top_canvas);
 if(choose&&a){if(preview(a,0))paint_head(bottom,52,74,56,56);if(preview(a,2))paint_head(bottom,144,66,64,80);}
 if(a){
  if(preview(a,2))paint_head(top,qr_matrix_valid?2:48,qr_matrix_valid?31:12,qr_matrix_valid?112:160,qr_matrix_valid?140:160);
  label((256-text_width(a->name))/2,3,a->name);status_icon(top,7,7,a);
  if(qr_matrix_valid)for(int y=0;y<130;y++)for(int x=0;x<130;x++){
   int qx=x/2-4,qy=y/2-4;int black=qx>=0&&qx<57&&qy>=0&&qy<57&&qrcodegen_getModule(qr_matrix,qx,qy);
   top[(31+y)*256+122+x]=black?0x8000:0xffff;
  }
 }else label(52,83,"Choose or create a Mii first.");
 if(status&&status[0])label((256-text_width(status))/2,177,status);
}
void mds_ui_camera_notice(const char*message)
{
 for(unsigned i=176*256;i<192*256;i++)top[i]=0xffff;
 if(message)label(3,177,message);
}
