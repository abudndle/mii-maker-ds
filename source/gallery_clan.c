#include "gallery_clan.h"
#include "gallery_clan_generated.h"
#include <stddef.h>
#include <string.h>

#define KEY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
/* The original SelectMii_Select CLPA scale keys end at frame 2; do not
 * spend extra CPU on its unanimated tail (clip metadata says 6 frames). */
#define SELECT_VISIBLE_TICKS 5u
#define SOURCE_FRAME_Q16_PER_VBLANK 32768

void mds_gallery_clan_reset(MdsGalleryClan *state)
{
    if(state)memset(state,0,sizeof(*state));
}

int mds_gallery_clan_update(MdsGalleryClan *state,unsigned page,
                            unsigned selected,uint32_t now)
{
    if(!state||page>=10||selected>=100)return 0;
    if(!state->initialized){
        state->initialized=1;state->page=page;state->selected=selected;
        state->previous_page=page;state->started=now;
        return 0;
    }
    if(state->page==page&&state->selected==selected)return 0;
    state->previous_page=state->page;
    state->page_changed=(uint8_t)(page!=state->page);
    state->page=page;state->selected=selected;
    state->started=now;state->active=1;
    return 1;
}

int mds_gallery_clan_active(const MdsGalleryClan *state,uint32_t now)
{
    return state&&state->initialized&&state->active&&
           (uint32_t)(now-state->started)<SELECT_VISIBLE_TICKS;
}

static int channel8(const MdsClanKey *keys,size_t count,int32_t frame)
{
    int32_t value=mds_clan_curve_eval(keys,count,frame);
    if(value<=0)return 0;
    if(value>=255*65536)return 255;
    return (int)(((int64_t)value+32768)/65536);
}

static uint16_t tint(const MdsClanKey *red,size_t nr,
                     const MdsClanKey *green,size_t ng,
                     const MdsClanKey *blue,size_t nb,int32_t frame)
{
    unsigned r=(unsigned)channel8(red,nr,frame);
    unsigned g=(unsigned)channel8(green,ng,frame);
    unsigned b=(unsigned)channel8(blue,nb,frame);
    return (uint16_t)(0x8000u|(r>>3)|((g>>3)<<5)|((b>>3)<<10));
}

int mds_gallery_clan_style(const MdsGalleryClan *state,uint32_t now,
                           MdsGalleryClanStyle *out)
{
    if(!out)return 0;
    out->scale_x_q16=65536u;
    out->scale_y_q16=65536u;
    out->selected_room_tint=0xffffu;
    out->previous_room_tint=0xffffu;
    out->previous_page=0;
    out->room_transition=0;
    if(!mds_gallery_clan_active(state,now))return 0;
    uint32_t elapsed=(uint32_t)(now-state->started);
    int32_t frame=(int32_t)(elapsed*SOURCE_FRAME_Q16_PER_VBLANK);
    int32_t sx=mds_clan_curve_eval(gallery_slot_select_scale_x,
                                  KEY_COUNT(gallery_slot_select_scale_x),frame);
    int32_t sy=mds_clan_curve_eval(gallery_slot_select_scale_y,
                                  KEY_COUNT(gallery_slot_select_scale_y),frame);
    /* Original source pulse is 1.0 to 1.1 and back. Invalid decoded
     * data must never create a giant or negative sprite. */
    if(sx>=65536&&sx<=78644)out->scale_x_q16=(uint32_t)sx;
    if(sy>=65536&&sy<=78644)out->scale_y_q16=(uint32_t)sy;
    if(state->page_changed&&elapsed<=2u){
        int32_t room_frame=(int32_t)(elapsed*SOURCE_FRAME_Q16_PER_VBLANK);
        out->selected_room_tint=tint(gallery_room_select_red,
            KEY_COUNT(gallery_room_select_red),gallery_room_select_green,
            KEY_COUNT(gallery_room_select_green),gallery_room_select_blue,
            KEY_COUNT(gallery_room_select_blue),room_frame);
        out->previous_room_tint=tint(gallery_room_unselect_red,
            KEY_COUNT(gallery_room_unselect_red),gallery_room_unselect_green,
            KEY_COUNT(gallery_room_unselect_green),gallery_room_unselect_blue,
            KEY_COUNT(gallery_room_unselect_blue),room_frame);
        out->previous_page=state->previous_page;
        out->room_transition=1;
    }
    return 1;
}
