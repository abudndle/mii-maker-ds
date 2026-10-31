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
    puts("PASS: dirty navigation, cancellation, failed-save rollback, failed-delete rollback, personal protection, direct creation in empty gallery slots, wrap");
}
