#include "confirm_choice.h"
#include "confirm_motion.h"
#include <stddef.h>
void mds_confirm_choice_tint(uint16_t *dialog,int choose_yes)
{
    if(!dialog)return;
    /* Actual scaled DialogBase02 B_BtnCommon_00/_01 bounds from original
     * Dialog CLYT, also used by source/profile_generated.h touch panes. */
    const unsigned y=choose_yes?71u:111u;
    const unsigned x=28u;
    const unsigned width=200u;
    const unsigned height=32u;
    for(unsigned row=y;row<y+height;row++){
        for(unsigned col=x;col<x+width;col++){
            uint16_t *dst=dialog+(size_t)row*MDS_CONFIRM_WIDTH+col;
            uint16_t pixel=*dst;
            unsigned r=pixel&31u, g=(pixel>>5)&31u,b=(pixel>>10)&31u;
            /* Preserve source artwork detail while applying actual source
             * CLMC target/default material channel ratios. */
            r=(r*50u+50u)/100u;
            g=(g*163u+95u)/190u;
            b=(b*112u+74u)/149u;
            if(r>31u)r=31u;
            if(g>31u)g=31u;
            if(b>31u)b=31u;
            *dst=(uint16_t)((pixel&0x8000u)|(b<<10)|(g<<5)|r);
        }
    }
}
