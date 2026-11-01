#ifndef MDS_LIFECYCLE_H
#define MDS_LIFECYCLE_H
typedef struct {int requested,suspended,release_gate;} MdsLifecycle;
void mds_lifecycle_request(volatile MdsLifecycle *);
/* Called with live input each VBlank; zero means discard this frame's input. */
int mds_lifecycle_poll(volatile MdsLifecycle *,int lid_closed,unsigned held);
void mds_lifecycle_suspend(volatile MdsLifecycle *);
void mds_lifecycle_resume(volatile MdsLifecycle *);
#endif
