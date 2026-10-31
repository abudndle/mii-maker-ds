#ifndef MDS_VIEW_H
#define MDS_VIEW_H
#include <stdint.h>
/* Twenty-four 15-degree steps for the original L/R Mii viewing controls.
 * Fixed-point Q14 preserves portable ARM9 and host behavior. */
#define MDS_VIEW_STEPS 24u
unsigned mds_view_step(unsigned current,int direction);
void mds_view_rotate(int32_t *x,int32_t *z,unsigned step);
#endif
