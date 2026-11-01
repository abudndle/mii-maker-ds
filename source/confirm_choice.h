#ifndef MDS_CONFIRM_CHOICE_H
#define MDS_CONFIRM_CHOICE_H
#include <stdint.h>
/* The original DialogBase02_Select P_BaseL/R CLMC RGB source frames
 * move from (100,190,149) to (50,163,112) by source frame 1.
 * Apply as material-relative RGB555 tint to the existing original dialog.
 * This is a bounded DS adaptation, not a full CLMC material compositor. */
#define MDS_CONFIRM_CHOICE_VBLANKS 12u /* source six-frame clip, provisional 2 VBlank/frame */
void mds_confirm_choice_tint(uint16_t *dialog,int choose_yes);
#endif
