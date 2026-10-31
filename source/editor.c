#include "editor.h"
#include <string.h>
static void reload(MdsEditor *e)
{
    if(e->gallery->used[e->slot])e->draft=e->gallery->miis[e->slot];
    else mds_new(&e->draft);
    e->baseline=e->draft;
}
void mds_editor_begin(MdsEditor *e,MdsGallery *g)
{
    memset(e,0,sizeof *e);e->gallery=g;reload(e);e->status="Ready";
}
int mds_editor_dirty(const MdsEditor *e){return memcmp(&e->draft,&e->baseline,sizeof e->draft)!=0;}
int mds_editor_save(MdsEditor *e,MdsPersist persist,void *ctx)
{
    MdsGallery *g=e->gallery;
    static const unsigned days[]={0,31,29,31,30,31,30,31,31,30,31,30,31};
    unsigned month=e->draft.value[49],day=e->draft.value[50];
    if((month||day)&&(!month||month>12||!day||day>days[month])){e->status="Choose a valid birthday.";return 0;}
    MdsAvatar prior=g->miis[e->slot];
    uint8_t used=g->used[e->slot];
    uint32_t generation=g->generation;
    int bank=g->active_bank;
    if(e->draft.value[46]&&(!used||!prior.value[46])){unsigned count=0;for(unsigned i=0;i<MDS_SLOTS;i++)if(i!=e->slot&&g->used[i])count+=g->miis[i].value[46];if(count>=10){e->status="You can save up to ten favorites.";return 0;}}
    if(!mds_gallery_store(g,e->slot,&e->draft)){e->status="Personal Mii or invalid data";return 0;}
    if(!persist||!persist(g,ctx)){
        g->miis[e->slot]=prior;g->used[e->slot]=used;g->generation=generation;g->active_bank=bank;
        e->status="Save failed. Draft retained";return 0;
    }
    e->baseline=e->draft;e->status="ROM save written";return 1;
}
int mds_editor_request(MdsEditor *e,MdsEditAction action)
{
    if(action==MDS_EDIT_NONE||(unsigned)action>(unsigned)MDS_EDIT_RELOAD)return 0;
    if(action==MDS_EDIT_DELETE){
        if(!e->gallery->used[e->slot]){e->status="Slot is empty";return 0;}
        if(e->gallery->miis[e->slot].value[51]){e->status="Personal Mii cannot be deleted";return 0;}
        e->pending=action;e->status="Delete Mii? A yes / B back";return 1;
    }
    e->pending=action;
    if(mds_editor_dirty(e)){e->status="Discard edits? A yes / B back";return 1;}
    return mds_editor_confirm(e,1,NULL,NULL);
}
int mds_editor_confirm(MdsEditor *e,int accept,MdsPersist persist,void *ctx)
{
    MdsEditAction action=e->pending;e->pending=MDS_EDIT_NONE;
    if(!accept){e->status="Cancelled. Draft retained";return 0;}
    if(action==MDS_EDIT_DELETE){
        MdsGallery *g=e->gallery;MdsAvatar prior=g->miis[e->slot];
        uint32_t generation=g->generation;int bank=g->active_bank;
        if(!mds_gallery_delete(g,e->slot)){e->status="Delete blocked";return 0;}
        if(!persist||!persist(g,ctx)){
            g->miis[e->slot]=prior;g->used[e->slot]=1;g->generation=generation;g->active_bank=bank;
            e->status="Delete failed. Mii retained";return 0;
        }
        reload(e);e->status="Mii deleted";return 1;
    }
    if(action==MDS_EDIT_PREV)e->slot=(e->slot+MDS_SLOTS-1)%MDS_SLOTS;
    else if(action==MDS_EDIT_NEXT)e->slot=(e->slot+1)%MDS_SLOTS;
    else if(action==MDS_EDIT_NEW){mds_new(&e->draft);e->baseline=e->draft;e->status="New draft: START to save";return 1;}
    else if(action!=MDS_EDIT_RELOAD)return 0;
    reload(e);e->status=e->gallery->used[e->slot]?"Slot loaded":"Empty slot";return 1;
}

int mds_editor_copy(MdsEditor*e,MdsPersist persist,void*ctx)
{
 MdsGallery*g=e->gallery;
 if(e->slot>=MDS_SLOTS||!g->used[e->slot]){e->status="Choose a saved Mii to copy.";return 0;}
 if(!g->miis[e->slot].value[48]){e->status="Copying is not allowed.";return 0;}
 unsigned dest=0;while(dest<MDS_SLOTS&&g->used[dest])dest++;
 if(dest==MDS_SLOTS){e->status="All 100 Mii slots are occupied";return 0;}
 MdsAvatar prior=g->miis[dest],copy=g->miis[e->slot];uint32_t generation=g->generation;int bank=g->active_bank;
 copy.value[51]=0;copy.value[46]=0;
 if(!mds_gallery_store(g,dest,&copy))return 0;
 if(!persist||!persist(g,ctx)){g->miis[dest]=prior;g->used[dest]=0;g->generation=generation;g->active_bank=bank;e->status="Copy failed. Original retained.";return 0;}
 e->slot=dest;reload(e);e->status="Mii copied.";return 1;
}
