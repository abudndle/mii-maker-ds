#include "photo_candidate_input.h"
#include <assert.h>
static int sample(MdsPhotoTouch *g,int down,int held,int up,int x,int y)
{
 return mds_photo_touch_sample(g,down,held,up,x,y);
}
int main(void)
{
 MdsPhotoTouch g={0};
 /* Down/held/up in original Use region produces a release candidate. */
 assert(!sample(&g,1,1,0,115,175));
 assert(!sample(&g,0,1,0,117,176));
 assert(sample(&g,0,0,1,117,176));
 /* A leave-and-return sequence between queued edges permanently cancels. */
 assert(!sample(&g,1,1,0,115,175));
 assert(!sample(&g,0,1,0,160,175));
 assert(!sample(&g,0,1,0,115,175));
 assert(!sample(&g,0,0,1,115,175));
 /* Leaving the strip itself cancels even when release is back inside. */
 assert(!sample(&g,1,1,0,165,175));
 assert(!sample(&g,0,1,0,165,150));
 assert(!sample(&g,0,1,0,165,175));
 assert(!sample(&g,0,0,1,165,175));
 /* New valid press is unaffected by a previous canceled gesture. */
 assert(!sample(&g,1,1,0,165,175));
 assert(sample(&g,0,0,1,165,175));
 /* A release without down, an out-of-region down, and null state reject. */
 assert(!sample(&g,0,0,1,165,175));
 assert(!sample(&g,1,1,0,25,130));
 assert(!sample(&g,0,0,1,115,175));
 assert(!sample(0,1,1,1,115,175));
 return 0;
}
