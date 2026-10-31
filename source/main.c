#include <nds.h>
#include <string.h>
#include "editor.h"
#include "save_nds.h"
#include "ui.h"
#include "camera_ds.h"
#include "menu.h"
#include "qr_scan.h"
static MdsGallery gallery;
static MdsEditor editor;
static int save_ready;
static MdsProfile profile;
static MdsImport importer;
static int qr_select_image;
static int screen=MDS_SCREEN_HOME;
static volatile uint32_t animation_vblanks;
typedef struct {int down,repeat,held;touchPosition touch;} MdsInput;
static volatile MdsInput input_queue[32];
static volatile unsigned input_read,input_write;
static volatile int live_held,live_touch_x;
static void animation_vblank(void)
{
 animation_vblanks++;scanKeys();
 live_held=keysHeld();touchPosition current;touchRead(&current);live_touch_x=current.px;
 MdsInput event={.down=keysDown(),.repeat=keysDownRepeat(),.held=keysHeld()};
 if(!(event.down||event.repeat))return;
 touchRead(&event.touch);
 unsigned next=(input_write+1)%32;
 if(next!=input_read){input_queue[input_write]=event;input_write=next;}
}
static MdsInput next_input(void)
{
 int state=enterCriticalSection();MdsInput event={.held=keysHeld()};
 if(input_read!=input_write){event=input_queue[input_read];input_read=(input_read+1)%32;}
 leaveCriticalSection(state);return event;
}
static uint32_t render_time(void){return animation_vblanks;}
static int input_waiting(void){return input_read!=input_write;}
static int persist(MdsGallery *g,void *ctx){(void)ctx;return save_ready&&mds_cart_flush(g);}
int main(void)
{
    powerOn(POWER_ALL_2D);irqSet(IRQ_VBLANK,animation_vblank);irqEnable(IRQ_VBLANK);keysSetRepeat(20,5);
    int ui_ready=mds_ui_init();mds_ui_set_render_abort(input_waiting);mds_ui_set_render_clock(render_time);mds_gallery_new(&gallery);save_ready=mds_cart_open(&gallery);mds_editor_begin(&editor,&gallery);mds_profile_begin(&profile);
    int camera_open=0,camera_qr=0,focus=0,drawn_focus=-1,drawn_screen=-1,return_home=0;
    unsigned page=0,drawn_page=99;
    unsigned accessory_choice=0;
    uint32_t slider_changed=0;int slider_preview_pending=0;
    int last_transition_screen=MDS_SCREEN_HOME;
    const char *notice="",*drawn_notice=NULL;
    const char *save_notice="";
    int save_return_screen=MDS_SCREEN_HOME;
    if(ui_ready&&!save_ready)screen=MDS_SCREEN_SAVE_STATUS;
    MdsEditor drawn;memset(&drawn,255,sizeof drawn);
    for(;;){
        MdsInput input=next_input();int k=input.repeat,down=input.down;
        if(camera_open){
            if(down&KEY_B){mds_camera_close();camera_open=0;mds_ui_restore_top();drawn_screen=-1;}
            else{
                if(down&KEY_A){
                    if(camera_qr){
                        MdsMiiRecord received;
                        if(mds_qr_scan_rgb555(&received,mds_camera_frame(),256,192)){
                            if(mds_editor_import(&editor,&received.avatar,persist,NULL)){mds_camera_close();camera_open=0;mds_ui_restore_top();screen=MDS_SCREEN_GALLERY;page=editor.slot/10;drawn_screen=-1;}
                        }else editor.status="No valid Mii QR found. Try again.";
                    }else mds_camera_freeze();
                }
                if(down&KEY_X)mds_camera_switch();
                if(camera_open){camera_open=mds_camera_update();mds_ui_camera(mds_camera_frame());if(!camera_qr)editor.status=mds_camera_status();mds_ui_camera_notice(editor.status);mds_ui_present_top();}
            }
        }else if(editor.pending){
            if((editor.pending==MDS_EDIT_SORT_NAME||editor.pending==MDS_EDIT_SORT_FAVORITES)&&(down&(KEY_L|KEY_R)))
                editor.pending=editor.pending==MDS_EDIT_SORT_NAME?MDS_EDIT_SORT_FAVORITES:MDS_EDIT_SORT_NAME;
            int response=-1;
            if(down&KEY_A)response=1;else if(down&KEY_B)response=0;
            else if(down&KEY_TOUCH){touchPosition t;t=input.touch;
                if((editor.pending==MDS_EDIT_SORT_NAME||editor.pending==MDS_EDIT_SORT_FAVORITES)&&t.px>=24&&t.px<232&&t.py>=40&&t.py<64)
                    editor.pending=editor.pending==MDS_EDIT_SORT_NAME?MDS_EDIT_SORT_FAVORITES:MDS_EDIT_SORT_NAME;
                else response=mds_ui_confirm_touch(t.px,t.py);
            }
            if(response>=0){mds_editor_confirm(&editor,response,persist,NULL);if(screen==MDS_SCREEN_GALLERY)page=editor.slot/10;if(response&&return_home)screen=MDS_SCREEN_HOME;return_home=0;}
        }else if(screen==MDS_SCREEN_SAVE_STATUS){
            int response=-1;
            if(down&KEY_B)response=0;else if(down&KEY_A)response=1;
            else if(down&KEY_TOUCH)response=mds_ui_confirm_touch(input.touch.px,input.touch.py);
            if(response==0){screen=save_return_screen;if(!save_ready)notice="Saving unavailable. SELECT: Details.";}
            if(response==1){
                if(mds_editor_dirty(&editor))save_notice="Draft kept. Save or cancel it first.";
                else{
                    unsigned selected=editor.slot;
                    save_ready=mds_cart_open(&gallery);
                    if(save_ready){mds_editor_begin(&editor,&gallery);editor.slot=selected;mds_editor_request(&editor,MDS_EDIT_RELOAD);page=selected/10;save_notice="Save loaded. Gallery refreshed.";}
                    else save_notice="Gallery kept. Check your save file.";
                }
                drawn_screen=-1;
            }
        }else if(screen==MDS_SCREEN_HOME){
            if(down&KEY_SELECT){save_return_screen=screen;save_notice="";screen=MDS_SCREEN_SAVE_STATUS;continue;}
            if(k&KEY_UP)focus=mds_home_focus_step(focus,-1);
            if(k&KEY_DOWN)focus=mds_home_focus_step(focus,1);
            int action=down&KEY_A?focus+1:0;
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;action=mds_home_touch(t.px,t.py);}
            if(action==MDS_HOME_VIEW){screen=MDS_SCREEN_GALLERY;page=editor.slot/10;notice="";}
            else if(action==MDS_HOME_CREATE){
                unsigned free_slot=0;while(free_slot<100&&gallery.used[free_slot])free_slot++;
                if(free_slot==100)notice="All 100 Mii slots are occupied";
                else{editor.slot=free_slot;mds_editor_request(&editor,MDS_EDIT_NEW);editor.field=2;
                    unsigned personal=0;for(unsigned i=0;i<100;i++)if(gallery.used[i])personal+=gallery.miis[i].value[51];if(!personal){editor.draft.value[51]=1;editor.draft.value[46]=1;}
                    mds_profile_open(&profile,&editor.draft,MDS_PROFILE_GENDER);screen=MDS_SCREEN_GENDER;notice="";}
            }else if(action==MDS_HOME_TRANSFER){mds_ui_import_open(&importer);screen=MDS_SCREEN_IMPORT;}
            else if(action==MDS_HOME_QR){screen=MDS_SCREEN_QR;qr_select_image=0;mds_ui_qr_reset();notice="L/R: choose a saved Mii";if(!gallery.used[editor.slot]){for(unsigned i=0;i<100;i++)if(gallery.used[i]){editor.slot=i;break;}}}
            else if(action==MDS_HOME_HELP)notice="Choose View or Create. B returns here.";
            if(down&KEY_B)notice="";
        }else if(screen==MDS_SCREEN_QR){
            int action=0;
            if(down&KEY_B){if(qr_select_image){qr_select_image=0;drawn_screen=-1;}else screen=MDS_SCREEN_HOME;}
            if(down&(KEY_L|KEY_R)){unsigned candidate=editor.slot;for(unsigned i=0;i<100;i++){candidate=(candidate+(down&KEY_L?99:1))%100;if(gallery.used[candidate]){editor.slot=candidate;break;}}mds_ui_qr_reset();drawn_screen=-1;}
            if(down&KEY_A)action=qr_select_image?2:1;
            if(down&KEY_Y)action=2;
            if(down&KEY_SELECT)action=3;
            if((down&KEY_X)&&isDSiMode())action=4;
            if(down&KEY_TOUCH){int x=input.touch.px,y=input.touch.py;action=mds_ui_qr_touch(x,y,qr_select_image,isDSiMode());if(y>=168){if(qr_select_image)qr_select_image=0;else screen=MDS_SCREEN_HOME;drawn_screen=-1;}}
            if(action==2&&!qr_select_image){qr_select_image=1;action=0;drawn_screen=-1;}

            if(action==4){camera_qr=1;camera_open=mds_camera_open();editor.status=camera_open?"A: Scan Mii QR / X: Camera / B: Back":mds_camera_status();notice=editor.status;}
            else if(action){notice=mds_ui_qr_export(gallery.used[editor.slot]?&gallery.miis[editor.slot]:NULL,editor.slot,action);drawn_screen=-1;}
        }else if(screen==MDS_SCREEN_IMPORT){
            int action=0;
            if(k&KEY_UP){mds_import_step(&importer,-1);drawn_screen=-1;}
            if(k&KEY_DOWN){mds_import_step(&importer,1);drawn_screen=-1;}
            if(down&KEY_B)action=1;
            if(down&KEY_A)action=2;
            if(down&KEY_X)action=3;
            if(down&KEY_TOUCH){
                int x=input.touch.px,y=input.touch.py;
                if(y>=168)action=x<126?1:2;
                else if(x>=184&&y<26)action=3;
                else if(x>=16&&x<240&&y>=32&&y<147){unsigned slot=importer.selected/5*5+(unsigned)(y-32)/23;if(slot<importer.count)mds_import_select(&importer,slot);}
                drawn_screen=-1;
            }
            if(action==1)screen=MDS_SCREEN_HOME;
            if(action==3){mds_ui_import_open(&importer);drawn_screen=-1;}
            if(action==2){
                if(!importer.valid)importer.status="Choose a valid Mii file first.";
                else if(mds_editor_import(&editor,&importer.record.avatar,persist,NULL)){screen=MDS_SCREEN_GALLERY;page=editor.slot/10;}
                else importer.status=editor.status;
                drawn_screen=-1;
            }
        }else if(screen==MDS_SCREEN_GALLERY){
            if(down&KEY_START){mds_editor_request(&editor,MDS_EDIT_SORT_NAME);continue;}
            if(down&KEY_B)screen=MDS_SCREEN_HOME;
            int horizontal=((k&KEY_RIGHT)!=0)-((k&KEY_LEFT)!=0);
            int vertical=((k&KEY_DOWN)!=0)-((k&KEY_UP)!=0);
            if(down&(KEY_L|KEY_R))vertical+=down&KEY_L?-2:2;
            if(horizontal||vertical){editor.slot=mds_gallery_step(editor.slot,horizontal,vertical);page=editor.slot/10;mds_editor_request(&editor,MDS_EDIT_RELOAD);}
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;int slot=mds_gallery_touch(t.px,t.py,page);if(slot>=0){editor.slot=(unsigned)slot;mds_editor_request(&editor,MDS_EDIT_RELOAD);}}
            if(down&KEY_A){if(gallery.used[editor.slot]&&!mds_editor_locked(&gallery.miis[editor.slot])){mds_editor_request(&editor,MDS_EDIT_RELOAD);screen=MDS_SCREEN_EDITOR;}else editor.status=gallery.used[editor.slot]?"This received Mii cannot be edited.":"Choose a saved Mii to edit";}
            if(down&KEY_X)mds_editor_request(&editor,MDS_EDIT_DELETE);
            if(down&KEY_Y){if(mds_editor_copy(&editor,persist,NULL))page=editor.slot/10;}
            if(down&KEY_SELECT)editor.status=gallery.used[editor.slot]?mds_ui_export_image(&gallery.miis[editor.slot],editor.slot):"Choose a saved Mii first.";
        }else if(screen==MDS_SCREEN_GENDER){
            if(k&KEY_LEFT)mds_profile_choice_step(&profile,-1);
            if(k&KEY_RIGHT)mds_profile_choice_step(&profile,1);
            int chosen=-1;
            if(down&KEY_A)chosen=profile.choice;
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;const char*h=mds_profile_hit(2,t.px,t.py);if(!strcmp(h,"B_Male"))chosen=0;else if(!strcmp(h,"B_Female"))chosen=1;}
            if(chosen>=0){profile.choice=chosen;mds_profile_done(&profile,&editor.draft);screen=MDS_SCREEN_EDITOR;}
            if(down&KEY_B){mds_profile_cancel(&profile);screen=MDS_SCREEN_HOME;}
            if(down)drawn_screen=-1;
        }else if(screen==MDS_SCREEN_PROFILE){
            if(profile.mode==MDS_PROFILE_ROOT&&(down&KEY_Y)){save_return_screen=screen;save_notice="";screen=MDS_SCREEN_SAVE_STATUS;continue;}
            unsigned favorites=0;for(unsigned i=0;i<100;i++)if(i!=editor.slot&&gallery.used[i])favorites+=gallery.miis[i].value[46];
            int action=0;
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;action=mds_profile_touch(&profile,&editor.draft,t.px,t.py,favorites);}
            if(down&KEY_B){if(profile.mode==MDS_PROFILE_ROOT)action=1;else mds_profile_cancel(&profile);}
            int profile_mode=profile.mode;
            int horizontal=((k&KEY_RIGHT)!=0)-((k&KEY_LEFT)!=0);
            int vertical=((k&KEY_DOWN)!=0)-((k&KEY_UP)!=0);
            if(profile_mode==MDS_PROFILE_BIRTHDAY){
                if(horizontal)mds_profile_date_step(&profile,1,horizontal);
                if(vertical)mds_profile_date_step(&profile,0,-vertical);
                if(down&KEY_X){profile.month=profile.day=0;mds_profile_done(&profile,&editor.draft);}
            }else mds_profile_move(&profile,horizontal,vertical);
            if(profile_mode==MDS_PROFILE_NAME||profile_mode==MDS_PROFILE_CREATOR){
                if(down&KEY_X)mds_profile_backspace(&profile);
                if(down&KEY_Y)profile.upper^=1;
            }
            if(down&KEY_A)action=mds_profile_activate(&profile,&editor.draft,favorites);
            if(down&KEY_START){if(profile.mode==MDS_PROFILE_ROOT)action=2;else mds_profile_done(&profile,&editor.draft);}
            if(action==1)screen=MDS_SCREEN_EDITOR;
            if(action==2){profile.status="";mds_editor_save(&editor,persist,NULL);}
            if(down||k)drawn_screen=-1;
        }else if(screen==MDS_SCREEN_ACCESSORIES){
            int horizontal=((k&KEY_RIGHT)!=0)-((k&KEY_LEFT)!=0);
            int vertical=((k&KEY_DOWN)!=0)-((k&KEY_UP)!=0);
            if(horizontal||vertical){accessory_choice=mds_accessory_step(accessory_choice,horizontal,vertical);drawn_screen=-1;}
            if(down&KEY_A){editor.field=mds_accessory_field(accessory_choice);screen=MDS_SCREEN_EDITOR;}
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;const char*h=mds_profile_hit(8,t.px,t.py);int f=-1;if(!strcmp(h,"B_Glasses"))f=30;else if(!strcmp(h,"B_Mustache"))f=34;else if(!strcmp(h,"B_Beard"))f=35;else if(!strcmp(h,"B_Mole"))f=39;if(f>=0){editor.field=f;screen=MDS_SCREEN_EDITOR;}}
            if(down&KEY_B)screen=MDS_SCREEN_EDITOR;
        }else{
            if(down&KEY_X){screen=MDS_SCREEN_ACCESSORIES;continue;}
            if(k&KEY_UP)editor.field=(editor.field+50)%51;
            if(k&KEY_DOWN)editor.field=(editor.field+1)%51;
            if(k&KEY_LEFT)mds_adjust(&editor.draft,(unsigned)editor.field,-1);
            if(k&(KEY_RIGHT|KEY_A))mds_adjust(&editor.draft,(unsigned)editor.field,1);
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;if(t.px<30&&t.py>=128&&t.py<149)screen=MDS_SCREEN_ACCESSORIES;else mds_ui_touch(&editor.draft,&editor.field,t.px,t.py);if(mds_ui_slider_active()){slider_changed=animation_vblanks;slider_preview_pending=1;}drawn_screen=-1;}
            if(down&KEY_L)mds_editor_request(&editor,MDS_EDIT_PREV);
            if(down&KEY_R)mds_editor_request(&editor,MDS_EDIT_NEXT);
            if(down&KEY_START){mds_ui_info(&editor.draft,editor.slot,editor.field,"Saving...",mds_editor_dirty(&editor));mds_editor_save(&editor,persist,NULL);}
            if(down&KEY_SELECT){mds_profile_begin(&profile);screen=MDS_SCREEN_PROFILE;}
            if((input.held&KEY_B)&&(down&KEY_Y))mds_editor_request(&editor,MDS_EDIT_DELETE);
            else if(down&KEY_Y){camera_qr=0;camera_open=mds_camera_open();editor.status=mds_camera_status();}
            if((down&KEY_B)&&!(input.held&KEY_Y)){
                mds_editor_request(&editor,MDS_EDIT_RELOAD);
                if(editor.pending)return_home=1;else screen=MDS_SCREEN_HOME;
            }
        }
        if(screen==MDS_SCREEN_EDITOR&&mds_editor_locked(&editor.draft)){screen=MDS_SCREEN_GALLERY;page=editor.slot/10;editor.status="This received Mii cannot be edited.";}
        if(mds_ui_slider_active()){
            if(screen!=MDS_SCREEN_EDITOR||editor.pending||!(live_held&KEY_TOUCH)){mds_ui_slider_release();drawn_screen=-1;}
            else if(mds_ui_slider_move(&editor.draft,live_touch_x)){slider_changed=animation_vblanks;slider_preview_pending=1;drawn_screen=-1;}
        }
        int defer_preview=mds_ui_slider_active()&&animation_vblanks-slider_changed<12;
        if(!defer_preview&&slider_preview_pending){drawn_screen=-1;slider_preview_pending=0;}
        swiWaitForVBlank();
        if(screen!=last_transition_screen){
            if((screen==MDS_SCREEN_GALLERY&&last_transition_screen==MDS_SCREEN_HOME)||
               (screen==MDS_SCREEN_HOME&&last_transition_screen==MDS_SCREEN_GALLERY))
                mds_ui_scene_transition_start(animation_vblanks);
            else mds_ui_scene_transition_cancel();
            last_transition_screen=screen;
        }
        int animate=0;
        mds_ui_motion_scene(screen==MDS_SCREEN_GALLERY);
        if(!mds_ui_slider_active()&&!(screen==MDS_SCREEN_PROFILE&&profile.mode!=MDS_PROFILE_ROOT))animate=mds_ui_animation_tick(animation_vblanks);
        if(!camera_open&&(drawn_screen!=screen||drawn_focus!=focus||drawn_page!=page||drawn_notice!=notice||memcmp(&drawn,&editor,sizeof editor))){
            if(screen==MDS_SCREEN_HOME)mds_ui_home(focus,notice);
            else if(screen==MDS_SCREEN_SAVE_STATUS)mds_ui_save_status(mds_cart_status(),save_notice,save_ready);
            else if(screen==MDS_SCREEN_GALLERY)mds_ui_gallery(&gallery,page,editor.slot,editor.status);
            else if(screen==MDS_SCREEN_QR)mds_ui_qr(gallery.used[editor.slot]?&gallery.miis[editor.slot]:NULL,notice,isDSiMode(),qr_select_image);
            else if(screen==MDS_SCREEN_IMPORT)mds_ui_import(&importer);
            else if(screen==MDS_SCREEN_PROFILE){mds_ui_profile(&profile,&editor.draft);mds_ui_info(&editor.draft,editor.slot,45,profile.status[0]?profile.status:editor.status,mds_editor_dirty(&editor));}
            else if(screen==MDS_SCREEN_GENDER){mds_ui_gender(1,profile.choice);mds_ui_info(&editor.draft,editor.slot,45,"Select a gender.",mds_editor_dirty(&editor));}
            else if(screen==MDS_SCREEN_ACCESSORIES){mds_ui_accessories(accessory_choice);mds_ui_info(&editor.draft,editor.slot,editor.field,"Choose a feature.",mds_editor_dirty(&editor));}
            else{if(ui_ready)mds_ui_draw(&editor.draft,editor.field);if(!defer_preview)mds_ui_info(&editor.draft,editor.slot,editor.field,editor.status,mds_editor_dirty(&editor));}
            if(editor.pending==MDS_EDIT_SORT_NAME||editor.pending==MDS_EDIT_SORT_FAVORITES)mds_ui_sort_confirm(editor.pending==MDS_EDIT_SORT_FAVORITES);
            else if(editor.pending)mds_ui_confirm(editor.pending==MDS_EDIT_DELETE?"Erase this Mii?":"Discard your changes?");
            mds_ui_scene_transition_step(animation_vblanks,1);
            mds_ui_present_top();
            drawn=editor;drawn_screen=screen;drawn_focus=focus;drawn_page=page;drawn_notice=notice;
        }else if(!camera_open&&animate){
            mds_ui_scene_transition_step(animation_vblanks,0);
            if(screen==MDS_SCREEN_GALLERY)mds_ui_gallery_top(&gallery,page,editor.slot,editor.status);
            else if(screen==MDS_SCREEN_EDITOR||screen==MDS_SCREEN_ACCESSORIES)mds_ui_info(&editor.draft,editor.slot,editor.field,editor.status,mds_editor_dirty(&editor));
            else if(screen==MDS_SCREEN_PROFILE||screen==MDS_SCREEN_GENDER)mds_ui_info(&editor.draft,editor.slot,45,profile.status[0]?profile.status:editor.status,mds_editor_dirty(&editor));
            mds_ui_present_top();
        }else if(!camera_open){
            mds_ui_scene_transition_step(animation_vblanks,0);
        }
    }
}
