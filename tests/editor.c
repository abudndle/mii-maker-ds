#include "editor.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static MdsGallery g;
static int failed(MdsGallery *gallery,void *ctx){(void)ctx;gallery->generation++;gallery->active_bank=1;return 0;}
static int saved(MdsGallery *gallery,void *ctx){(void)gallery;(void)ctx;return 1;}
int main(void){
    MdsEditor e;mds_gallery_new(&g);mds_editor_begin(&e,&g);
    /* Gallery A on an empty slot creates there, without saving immediately. */
    assert(!mds_editor_create(NULL,2));
    assert(!mds_editor_create(&e,MDS_SLOTS));
    assert(mds_editor_create(&e,23));
    assert(e.slot==23&&e.field==2&&!e.pending);
    assert(!g.used[23]&&e.draft.value[51]&&e.draft.value[46]);
    assert(mds_editor_dirty(&e));
    /* A second creation cannot silently erase an unfinished draft. */
    e.draft.value[5]=9;
    assert(!mds_editor_create(&e,24)&&e.slot==23&&e.draft.value[5]==9);
    assert(mds_editor_save(&e,saved,NULL)&&g.used[23]&&g.miis[23].value[51]);
    assert(!mds_editor_create(&e,23)); /* occupied slot */
    assert(mds_editor_create(&e,24));
    assert(e.slot==24&&!e.draft.value[51]&&!e.draft.value[46]&&!g.used[24]);
    /* Cancellation in the gender screen can restore the untouched baseline. */
    e.draft=e.baseline;
    assert(!mds_editor_dirty(&e));
    mds_gallery_new(&g);mds_editor_begin(&e,&g);
    e.draft.value[5]=25;assert(mds_editor_dirty(&e));
    assert(mds_editor_request(&e,MDS_EDIT_NEXT));assert(e.pending==MDS_EDIT_NEXT&&e.slot==0);
    assert(!mds_editor_confirm(&e,0,saved,NULL));assert(e.draft.value[5]==25);
    assert(!mds_editor_save(&e,failed,NULL));assert(!g.used[0]&&g.generation==0&&g.active_bank==-1);assert(e.draft.value[5]==25);
    assert(mds_editor_save(&e,saved,NULL));assert(g.used[0]&&g.miis[0].value[5]==25&&!mds_editor_dirty(&e));
    assert(mds_editor_request(&e,MDS_EDIT_DELETE));assert(!mds_editor_confirm(&e,0,saved,NULL));assert(g.used[0]);
    assert(mds_editor_request(&e,MDS_EDIT_DELETE));assert(!mds_editor_confirm(&e,1,failed,NULL));assert(g.used[0]&&g.miis[0].value[5]==25&&g.generation==0&&g.active_bank==-1);
    assert(mds_editor_request(&e,MDS_EDIT_DELETE));assert(mds_editor_confirm(&e,1,saved,NULL));assert(!g.used[0]);
    e.draft.value[51]=1;assert(mds_editor_save(&e,saved,NULL));assert(!mds_editor_request(&e,MDS_EDIT_DELETE));assert(g.used[0]);
    assert(mds_editor_request(&e,MDS_EDIT_PREV));assert(e.slot==99);assert(mds_editor_request(&e,MDS_EDIT_NEXT));assert(e.slot==0);
    mds_gallery_new(&g);mds_editor_begin(&e,&g);
    e.draft.value[49]=2;e.draft.value[50]=30;assert(!mds_editor_save(&e,saved,NULL)&&!g.used[0]);
    e.draft.value[50]=29;assert(mds_editor_save(&e,saved,NULL));
    mds_gallery_new(&g);MdsAvatar favorite;mds_new(&favorite);favorite.value[46]=1;
    for(unsigned i=0;i<10;i++){assert(mds_gallery_store(&g,i,&favorite));}
    mds_editor_begin(&e,&g);e.slot=10;mds_new(&e.draft);e.draft.value[46]=1;assert(!mds_editor_save(&e,saved,NULL)&&!g.used[10]);
    mds_gallery_new(&g);mds_editor_begin(&e,&g);e.draft.value[51]=1;e.draft.value[46]=1;assert(mds_editor_save(&e,saved,NULL));
    g.miis[0].value[48]=0;assert(!mds_editor_copy(&e,saved,NULL)&&!g.used[1]);g.miis[0].value[48]=1;
    assert(!mds_editor_copy(&e,failed,NULL)&&!g.used[1]);assert(mds_editor_copy(&e,saved,NULL)&&e.slot==1&&g.used[1]&&!g.miis[1].value[51]&&!g.miis[1].value[46]);
    assert(g.miis[0].value[51]&&g.miis[0].value[46]);
    mds_gallery_new(&g);mds_editor_begin(&e,&g);MdsAvatar imported;mds_new(&imported);strcpy(imported.name,"Imported");imported.value[51]=imported.value[46]=1;
    imported.value[48]=0;assert(mds_editor_import(&e,&imported,saved,NULL)&&g.used[0]&&mds_editor_locked(&g.miis[0]));assert(!mds_editor_copy(&e,saved,NULL));e.draft.value[5]=1;assert(!mds_editor_save(&e,saved,NULL)&&g.miis[0].value[5]==0);mds_gallery_new(&g);mds_editor_begin(&e,&g);imported.value[48]=1;
    assert(!mds_editor_import(&e,&imported,failed,NULL)&&!g.used[0]&&g.generation==0&&g.active_bank==-1);
    assert(mds_editor_import(&e,&imported,saved,NULL)&&g.used[0]&&!g.miis[0].value[51]&&!g.miis[0].value[46]&&!strcmp(g.miis[0].name,"Imported"));
    imported.value[49]=2;imported.value[50]=30;assert(!mds_editor_import(&e,&imported,saved,NULL)&&!g.used[1]);
    e.slot=0;g.miis[0].value[61]=3;g.miis[0].value[48]=1;assert(!mds_editor_copy(&e,saved,NULL));
    /* DS gallery drag sorting must persist moves and occupied-slot swaps
     * without losing Personal/Favorite/received status or unfinished edits. */
    mds_gallery_new(&g);mds_editor_begin(&e,&g);
    MdsAvatar owner,visitor;
    mds_new(&owner);strcpy(owner.name,"Owner");owner.value[51]=1;owner.value[46]=1;
    mds_new(&visitor);strcpy(visitor.name,"Visitor");visitor.value[61]=3;visitor.value[48]=0;
    assert(mds_gallery_store(&g,8,&owner));
    assert(mds_gallery_store(&g,9,&visitor));
    e.slot=8;assert(mds_editor_request(&e,MDS_EDIT_RELOAD));
    assert(!mds_editor_move(NULL,10,saved,NULL));
    assert(!mds_editor_move(&e,8,saved,NULL));
    assert(!mds_editor_move(&e,MDS_SLOTS,saved,NULL));
    assert(!mds_editor_move(&e,10,failed,NULL));
    assert(e.slot==8&&g.used[8]&&!g.used[10]);
    assert(g.generation==0&&g.active_bank==-1);
    assert(g.miis[8].value[51]&&g.miis[8].value[46]);
    assert(mds_editor_move(&e,10,saved,NULL));
    assert(e.slot==10&&!g.used[8]&&g.used[10]);
    assert(g.miis[10].value[51]&&g.miis[10].value[46]);
    assert(!mds_editor_dirty(&e));
    assert(!mds_editor_move(&e,9,failed,NULL));
    assert(e.slot==10&&g.used[9]&&g.used[10]);
    assert(!strcmp(g.miis[9].name,"Visitor"));
    assert(!strcmp(g.miis[10].name,"Owner"));
    assert(g.generation==0&&g.active_bank==-1);
    assert(mds_editor_move(&e,9,saved,NULL));
    assert(e.slot==9&&g.used[9]&&g.used[10]);
    assert(!strcmp(g.miis[9].name,"Owner"));
    assert(!strcmp(g.miis[10].name,"Visitor"));
    assert(g.miis[9].value[51]&&g.miis[9].value[46]);
    assert(g.miis[10].value[61]==3&&!g.miis[10].value[48]);
    assert(!mds_editor_dirty(&e));
    e.draft.value[5]=25;
    assert(!mds_editor_move(&e,10,saved,NULL));
    assert(e.slot==9&&g.miis[9].value[5]==owner.value[5]);
    e.draft=e.baseline;
    e.pending=MDS_EDIT_DELETE;
    assert(!mds_editor_move(&e,10,saved,NULL));
    e.pending=MDS_EDIT_NONE;
    e.slot=8;assert(mds_editor_request(&e,MDS_EDIT_RELOAD));
    assert(!mds_editor_move(&e,9,saved,NULL));
    assert(!strcmp(g.miis[9].name,"Owner"));
    e.slot=9;assert(mds_editor_request(&e,MDS_EDIT_RELOAD));
    assert(!mds_editor_move(&e,8,NULL,NULL));
    assert(g.used[9]&&!g.used[8]&&e.slot==9);
    assert(g.miis[9].value[51]);
    /* Received Miis may be COPIED for editing, not edited in place, even
     * when their original transfer included copy permission. */
    mds_gallery_new(&g);mds_editor_begin(&e,&g);
    MdsAvatar received;mds_new(&received);
    strcpy(received.name,"Received");
    received.value[61]=1;received.value[48]=1;
    assert(mds_gallery_store(&g,0,&received));
    assert(mds_editor_request(&e,MDS_EDIT_RELOAD));
    assert(mds_editor_locked(&g.miis[0]));
    assert(!mds_editor_save(&e,saved,NULL)); /* source is always read-only */
    assert(mds_editor_request(&e,MDS_EDIT_COPY_RECEIVED));
    assert(e.pending==MDS_EDIT_COPY_RECEIVED&&e.slot==0);
    assert(!mds_editor_request(&e,MDS_EDIT_DELETE)); /* single modal */
    assert(!mds_editor_confirm(&e,0,saved,NULL));
    assert(e.slot==0&&!g.used[1]&&g.miis[0].value[61]==1);
    e.draft.value[5]=18;
    assert(!mds_editor_request(&e,MDS_EDIT_COPY_RECEIVED));
    assert(e.slot==0&&!g.used[1]);
    e.draft=e.baseline;
    assert(mds_editor_request(&e,MDS_EDIT_COPY_RECEIVED));
    assert(!mds_editor_confirm(&e,1,failed,NULL));
    assert(e.slot==0&&!g.used[1]&&g.miis[0].value[61]==1);
    assert(g.generation==0&&g.active_bank==-1);
    assert(mds_editor_request(&e,MDS_EDIT_COPY_RECEIVED));
    assert(mds_editor_confirm(&e,1,saved,NULL));
    assert(e.slot==1&&g.used[1]&&!mds_editor_locked(&g.miis[1]));
    assert(g.miis[0].value[61]==1&&g.miis[0].value[48]==1);
    assert(!g.miis[1].value[61]&&!g.miis[1].value[51]&&!g.miis[1].value[46]);
    assert(!mds_editor_dirty(&e));
    e.draft.value[5]=18;
    assert(mds_editor_save(&e,saved,NULL));
    assert(g.miis[1].value[5]==18&&g.miis[0].value[5]!=18);
    /* Special/locked received Miis may not enter the copy-edit flow. */
    mds_gallery_new(&g);mds_editor_begin(&e,&g);
    received.value[61]=3;
    assert(mds_gallery_store(&g,0,&received));
    assert(mds_editor_request(&e,MDS_EDIT_RELOAD));
    assert(mds_editor_locked(&g.miis[0]));
    assert(!mds_editor_request(&e,MDS_EDIT_COPY_RECEIVED));
    assert(!e.pending&&!g.used[1]);
    received.value[61]=1;received.value[48]=0;
    assert(mds_gallery_store(&g,0,&received));
    assert(mds_editor_request(&e,MDS_EDIT_RELOAD));
    assert(!mds_editor_request(&e,MDS_EDIT_COPY_RECEIVED));
    assert(!e.pending&&!g.used[1]);
    puts("PASS: dirty navigation, failed-save/delete/move rollback, Personal Mii protection, direct creation, gallery sort, received copy-before-edit, wrap");
}
