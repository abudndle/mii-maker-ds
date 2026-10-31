#include "editor.h"
#include "save_compact.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
static MdsGallery g;
static int failed(MdsGallery *gallery,void *ctx){(void)ctx;gallery->generation++;gallery->active_bank=1;return 0;}
static int saved(MdsGallery *gallery,void *ctx){(void)gallery;(void)ctx;return 1;}
static MdsGallery original,restored;
static uint8_t save_image[MDS_SAVE_SIZE];
static int compact_transport;
static int committed(MdsGallery *gallery,void *ctx){
    (void)ctx;
    if(!compact_transport)return mds_gallery_commit(gallery,save_image,sizeof save_image);
    if(!mds_compact_encode(gallery,save_image,MDS_COMPACT_SIZE))return 0;
    gallery->generation++;gallery->active_bank=2;return 1;
}
static void restored_sort(void){
    assert(compact_transport?mds_compact_load(&restored,save_image,MDS_COMPACT_SIZE):mds_gallery_load(&restored,save_image,sizeof save_image));
    assert(!memcmp(&g,&restored,sizeof g));
}
static void sorting(void)
{
    MdsEditor e;
    memset(save_image,0xff,sizeof save_image);
    mds_gallery_new(&g);
    const unsigned slots[]={2,19,40,75,99};
    const char *names[]={"Zulu","beta","Alpha","alpha","Received"};
    for(unsigned i=0;i<5;i++){
        MdsAvatar a;mds_new(&a);strcpy(a.name,names[i]);
        a.value[5]=(uint8_t)(i+10);a.value[46]=i<2;a.value[51]=i==0;
        if(i==4){a.value[61]=1;a.value[48]=0;}
        assert(mds_gallery_store(&g,slots[i],&a));
    }
    g.settings[3]=27;original=g;
    mds_editor_begin(&e,&g);e.slot=99;assert(mds_editor_request(&e,MDS_EDIT_RELOAD));
    MdsAvatar selected=e.draft;
    assert(mds_editor_request(&e,MDS_EDIT_SORT_NAME));
    assert(!mds_editor_confirm(&e,0,committed,NULL));assert(!memcmp(&g,&original,sizeof g));
    assert(mds_editor_request(&e,MDS_EDIT_SORT_NAME));
    assert(!mds_editor_confirm(&e,1,failed,NULL));
    assert(!memcmp(&g,&original,sizeof g)&&e.slot==99&&!memcmp(&e.draft,&selected,sizeof selected));
    assert(mds_editor_request(&e,MDS_EDIT_SORT_NAME));
    assert(!mds_editor_confirm(&e,1,NULL,NULL));assert(!memcmp(&g,&original,sizeof g));
    e.draft.value[5]++;assert(!mds_editor_request(&e,MDS_EDIT_SORT_NAME));e.draft=e.baseline;
    assert(mds_editor_request(&e,MDS_EDIT_SORT_NAME));assert(mds_editor_confirm(&e,1,committed,NULL));
    const unsigned alphabetical[]={40,75,19,99,2};
    for(unsigned i=0;i<5;i++)assert(g.used[i]&&!memcmp(&g.miis[i],&original.miis[alphabetical[i]],sizeof(MdsAvatar)));
    for(unsigned i=5;i<MDS_SLOTS;i++)assert(!g.used[i]);
    assert(e.slot==3&&!memcmp(&e.draft,&selected,sizeof selected)&&!mds_editor_dirty(&e));
    assert(mds_editor_locked(&e.draft)&&g.miis[4].value[51]);
    assert(!mds_gallery_delete(&g,4));
    restored_sort();
    assert(mds_editor_request(&e,MDS_EDIT_SORT_FAVORITES));assert(mds_editor_confirm(&e,1,committed,NULL));
    const unsigned favorites[]={19,2,40,75,99};
    for(unsigned i=0;i<5;i++)assert(!memcmp(&g.miis[i],&original.miis[favorites[i]],sizeof(MdsAvatar)));
    assert(e.slot==4&&!memcmp(&e.draft,&selected,sizeof selected));
    restored_sort();
    /* Repeating an already sorted request must not require or write storage. */
    original=g;assert(mds_editor_request(&e,MDS_EDIT_SORT_FAVORITES));assert(mds_editor_confirm(&e,1,NULL,NULL));assert(!memcmp(&g,&original,sizeof g));
    mds_gallery_new(&g);mds_editor_begin(&e,&g);
    assert(mds_editor_request(&e,MDS_EDIT_SORT_NAME));assert(mds_editor_confirm(&e,1,NULL,NULL));assert(e.slot==0);
    /* Full galleries, duplicate names and non-ASCII UTF-8 retain every record. */
    memset(save_image,0xff,sizeof save_image);
    for(unsigned i=0;i<MDS_SLOTS;i++){
        MdsAvatar a;mds_new(&a);strcpy(a.name,i%2?"\xc3\x89mile":"Same");a.value[5]=(uint8_t)i;
        assert(mds_gallery_store(&g,i,&a));
    }
    original=g;mds_editor_begin(&e,&g);e.slot=99;assert(mds_editor_request(&e,MDS_EDIT_RELOAD));selected=e.draft;
    assert(mds_editor_request(&e,MDS_EDIT_SORT_NAME));assert(mds_editor_confirm(&e,1,committed,NULL));
    for(unsigned i=0;i<50;i++){
        assert(!memcmp(&g.miis[i],&original.miis[i*2],sizeof(MdsAvatar)));
        assert(!memcmp(&g.miis[i+50],&original.miis[i*2+1],sizeof(MdsAvatar)));
    }
    assert(e.slot==99&&!memcmp(&e.draft,&selected,sizeof selected));
    restored_sort();
}
int main(void){
    sorting();compact_transport=1;sorting();
    MdsEditor e;mds_gallery_new(&g);mds_editor_begin(&e,&g);
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
    puts("PASS: stable name/favorite sorting, both save transports, selection/permissions and failed-sort rollback; dirty navigation, cancellation, failed-save rollback, failed-delete rollback, personal protection, wrap");
}
