#include "create_method.h"
#include <assert.h>
#include <string.h>
static MdsCreateOutcome evaluate(MdsCreateInput i){return mds_create_method_input(i);}
int main(void)
{
 MdsCreateInput i;memset(&i,0,sizeof i);
 i.selection=0;i.dsi_enabled=1;
 MdsCreateOutcome r=evaluate(i);
 assert(r.choice==MDS_CREATE_NONE&&r.selection==0);
 /* A+right used to jump into photo creation instead of scratch. */
 i.confirm=1;i.right=1;
 r=evaluate(i);
 assert(r.choice==MDS_CREATE_SCRATCH&&r.selection==0);
 i.confirm=0;r=evaluate(i);
 assert(r.choice==MDS_CREATE_NONE&&r.selection==1);
 /* DSi and ordinary DS have the same navigation, different feature gate. */
 i.confirm=1;i.right=0;i.dsi_enabled=0;
 r=evaluate(i);assert(r.choice==MDS_CREATE_NONE&&r.selection==1);
 i.dsi_enabled=1;r=evaluate(i);
 assert(r.choice==MDS_CREATE_PHOTO_PREVIEW&&r.selection==1);
 /* B wins even when A/touch/directions arrive at once. */
 i.cancel=1;i.touch=1;i.x=100;i.y=70;i.up=1;
 r=evaluate(i);
 assert(r.choice==MDS_CREATE_BACK&&r.selection==1);
 i.cancel=0;
 /* Touch explicitly chooses scratch over simultaneous A on photo. */
 r=evaluate(i);
 assert(r.choice==MDS_CREATE_SCRATCH&&r.selection==1);
 i.touch=0;
 r=evaluate(i);
 assert(r.choice==MDS_CREATE_PHOTO_PREVIEW&&r.selection==1);
 /* Disabled DSi photo target is inert on DS; does not switch selection. */
 i.dsi_enabled=0;i.confirm=0;i.touch=1;i.x=100;i.y=140;i.up=0;
 r=evaluate(i);
 assert(r.choice==MDS_CREATE_NONE&&r.selection==1);
 /* Invalid touch plus A uses the already highlighted menu item. */
 i.confirm=1;i.x=0;i.y=0;
 r=evaluate(i);
 assert(r.choice==MDS_CREATE_NONE&&r.selection==1);
 i.selection=0;
 r=evaluate(i);
 assert(r.choice==MDS_CREATE_SCRATCH&&r.selection==0);
 /* Opposing directions on an axis must not toggle twice or once. */
 memset(&i,0,sizeof i);i.selection=0;i.up=i.down=1;
 r=evaluate(i);assert(r.selection==0);
 i.up=i.down=0;i.left=i.right=1;
 r=evaluate(i);assert(r.selection==0);
 /* Two unopposed directions still toggle exactly once. */
 i.right=0;i.up=1;
 r=evaluate(i);assert(r.selection==1);
 /* No invalid selection is ever made into a method. */
 i.selection=2;i.confirm=1;i.up=0;i.left=0;
 r=evaluate(i);assert(r.choice==MDS_CREATE_NONE&&r.selection==2);
 return 0;
}
