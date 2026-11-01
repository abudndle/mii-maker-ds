#include <nds.h>
#include <string.h>
#include "editor.h"
#include "save_nds.h"
#include "ui.h"
#include "camera_ds.h"
#include "menu.h"
#include "saved_select.h"
#include "qr_scan.h"
static MdsGallery gallery;
static MdsEditor editor;
static int save_ready;
static MdsProfile profile;
static MdsImport importer;
static int qr_select_image;
static int screen=MDS_SCREEN_HOME;
static volatile uint32_t animation_vblanks;
typedef struct {int down,repeat,held,up;touchPosition touch;} MdsInput;
static volatile MdsInput input_queue[32];
static volatile unsigned input_read,input_write;
static volatile int live_held,live_touch_x,live_touch_y;
static void animation_vblank(void)
{
 animation_vblanks++;scanKeys();
 live_held=keysHeld();touchPosition current;touchRead(&current);
 /* Record the last valid stylus coordinate for the release event. */
 if(live_held&KEY_TOUCH){live_touch_x=current.px;live_touch_y=current.py;}
 MdsInput event={.down=keysDown(),.repeat=keysDownRepeat(),.held=live_held,
                 .up=keysUp()};
 if(!(event.down||event.repeat||event.up))return;
 event.touch=current;
 if(event.up&KEY_TOUCH){event.touch.px=live_touch_x;event.touch.py=live_touch_y;}
 /* Reserve eight of the 31 usable slots for fresh presses. Holding a
  * direction during expensive software rendering must not fill the FIFO
  * with repeat events and force genuine input out of the queue. */
 unsigned queued=(input_write+32-input_read)%32;
 if(!(event.down||event.up)&&queued>=23)return;
 unsigned next=(input_write+1)%32;
 if(next==input_read){
  /* Rendering may take several VBlanks. Drop repeat-only events first;
   * preserve new button/touch presses even when the FIFO is saturated. */
  if(!(event.down||event.up))return;
  input_read=(input_read+1)%32;
 }
 input_queue[input_write]=event;
 input_write=next;
}
static MdsInput next_input(void)
{
 int state=enterCriticalSection();MdsInput event={.held=live_held};
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
    int camera_open=0,camera_qr=0,focus=0,drawn_focus=-1,drawn_screen=-1;
    int gender_return_screen=MDS_SCREEN_HOME;
    int saved_selected=-1,qr_return_screen=MDS_SCREEN_HOME;
    int editor_return_screen=MDS_SCREEN_HOME,pending_editor_return=0;
    unsigned page=0,drawn_page=99;
    MdsGalleryDrag gallery_drag;mds_gallery_drag_reset(&gallery_drag);
    uint32_t slider_changed=0;int slider_preview_pending=0;
    int last_transition_screen=MDS_SCREEN_HOME;
    int last_profile_mode=-1;
    MdsProfile profile_exit_visual;
    int profile_exit_pending=0,profile_exit_to_editor=0;
    const char *notice="",*drawn_notice=NULL;
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
            int response=-1;
            if(down&KEY_A)response=1;else if(down&KEY_B)response=0;
            else if(down&KEY_TOUCH){touchPosition t;t=input.touch;response=mds_ui_confirm_touch(t.px,t.py);}
            if(response>=0){
                int copy_prompt=editor.pending==MDS_EDIT_COPY_RECEIVED;
                int confirmed=mds_editor_confirm(&editor,response,persist,NULL);
                if(response&&confirmed&&copy_prompt){
                    /* The received source remains unchanged. Open only the
                     * newly persisted editable copy, on its gallery page. */
                    page=editor.slot/10;
                    editor_return_screen=MDS_SCREEN_GALLERY;
                    screen=MDS_SCREEN_EDITOR;
                }else if(response&&confirmed&&pending_editor_return)
                    screen=editor_return_screen;
                pending_editor_return=0;
            }
        }else if(screen==MDS_SCREEN_HOME){
            int previous_focus=focus;
            if(k&KEY_UP)focus=mds_home_focus_step(focus,-1);
            if(k&KEY_DOWN)focus=mds_home_focus_step(focus,1);
            if(focus!=previous_focus)mds_ui_home_focus_start(animation_vblanks);
            int action=down&KEY_A?focus+1:0;
            if(input.up&(KEY_TOUCH|KEY_LEFT|KEY_RIGHT|KEY_A))
                mds_ui_editor_adjust_release(animation_vblanks,input.up);
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;action=mds_home_touch(t.px,t.py);}
            if(action==MDS_HOME_VIEW){screen=MDS_SCREEN_GALLERY;page=editor.slot/10;notice="";}
            else if(action==MDS_HOME_CREATE){
                unsigned free_slot=0;while(free_slot<100&&gallery.used[free_slot])free_slot++;
                if(free_slot==100)notice="All 100 Mii slots are occupied";
                else if(mds_editor_create(&editor,free_slot)){
                    gender_return_screen=MDS_SCREEN_HOME;
                    mds_profile_open(&profile,&editor.draft,MDS_PROFILE_GENDER);
                    screen=MDS_SCREEN_GENDER;notice="";
                }else notice=editor.status;
            }else if(action==MDS_HOME_TRANSFER){
                /* The source list is the 100-slot cartridge save, not an SD
                 * directory. External .cfsd imports remain optional via X. */
                saved_selected=mds_saved_first(&gallery);
                if(saved_selected<0)notice="Save a Mii first.";
                else{screen=MDS_SCREEN_SAVED;page=(unsigned)saved_selected/10;notice="";}
            }
            else if(action==MDS_HOME_QR){qr_return_screen=MDS_SCREEN_HOME;screen=MDS_SCREEN_QR;qr_select_image=0;mds_ui_qr_reset();notice="L/R: choose a saved Mii";if(!gallery.used[editor.slot]){int saved=mds_gallery_next_saved(gallery.used,editor.slot,1);if(saved>=0)editor.slot=(unsigned)saved;}}
            else if(action==MDS_HOME_HELP)notice="Choose View or Create. B returns here.";
            if(down&KEY_B)notice="";
        }else if(screen==MDS_SCREEN_SAVED){
            /* Choose existing Miis in the cartridge's own gallery. */
            if(down&KEY_B)screen=MDS_SCREEN_HOME;
            if((k&(KEY_UP|KEY_LEFT))&&saved_selected>=0){
                int next=mds_saved_next(&gallery,saved_selected,-1);
                if(next>=0){saved_selected=next;page=(unsigned)next/10;drawn_screen=-1;}
            }else if((k&(KEY_DOWN|KEY_RIGHT))&&saved_selected>=0){
                int next=mds_saved_next(&gallery,saved_selected,1);
                if(next>=0){saved_selected=next;page=(unsigned)next/10;drawn_screen=-1;}
            }
            if(down&(KEY_L|KEY_R)){
                int next=mds_saved_next(&gallery,saved_selected,
                                       (down&KEY_L)?-1:1);
                if(next>=0){saved_selected=next;page=(unsigned)next/10;drawn_screen=-1;}
            }
            if(down&KEY_TOUCH){
                int slot=mds_gallery_touch(input.touch.px,input.touch.py,page);
                if(slot>=0&&gallery.used[slot]){
                    saved_selected=slot;drawn_screen=-1;
                }
            }
            if(down&KEY_X){
                /* Legacy file import is a separate, optional action. */
                mds_ui_import_open(&importer);screen=MDS_SCREEN_IMPORT;
            }
            if((down&KEY_Y)&&saved_selected>=0){
                editor.slot=(unsigned)saved_selected;
                mds_editor_request(&editor,MDS_EDIT_RELOAD);
                if(mds_editor_copy(&editor,persist,NULL)){
                    saved_selected=(int)editor.slot;
                    page=editor.slot/10;
                }
                drawn_screen=-1;
            }
            if((down&KEY_A)&&saved_selected>=0){
                editor.slot=(unsigned)saved_selected;
                mds_editor_request(&editor,MDS_EDIT_RELOAD);
                qr_return_screen=MDS_SCREEN_SAVED;
                qr_select_image=0;mds_ui_qr_reset();
                notice="Saved Mii: QR transfer and image";
                screen=MDS_SCREEN_QR;
            }
        }else if(screen==MDS_SCREEN_QR){
            int action=0;
            if(down&KEY_B){if(qr_select_image){qr_select_image=0;drawn_screen=-1;}else screen=qr_return_screen;}
            if(down&(KEY_L|KEY_R)){int saved=mds_gallery_next_saved(gallery.used,editor.slot,down&KEY_L?-1:1);if(saved>=0)editor.slot=(unsigned)saved;mds_ui_qr_reset();drawn_screen=-1;}
            if(down&KEY_A)action=qr_select_image?2:1;
            if(down&KEY_Y)action=2;
            if(down&KEY_SELECT)action=3;
            if((down&KEY_X)&&isDSiMode())action=4;
            if(down&KEY_TOUCH){int x=input.touch.px,y=input.touch.py;action=mds_ui_qr_touch(x,y,qr_select_image,isDSiMode());if(y>=168){if(qr_select_image)qr_select_image=0;else screen=qr_return_screen;drawn_screen=-1;}}
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
            /* Room slots are selected and dragged with the touchscreen;
             * the D-pad must not move a box-selection cursor. */
            if(down&KEY_UP){if(mds_ui_motion_step(-1))drawn_screen=-1;}
            else if(down&KEY_DOWN){if(mds_ui_motion_step(1))drawn_screen=-1;}
            if(down&KEY_START){if(mds_ui_motion_auto())drawn_screen=-1;}
            if(down&KEY_B)screen=MDS_SCREEN_HOME;
            /* Physical L/R and touchscreen arrows both navigate rooms.
             * Never change rooms while a Mii drag is in progress. */
            if(down&(KEY_L|KEY_R)){
                int direction=(down&KEY_L)?-1:1;
                if(gallery_drag.source>=0){
                    /* Shoulder buttons browse destination rooms while the
                     * selected Mii remains attached to the stylus. */
                    int next=mds_gallery_page_step(page,gallery_drag.source,direction);
                    if(next>=0){page=(unsigned)next/10;drawn_screen=-1;}
                }else{
                    int next=mds_gallery_page_step(page,editor.slot,direction);
                    if(next>=0){page=(unsigned)next/10;editor.slot=(unsigned)next;mds_editor_request(&editor,MDS_EDIT_RELOAD);drawn_screen=-1;}
                }
            }
            if(down&KEY_TOUCH){
                int slot=mds_gallery_touch(input.touch.px,input.touch.py,page);
                int arrow=mds_gallery_room_arrow(input.touch.px,input.touch.py,page);
                /* A bare arrow tap changes rooms; an active drag never pages
                 * until release, so the displayed room stays stable. */
                if(gallery_drag.source<0&&arrow){
                    int next=mds_gallery_page_step(page,editor.slot,arrow);
                    if(next>=0){page=(unsigned)next/10;editor.slot=(unsigned)next;mds_editor_request(&editor,MDS_EDIT_RELOAD);drawn_screen=-1;}
                }else if(gallery_drag.source<0&&slot>=0&&gallery.used[slot]){
                    /* A tap selects immediately; if the stylus moves before
                     * release, the same gesture becomes a drag operation. */
                    editor.slot=(unsigned)slot;
                    mds_editor_request(&editor,MDS_EDIT_RELOAD);
                    mds_gallery_drag_begin(&gallery_drag,page,slot,1);
                    drawn_screen=-1;
                }
            }
            /* During a continuous stylus drag, crossing a room arrow pages
             * the bottom destination boxes while retaining the grabbed Mii.
             * The move itself is committed only when released on a box. */
            if((k&KEY_TOUCH)&&gallery_drag.source>=0){
                int arrow=mds_gallery_room_arrow(input.touch.px,input.touch.py,page);
                if(arrow){
                    int next=mds_gallery_page_step(page,(unsigned)gallery_drag.source,arrow);
                    if(next>=0&&(unsigned)next/10!=page){page=(unsigned)next/10;drawn_screen=-1;}
                }
            }
            if(input.up&KEY_TOUCH){
                unsigned source=0;
                int arrow=mds_gallery_room_arrow(input.touch.px,input.touch.py,page);
                if(gallery_drag.source>=0&&arrow){
                    /* Arrow tap pages the destination room but keeps the
                     * grabbed Mii active. A later box tap/drop commits it. */
                    int next=mds_gallery_page_step(page,(unsigned)gallery_drag.source,arrow);
                    if(next>=0){page=(unsigned)next/10;drawn_screen=-1;}
                }else if(gallery_drag.source>=0){
                    int destination=mds_gallery_drag_end(&gallery_drag,page,
                        mds_gallery_touch(input.touch.px,input.touch.py,page),&source);
                    if(destination>=0){
                        editor.slot=source;
                        mds_editor_request(&editor,MDS_EDIT_RELOAD);
                        if(mds_editor_move(&editor,(unsigned)destination,persist,NULL))
                            page=editor.slot/10;
                        drawn_screen=-1;
                    }
                }
            }
            /* A recalls Miis; hold SELECT+A for legacy create/edit/copy
             * until the equivalent touchscreen actions are available. */
            if(down&KEY_A && !(k&KEY_SELECT)){mds_ui_room_recall();drawn_screen=-1;}
            else if((down&KEY_A) && (k&KEY_SELECT)){
                if(!gallery.used[editor.slot]){
                    if(mds_editor_create(&editor,editor.slot)){
                        gender_return_screen=MDS_SCREEN_GALLERY;
                        mds_profile_open(&profile,&editor.draft,MDS_PROFILE_GENDER);
                        screen=MDS_SCREEN_GENDER;
                    }
                }else if(gallery.miis[editor.slot].value[61]&1){
                    /* Nintendo 3DS behavior: permitted received Miis must be
                     * copied first; never edit the received original. */
                    if(!mds_editor_request(&editor,MDS_EDIT_COPY_RECEIVED))
                        drawn_screen=-1;
                }else if(!mds_editor_locked(&gallery.miis[editor.slot])){
                    mds_editor_request(&editor,MDS_EDIT_RELOAD);
                    editor_return_screen=MDS_SCREEN_GALLERY;
                    screen=MDS_SCREEN_EDITOR;
                }else editor.status="This received Mii cannot be edited.";
            }
            if(down&KEY_X)mds_editor_request(&editor,MDS_EDIT_DELETE);
            if(down&KEY_Y){if(mds_editor_copy(&editor,persist,NULL))page=editor.slot/10;}
            if(down&KEY_SELECT)editor.status=gallery.used[editor.slot]?mds_ui_export_image(&gallery.miis[editor.slot],editor.slot):"Choose a saved Mii first.";
        }else if(screen==MDS_SCREEN_GENDER){
            if(k&KEY_LEFT)mds_profile_choice_step(&profile,-1);
            if(k&KEY_RIGHT)mds_profile_choice_step(&profile,1);
            int chosen=-1;
            if(down&KEY_A)chosen=profile.choice;
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;const char*h=mds_profile_hit(2,t.px,t.py);if(!strcmp(h,"B_Male"))chosen=0;else if(!strcmp(h,"B_Female"))chosen=1;}
            if(chosen>=0){
                profile.choice=chosen;mds_profile_done(&profile,&editor.draft);
                editor_return_screen=gender_return_screen;
                screen=MDS_SCREEN_EDITOR;
            }
            if(down&KEY_B){
                mds_profile_cancel(&profile);
                /* Cancel new-Mii creation without leaving a dirty draft. */
                editor.draft=editor.baseline;editor.pending=MDS_EDIT_NONE;
                editor.status="Creation cancelled";
                screen=gender_return_screen;
            }
            if(down)drawn_screen=-1;
        }else if(screen==MDS_SCREEN_PROFILE){
          if(!profile_exit_pending){
            MdsProfile previous_profile=profile;
            unsigned favorites=0;for(unsigned i=0;i<100;i++)if(i!=editor.slot&&gallery.used[i])favorites+=gallery.miis[i].value[46];
            int action=0;
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;action=mds_profile_touch(&profile,&editor.draft,t.px,t.py,favorites);}
            if(down&KEY_B){if(profile.mode==MDS_PROFILE_ROOT)action=1;else mds_profile_cancel(&profile);}
            if((down&KEY_A)&&profile.mode!=MDS_PROFILE_ROOT)mds_profile_done(&profile,&editor.draft);
            if(down&KEY_START){if(profile.mode==MDS_PROFILE_ROOT)action=2;else mds_profile_done(&profile,&editor.draft);}
            if(profile.mode==MDS_PROFILE_NAME||profile.mode==MDS_PROFILE_CREATOR){if(down&KEY_X)mds_profile_backspace(&profile);if(down&KEY_Y)profile.upper^=1;}
            else if(profile.mode==MDS_PROFILE_BIRTHDAY){if(k&KEY_LEFT)mds_profile_date_step(&profile,1,-1);if(k&KEY_RIGHT)mds_profile_date_step(&profile,1,1);if(k&KEY_UP)mds_profile_date_step(&profile,0,1);if(k&KEY_DOWN)mds_profile_date_step(&profile,0,-1);if(down&KEY_X){profile.month=profile.day=0;mds_profile_done(&profile,&editor.draft);}}
            else if(profile.mode!=MDS_PROFILE_ROOT&&k&(KEY_LEFT|KEY_RIGHT))mds_profile_choice_step(&profile,k&KEY_LEFT?-1:1);
            if(action==2){profile.status="";mds_editor_save(&editor,persist,NULL);}
            /* Keep the prior visual page on-screen until the original
             * DialogOut/OutUp curve completes; prevent input from skipping it.
             * The avatar mutations (OK/Cancel) have already happened. */
            if(action==1||(previous_profile.mode!=MDS_PROFILE_ROOT&&
                           profile.mode==MDS_PROFILE_ROOT)){
                profile_exit_visual=previous_profile;
                profile_exit_pending=1;
                profile_exit_to_editor=action==1;
                mds_ui_profile_transition_exit(animation_vblanks,
                                               !profile_exit_to_editor);
                drawn_screen=-1;
            }
            if(down||k)drawn_screen=-1;
          }
        }else if(screen==MDS_SCREEN_ACCESSORIES){
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;const char*h=mds_profile_hit(8,t.px,t.py);int f=-1;if(!strcmp(h,"B_Glasses"))f=30;else if(!strcmp(h,"B_Mustache"))f=34;else if(!strcmp(h,"B_Beard"))f=35;else if(!strcmp(h,"B_Mole"))f=39;if(f>=0){editor.field=f;screen=MDS_SCREEN_EDITOR;}}
            if(down&KEY_B)screen=MDS_SCREEN_EDITOR;
        }else{
            if(k&KEY_UP)editor.field=(editor.field+50)%51;
            if(k&KEY_DOWN)editor.field=(editor.field+1)%51;
            if(k&KEY_LEFT){
                uint8_t prior=editor.draft.value[editor.field];
                mds_adjust(&editor.draft,(unsigned)editor.field,-1);
                if(editor.draft.value[editor.field]!=prior)
                    mds_ui_editor_adjust_key(animation_vblanks,editor.field,-1);
                else mds_ui_editor_adjust_invalid_key(animation_vblanks,editor.field,-1);
            }
            if(k&(KEY_RIGHT|KEY_A)){
                uint8_t prior=editor.draft.value[editor.field];
                mds_adjust(&editor.draft,(unsigned)editor.field,1);
                if(editor.draft.value[editor.field]!=prior)
                    mds_ui_editor_adjust_key(animation_vblanks,editor.field,1);
                else mds_ui_editor_adjust_invalid_key(animation_vblanks,editor.field,1);
            }
            if(down&KEY_TOUCH){touchPosition t;t=input.touch;if(t.px<30&&t.py>=128&&t.py<149)screen=MDS_SCREEN_ACCESSORIES;else mds_ui_touch(&editor.draft,&editor.field,t.px,t.py);if(mds_ui_slider_active()){slider_changed=animation_vblanks;slider_preview_pending=1;}drawn_screen=-1;}
            if(down&KEY_L){if(mds_ui_view_step(-1))drawn_screen=-1;}
            if(down&KEY_R){if(mds_ui_view_step(1))drawn_screen=-1;}
            if(down&KEY_START){mds_ui_info(&editor.draft,editor.slot,editor.field,"Saving...",mds_editor_dirty(&editor));mds_editor_save(&editor,persist,NULL);}
            if(down&KEY_SELECT){mds_profile_begin(&profile);screen=MDS_SCREEN_PROFILE;}
            if((input.held&KEY_B)&&(down&KEY_Y))mds_editor_request(&editor,MDS_EDIT_DELETE);
            else if(down&KEY_Y){camera_qr=0;camera_open=mds_camera_open();editor.status=mds_camera_status();}
            if((down&KEY_B)&&!(input.held&KEY_Y)){
                mds_editor_request(&editor,MDS_EDIT_RELOAD);
                if(editor.pending)pending_editor_return=1;
                else screen=editor_return_screen;
            }
        }
        if(screen!=MDS_SCREEN_GALLERY)mds_gallery_drag_reset(&gallery_drag);
        if(screen==MDS_SCREEN_EDITOR&&mds_editor_locked(&editor.draft)){screen=MDS_SCREEN_GALLERY;page=editor.slot/10;editor.status="This received Mii cannot be edited.";}
        if(mds_ui_slider_active()){
            if(screen!=MDS_SCREEN_EDITOR||editor.pending||!(live_held&KEY_TOUCH)){mds_ui_slider_release();drawn_screen=-1;}
            else if(mds_ui_slider_move(&editor.draft,live_touch_x)){slider_changed=animation_vblanks;slider_preview_pending=1;drawn_screen=-1;}
        }
        int defer_preview=mds_ui_slider_active()&&animation_vblanks-slider_changed<12;
        if(!defer_preview&&slider_preview_pending){drawn_screen=-1;slider_preview_pending=0;}
        swiWaitForVBlank();
        /* Original DialogBase00 entrance whenever a profile page opens.
         * Hitboxes stay at their final positions; only pixels animate. */
        if(screen==MDS_SCREEN_PROFILE){
            if(!profile_exit_pending){
                if(last_profile_mode!=profile.mode)
                    mds_ui_profile_transition_start(animation_vblanks);
                last_profile_mode=profile.mode;
            }
        }else last_profile_mode=-1;
        /* Advance even when another redraw condition short-circuits. */
        int profile_transition_changed=screen==MDS_SCREEN_PROFILE&&
            mds_ui_profile_transition_tick(animation_vblanks);
        if(profile_exit_pending&&!mds_ui_profile_transition_active()){
            profile_exit_pending=0;
            if(profile_exit_to_editor)screen=MDS_SCREEN_EDITOR;
            drawn_screen=-1;
            profile_transition_changed=1;
        }
        if(screen!=last_transition_screen){
            if((screen==MDS_SCREEN_GALLERY&&last_transition_screen==MDS_SCREEN_HOME)||
               (screen==MDS_SCREEN_HOME&&last_transition_screen==MDS_SCREEN_GALLERY))
                mds_ui_scene_transition_start(animation_vblanks);
            else mds_ui_scene_transition_cancel();
            last_transition_screen=screen;
        }
        mds_ui_editor_selection_update(animation_vblanks,&editor.draft,
            editor.field,screen==MDS_SCREEN_EDITOR&&!editor.pending&&!camera_open);
        int editor_selection_repaint=mds_ui_editor_selection_tick(animation_vblanks);
        int editor_adjust_repaint=mds_ui_editor_adjust_tick(animation_vblanks);
        int animate=0;
        mds_ui_motion_scene(screen==MDS_SCREEN_GALLERY||screen==MDS_SCREEN_SAVED);
        mds_ui_view_scene(screen==MDS_SCREEN_EDITOR||screen==MDS_SCREEN_PROFILE||screen==MDS_SCREEN_ACCESSORIES);
        if(!mds_ui_slider_active()&&!(screen==MDS_SCREEN_PROFILE&&profile.mode!=MDS_PROFILE_ROOT))animate=mds_ui_animation_tick(animation_vblanks);
        if(!camera_open&&(drawn_screen!=screen||drawn_focus!=focus||drawn_page!=page||drawn_notice!=notice||memcmp(&drawn,&editor,sizeof editor)||(screen==MDS_SCREEN_HOME&&mds_ui_home_focus_tick(animation_vblanks))||profile_transition_changed||editor_selection_repaint||editor_adjust_repaint||((screen==MDS_SCREEN_GALLERY||screen==MDS_SCREEN_SAVED)&&
                     mds_ui_gallery_retry_pending()&&!input_waiting()))){
            if(screen==MDS_SCREEN_HOME)mds_ui_home(focus,notice);
            else if(screen==MDS_SCREEN_GALLERY){mds_ui_gallery_drag(gallery_drag.source,input.touch.px,input.touch.py);mds_ui_gallery(&gallery,page,editor.slot,editor.status);}
            else if(screen==MDS_SCREEN_SAVED)mds_ui_saved(&gallery,page,(unsigned)(saved_selected<0?0:saved_selected));
            else if(screen==MDS_SCREEN_QR)mds_ui_qr(gallery.used[editor.slot]?&gallery.miis[editor.slot]:NULL,notice,isDSiMode(),qr_select_image);
            else if(screen==MDS_SCREEN_IMPORT)mds_ui_import(&importer);
            else if(screen==MDS_SCREEN_PROFILE){
                const MdsProfile *shown=profile_exit_pending?
                    &profile_exit_visual:&profile;
                mds_ui_profile(shown,&editor.draft);
                mds_ui_info(&editor.draft,editor.slot,45,
                    shown->status[0]?shown->status:editor.status,
                    mds_editor_dirty(&editor));
            }
            else if(screen==MDS_SCREEN_GENDER){mds_ui_gender(1,profile.choice);mds_ui_info(&editor.draft,editor.slot,45,"Select a gender.",mds_editor_dirty(&editor));}
            else if(screen==MDS_SCREEN_ACCESSORIES){mds_ui_accessories();mds_ui_info(&editor.draft,editor.slot,editor.field,"Choose a feature.",mds_editor_dirty(&editor));}
            else{if(ui_ready)mds_ui_draw(&editor.draft,editor.field);if(!defer_preview)mds_ui_info(&editor.draft,editor.slot,editor.field,editor.status,mds_editor_dirty(&editor));}
            if(editor.pending)mds_ui_confirm(
                editor.pending==MDS_EDIT_DELETE?"Erase this Mii?":
                editor.pending==MDS_EDIT_COPY_RECEIVED?"Copy Mii to edit?":
                "Discard your changes?");
            mds_ui_scene_transition_step(animation_vblanks,1);
            mds_ui_present_top();
            drawn=editor;drawn_screen=screen;drawn_focus=focus;drawn_page=page;drawn_notice=notice;
        }else if(!camera_open&&animate){
            mds_ui_scene_transition_step(animation_vblanks,0);
            if(screen==MDS_SCREEN_GALLERY)mds_ui_gallery_top(&gallery,page,editor.slot,editor.status);
            else if(screen==MDS_SCREEN_SAVED)mds_ui_gallery_top(&gallery,page,(unsigned)(saved_selected<0?0:saved_selected),"Choose a saved Mii");
            else if(screen==MDS_SCREEN_EDITOR||screen==MDS_SCREEN_ACCESSORIES)mds_ui_info(&editor.draft,editor.slot,editor.field,editor.status,mds_editor_dirty(&editor));
            else if(screen==MDS_SCREEN_PROFILE||screen==MDS_SCREEN_GENDER)mds_ui_info(&editor.draft,editor.slot,45,profile.status[0]?profile.status:editor.status,mds_editor_dirty(&editor));
            mds_ui_present_top();
        }else if(!camera_open){
            mds_ui_scene_transition_step(animation_vblanks,0);
        }
    }
}
