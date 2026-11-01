#include <assert.h>
#include <stdio.h>
#include "menu.h"
/* Multiple physical key edges must not mutate a Mii twice in one event. */
int main(void)
{
 MdsGalleryControls c;mds_gallery_controls_reset(&c);
 assert(mds_gallery_controls_secondary_allowed(MDS_GALLERY_CONTROL_NONE));
 assert(!mds_gallery_controls_secondary_allowed(MDS_GALLERY_CONTROL_RECALL));
 assert(!mds_gallery_controls_secondary_allowed(MDS_GALLERY_CONTROL_EDIT));
 assert(!mds_gallery_controls_secondary_allowed(MDS_GALLERY_CONTROL_EXPORT));
 assert(!mds_gallery_controls_secondary_allowed(MDS_GALLERY_CONTROL_EDIT|MDS_GALLERY_CONTROL_EXPORT));
 unsigned a=mds_gallery_controls_step(&c,1,1,0,0,0);
 assert(a==MDS_GALLERY_CONTROL_RECALL&&!mds_gallery_controls_secondary_allowed(a));
 mds_gallery_controls_reset(&c);
 a=mds_gallery_controls_step(&c,1,1,1,1,0);
 assert(a==MDS_GALLERY_CONTROL_EDIT&&!mds_gallery_controls_secondary_allowed(a));
 a=mds_gallery_controls_step(&c,0,0,0,0,1);
 assert(a==MDS_GALLERY_CONTROL_NONE);
 mds_gallery_controls_reset(&c);
 a=mds_gallery_controls_step(&c,0,0,1,1,0);
 assert(a==MDS_GALLERY_CONTROL_NONE);
 a=mds_gallery_controls_step(&c,0,0,0,0,1);
 assert(a==MDS_GALLERY_CONTROL_EXPORT&&!mds_gallery_controls_secondary_allowed(a));
 puts("PASS: gallery primary actions exclude same-frame secondary mutations");
 return 0;
}
