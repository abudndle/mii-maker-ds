#include "editor.h"
#include "unicode.h"
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
/* Received characters are read-only: permission allows making an editable
 * COPY, never changing the original received record in-place. */
int mds_editor_locked(const MdsAvatar*a){return a&&(a->value[61]&3)!=0;}
int mds_editor_dirty(const MdsEditor *e){return memcmp(&e->draft,&e->baseline,sizeof e->draft)!=0;}
int mds_editor_save(MdsEditor *e,MdsPersist persist,void *ctx)
{
    MdsGallery *g=e->gallery;
    if(g->used[e->slot]&&mds_editor_locked(&g->miis[e->slot])){e->status="This received Mii cannot be edited.";return 0;}
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
    if(!e||!e->gallery||e->slot>=MDS_SLOTS||action==MDS_EDIT_NONE||
       (unsigned)action>(unsigned)MDS_EDIT_COPY_RECEIVED||e->pending)return 0;
    if(action==MDS_EDIT_COPY_RECEIVED){
        if(!e->gallery->used[e->slot]||!(e->gallery->miis[e->slot].value[61]&1)||
           (e->gallery->miis[e->slot].value[61]&2)||
           !e->gallery->miis[e->slot].value[48]){
            e->status="This received Mii cannot be copied.";
            return 0;
        }
        if(mds_editor_dirty(e)){
            e->status="Discard unsaved edits before copying.";
            return 0;
        }
        e->pending=action;
        e->status="Copy received Mii to edit? A yes / B back";
        return 1;
    }
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
    if(action==MDS_EDIT_COPY_RECEIVED)
        return mds_editor_copy(e,persist,ctx);
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

int mds_editor_create(MdsEditor *e,unsigned slot)
{
 if(!e||!e->gallery||slot>=MDS_SLOTS||e->gallery->used[slot])return 0;
 /* Never overwrite an unfinished edit when selecting a new gallery slot. */
 if(mds_editor_dirty(e)){
  e->status="Discard unsaved edits before creating a Mii.";
  return 0;
 }
 e->slot=slot;e->field=2;e->pending=MDS_EDIT_NONE;
 mds_new(&e->draft);e->baseline=e->draft;
 unsigned personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++)
  if(e->gallery->used[i]&&e->gallery->miis[i].value[51])personal++;
 if(!personal){e->draft.value[51]=1;e->draft.value[46]=1;}
 e->status="New draft: START to save";
 return 1;
}

int mds_editor_move(MdsEditor *e,unsigned destination,MdsPersist persist,void *ctx)
{
 if(!e||!e->gallery||e->slot>=MDS_SLOTS||destination>=MDS_SLOTS||
    destination==e->slot)return 0;
 MdsGallery *g=e->gallery;
 if(!g->used[e->slot]){e->status="Choose a saved Mii to move.";return 0;}
 if(e->pending||mds_editor_dirty(e)){
  e->status="Discard unsaved edits before moving a Mii.";
  return 0;
 }
 unsigned source=e->slot;
 MdsAvatar old_source=g->miis[source],old_dest=g->miis[destination];
 uint8_t was_source=g->used[source],was_dest=g->used[destination];
 uint32_t generation=g->generation;
 int bank=g->active_bank;
 /* Rearranging never changes the Mii contents or ownership/permissions.
  * The Personal Mii is protected from deletion but may change gallery slot. */
 g->miis[destination]=old_source;
 g->used[destination]=was_source;
 g->miis[source]=old_dest;
 g->used[source]=was_dest;
 if(!was_dest)memset(&g->miis[source],0,sizeof g->miis[source]);
 if(!persist||!persist(g,ctx)){
  g->miis[source]=old_source;g->miis[destination]=old_dest;
  g->used[source]=was_source;g->used[destination]=was_dest;
  g->generation=generation;g->active_bank=bank;
  e->status="Move failed. Gallery retained.";
  return 0;
 }
 e->slot=destination;
 reload(e);
 e->status=was_dest?"Miis swapped.":"Mii moved.";
 return 1;
}

/* A gallery Favorite button changes the saved record immediately.  Keep
 * the transaction separate from profile editing so a failed cartridge write
 * cannot leave a false red crown or an unsaved in-memory toggle. */
int mds_editor_toggle_favorite(MdsEditor *e,MdsPersist persist,void *ctx)
{
    if(!e||!e->gallery||e->slot>=MDS_SLOTS)return 0;
    MdsGallery *g=e->gallery;
    if(!g->used[e->slot]){e->status="Choose a saved Mii first.";return 0;}
    if(g->miis[e->slot].value[51]){
        e->status="Your Personal Mii is always a Favorite.";
        return 0;
    }
    if(mds_editor_locked(&g->miis[e->slot])){
        e->status="This received Mii cannot be changed.";
        return 0;
    }
    if(e->pending||mds_editor_dirty(e)){
        e->status="Discard unsaved edits before changing Favorite.";
        return 0;
    }
    if(!g->miis[e->slot].value[46]){
        unsigned favorites=0;
        for(unsigned i=0;i<MDS_SLOTS;i++)
            if(i!=e->slot&&g->used[i]&&g->miis[i].value[46])favorites++;
        if(favorites>=10){
            e->status="You can save up to ten favorites.";
            return 0;
        }
    }
    e->draft.value[46]=e->draft.value[46]?0:1;
    if(!mds_editor_save(e,persist,ctx)){
        /* mds_editor_save rolls back gallery metadata and saved record.
         * Restore the transient draft too: no unsaved Favorite change. */
        e->draft=e->baseline;
        return 0;
    }
    e->status=e->draft.value[46]?"Favorite added.":"Favorite removed.";
    return 1;
}

int mds_editor_copy(MdsEditor*e,MdsPersist persist,void*ctx)
{
 MdsGallery*g=e->gallery;
 if(e->slot>=MDS_SLOTS||!g->used[e->slot]){e->status="Choose a saved Mii to copy.";return 0;}
 if((g->miis[e->slot].value[61]&2)||!g->miis[e->slot].value[48]){e->status="Copying is not allowed.";return 0;}
 unsigned dest=0;while(dest<MDS_SLOTS&&g->used[dest])dest++;
 if(dest==MDS_SLOTS){e->status="All 100 Mii slots are occupied";return 0;}
 MdsAvatar prior=g->miis[dest],copy=g->miis[e->slot];uint32_t generation=g->generation;int bank=g->active_bank;
 copy.value[51]=0;copy.value[46]=0;copy.value[61]=0;
 if(!mds_gallery_store(g,dest,&copy))return 0;
 if(!persist||!persist(g,ctx)){g->miis[dest]=prior;g->used[dest]=0;g->generation=generation;g->active_bank=bank;e->status="Copy failed. Original retained.";return 0;}
 e->slot=dest;reload(e);e->status="Mii copied.";return 1;
}

int mds_editor_import(MdsEditor*e,const MdsAvatar*source,MdsPersist persist,void*ctx)
{
 if(!source||!mds_valid(source)){e->status="Invalid Mii data.";return 0;}
 static const unsigned days[]={0,31,29,31,30,31,30,31,31,30,31,30,31};
 unsigned month=source->value[49],day=source->value[50];uint8_t name[20];
 if(((month||day)&&(!month||!day||day>days[month]))||!source->name[0]||!mds_name_to_utf16(name,source->name)||!mds_name_to_utf16(name,source->creator)){e->status="Invalid Mii profile.";return 0;}
 MdsGallery*g=e->gallery;unsigned dest=0;while(dest<MDS_SLOTS&&g->used[dest])dest++;
 if(dest==MDS_SLOTS){e->status="All 100 Mii slots are occupied";return 0;}
 MdsAvatar old=g->miis[dest],copy=*source;uint32_t generation=g->generation;int bank=g->active_bank;
 copy.value[51]=0;copy.value[46]=0;copy.value[61]=(source->value[61]&2)|1;
 if(!mds_gallery_store(g,dest,&copy)){e->status="Invalid Mii data.";return 0;}
 if(!persist||!persist(g,ctx)){
  g->miis[dest]=old;g->used[dest]=0;g->generation=generation;g->active_bank=bank;e->status="Import failed. Gallery retained.";return 0;
 }
 e->slot=dest;reload(e);e->status="Mii imported.";return 1;
}
