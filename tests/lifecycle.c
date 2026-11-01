#include "lifecycle.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 MdsLifecycle s={0};
 assert(mds_lifecycle_poll(&s,0,0));
 assert(mds_lifecycle_poll(&s,0,1));
 /* Close during a held action. Input must stop even before the sleep handler. */
 assert(!mds_lifecycle_poll(&s,1,1)&&s.requested);
 assert(!mds_lifecycle_poll(&s,0,0));
 mds_lifecycle_suspend(&s);assert(s.suspended);
 for(unsigned buttons=0;buttons<8192;buttons++)assert(!mds_lifecycle_poll(&s,1,buttons));
 mds_lifecycle_resume(&s);assert(!s.requested&&!s.suspended&&s.release_gate);
 for(unsigned buttons=1;buttons<8192;buttons++)assert(!mds_lifecycle_poll(&s,0,buttons));
 /* Opening the lid while A/START/touch is held cannot accept a dialog or save. */
 assert(!mds_lifecycle_poll(&s,0,0)&&!s.release_gate);
 assert(mds_lifecycle_poll(&s,0,1));
 /* IRQ-requested sleep and fast close/open still require a fresh release. */
 mds_lifecycle_request(&s);assert(!mds_lifecycle_poll(&s,0,0));
 mds_lifecycle_suspend(&s);mds_lifecycle_resume(&s);
 assert(!mds_lifecycle_poll(&s,0,0));assert(mds_lifecycle_poll(&s,0,0));
 for(unsigned cycle=0;cycle<100;cycle++){
  assert(!mds_lifecycle_poll(&s,1,0));mds_lifecycle_suspend(&s);mds_lifecycle_resume(&s);
  assert(!mds_lifecycle_poll(&s,1,0)); /* lid closes again before release */
  mds_lifecycle_suspend(&s);mds_lifecycle_resume(&s);
  assert(!mds_lifecycle_poll(&s,0,0));assert(mds_lifecycle_poll(&s,0,0));
 }
 puts("PASS: lid/IRQ suspend, held-input suppression, fresh-release gating, fast reopen and repeated sleep cycles");
}
