#include "lifecycle.h"
void mds_lifecycle_request(volatile MdsLifecycle *s){s->requested=1;}
int mds_lifecycle_poll(volatile MdsLifecycle *s,int lid_closed,unsigned held)
{
 if(lid_closed)mds_lifecycle_request(s);
 if(s->requested||s->suspended)return 0;
 if(s->release_gate){if(!held)s->release_gate=0;return 0;}
 return 1;
}
void mds_lifecycle_suspend(volatile MdsLifecycle *s){s->suspended=1;}
void mds_lifecycle_resume(volatile MdsLifecycle *s)
{
 s->requested=0;s->suspended=0;s->release_gate=1;
}
