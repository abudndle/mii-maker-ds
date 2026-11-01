#include "original_gallery_art.h"
#include <stdio.h>

/* Native CLIM assets are NEVER part of the public source. Their converted
 * width, height and RGB555A1 pixels are read from optional private NitroFS.
 * One-time loading avoids filesystem I/O on every rendered gallery frame. */
#define MDS_ORIG_MAX_PIXELS (54u*60u)
typedef struct {
    const char *path;
    unsigned expected_width,expected_height;
    int state; /* 0: not tried, 1: validated, -1: not available */
    uint16_t pixels[MDS_ORIG_MAX_PIXELS];
} OriginalSprite;

static OriginalSprite room_box_base = {
    "nitro:/art/Select/BtnMiiB.bin",54,60,0,{0}
};
static OriginalSprite room_box_line = {
    "nitro:/art/Select/BtnMiiLine.bin",54,60,0,{0}
};
static OriginalSprite room_tab_line = {
    "nitro:/art/Select/BtnRoomEDITline.bin",32,28,0,{0}
};
static OriginalSprite room_tab_selected = {
    "nitro:/art/Select/BtnRoomEDITline01.bin",32,28,0,{0}
};

static int original_sprite_ready(OriginalSprite *sprite)
{
    if(sprite->state!=0)return sprite->state==1;
    /* If the original file is absent or damaged, do not retry at 60 FPS. */
    sprite->state=-1;
    FILE *f=fopen(sprite->path,"rb");
    if(!f)return 0;
    unsigned char dimensions[4];
    int valid=fread(dimensions,1,4,f)==4;
    if(valid){
        unsigned width=(unsigned)dimensions[0]|((unsigned)dimensions[1]<<8);
        unsigned height=(unsigned)dimensions[2]|((unsigned)dimensions[3]<<8);
        valid=width==sprite->expected_width &&
              height==sprite->expected_height &&
              width*height<=MDS_ORIG_MAX_PIXELS;
        if(valid){
            unsigned count=width*height;
            valid=fread(sprite->pixels,sizeof(uint16_t),count,f)==count &&
                  fgetc(f)==EOF; /* reject short and oversized resources */
        }
    }
    fclose(f);
    if(valid)sprite->state=1;
    return valid;
}

static int original_sprite_blit(OriginalSprite *sprite,uint16_t *canvas,
                                int width,int height,int x,int y,int w,int h,uint16_t tint)
{
    if(!canvas||width<=0||height<=0||width>512||height>512||
       w<=0||h<=0||w>512||h>512)return 0;
    if(!original_sprite_ready(sprite))return 0;
    for(int row=0;row<h;row++){
        long dest_y=(long)y+row;
        if(dest_y<0||dest_y>=height)continue;
        unsigned original_y=(unsigned)row*sprite->expected_height/(unsigned)h;
        for(int col=0;col<w;col++){
            long dest_x=(long)x+col;
            if(dest_x<0||dest_x>=width)continue;
            unsigned original_x=(unsigned)col*sprite->expected_width/(unsigned)w;
            uint16_t pixel=sprite->pixels[original_y*sprite->expected_width+original_x];
            if(pixel&0x8000u){
                /* CLMC source pane color: scale each original pixel channel.
                 * The source opacity bit is left intact; all integer math. */
                unsigned r=((unsigned)(pixel&31u)*((unsigned)tint&31u)+15u)/31u;
                unsigned g=((unsigned)((pixel>>5)&31u)*((unsigned)(tint>>5)&31u)+15u)/31u;
                unsigned blue=((unsigned)((pixel>>10)&31u)*((unsigned)(tint>>10)&31u)+15u)/31u;
                canvas[(size_t)dest_y*(unsigned)width+(size_t)dest_x]=
                    (uint16_t)(0x8000u|r|(g<<5)|(blue<<10));
            }
        }
    }
    return 1;
}

int mds_original_gallery_box_base(uint16_t *canvas,int width,int height,
                                  int x,int y,int w,int h)
{
    return original_sprite_blit(&room_box_base,canvas,width,height,x,y,w,h,0xffffu);
}

int mds_original_gallery_box_border_tinted(uint16_t *canvas,int width,int height,
                                           int x,int y,int w,int h,uint16_t tint)
{
    return original_sprite_blit(&room_box_line,canvas,width,height,x,y,w,h,tint);
}
int mds_original_gallery_box_border(uint16_t *canvas,int width,int height,
                                    int x,int y,int w,int h)
{
    return mds_original_gallery_box_border_tinted(canvas,width,height,
                                                  x,y,w,h,0xffffu);
}

int mds_original_gallery_room_tab_tinted(uint16_t *canvas,int width,int height,
                                         int x,int y,int w,int h,int selected,uint16_t tint)
{
    OriginalSprite *sprite=selected?&room_tab_selected:&room_tab_line;
    if(original_sprite_blit(sprite,canvas,width,height,x,y,w,h,tint))return 1;
    if(selected)
        return original_sprite_blit(&room_tab_line,canvas,width,height,x,y,w,h,tint);
    return 0;
}
int mds_original_gallery_room_tab(uint16_t *canvas,int width,int height,
                                  int x,int y,int w,int h,int selected)
{
    return mds_original_gallery_room_tab_tinted(canvas,width,height,
                                                x,y,w,h,selected,0xffffu);
}
