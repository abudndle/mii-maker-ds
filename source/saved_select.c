#include "saved_select.h"
unsigned mds_saved_count(const MdsGallery *g)
{
 unsigned count=0;
 if(g)for(unsigned i=0;i<MDS_SLOTS;i++)if(g->used[i])count++;
 return count;
}
int mds_saved_first(const MdsGallery *g)
{
 if(g)for(unsigned i=0;i<MDS_SLOTS;i++)if(g->used[i])return (int)i;
 return -1;
}
int mds_saved_next(const MdsGallery *g,int current,int direction)
{
 if(!g||!direction)return -1;
 if(current<0||current>=MDS_SLOTS)return mds_saved_first(g);
 unsigned slot=(unsigned)current;
 for(unsigned i=0;i<MDS_SLOTS;i++){
  slot=(slot+(direction>0?1u:MDS_SLOTS-1u))%MDS_SLOTS;
  if(g->used[slot])return (int)slot;
 }
 return -1;
}
