#define _POSIX_C_SOURCE 200809L
#include "restore.h"
#include "backup.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
static MdsRestore restore;
static MdsBackupBrowser browser;
static MdsGallery gallery,target,prior,decoded;
static uint8_t image[MDS_SAVE_SIZE];
static unsigned calls;
static int failure(MdsGallery *g,void *context){(void)context;calls++;g->generation++;g->active_bank=0;return 0;}
static int persisted(MdsGallery *g,void *context)
{
 calls++;int legacy=*(int *)context;
 assert(g->generation==prior.generation&&g->active_bank==prior.active_bank);
 if(legacy)return mds_gallery_commit(g,image,sizeof image);
 if(!mds_compact_encode(g,image,MDS_COMPACT_SIZE))return 0;
 g->generation++;g->active_bank=2;return 1;
}
static void populate(MdsGallery *g,const char *name)
{
 mds_gallery_new(g);
 for(unsigned i=0;i<MDS_SLOTS;i++){
  MdsAvatar a;mds_new(&a);snprintf(a.name,sizeof a.name,"%s%02u",name,i);
  strcpy(a.creator,"Author");a.value[51]=i==0;a.value[46]=i<3;a.value[5]=(uint8_t)(i%132);
  if(i==99){a.value[61]=1;a.value[48]=0;a.value[47]=0;}
  assert(mds_gallery_store(g,i,&a));
 }
 strcpy(g->miis[0].name,"\xe6\x97\xa5\xe6\x9c\xac");g->settings[3]=42;
}
static void write_file(const char *path,const void *data,size_t size)
{
 FILE *file=fopen(path,"wb");assert(file);assert(fwrite(data,1,size,file)==size);assert(!fclose(file));
}
int main(int argc,char **argv)
{
 assert(argc==2);char directory[256],path[256],candidate[256],safety[256],bad[512];
 snprintf(directory,sizeof directory,"%s/Restore",argv[1]);
 populate(&target,"Old");target.generation=700;
 assert(mds_backup_export(&target,directory,path,sizeof path)==MDS_BACKUP_OK);
 assert(mds_restore_prepare(&restore,path)==MDS_RESTORE_OK);
 populate(&gallery,"Now");gallery.generation=99;gallery.active_bank=1;prior=gallery;
 MdsEditor editor;mds_editor_begin(&editor,&gallery);editor.slot=99;mds_editor_request(&editor,MDS_EDIT_RELOAD);
 MdsEditor before=editor;int legacy=0;
 assert(mds_restore_apply(&restore,&editor,0,directory,persisted,&legacy)==MDS_RESTORE_CANCELLED);
 assert(!calls&&!memcmp(&gallery,&prior,sizeof gallery)&&!memcmp(&before,&editor,sizeof editor));
 editor.draft.value[5]=3;
 assert(mds_restore_apply(&restore,&editor,1,directory,persisted,&legacy)==MDS_RESTORE_BLOCKED&&!calls);
 editor=before;editor.pending=MDS_EDIT_DELETE;
 assert(mds_restore_apply(&restore,&editor,1,directory,persisted,&legacy)==MDS_RESTORE_BLOCKED&&!calls);editor=before;
 assert(mds_restore_apply(&restore,&editor,1,NULL,persisted,&legacy)==MDS_RESTORE_SAFETY_FAILED&&!calls);
 assert(!memcmp(&gallery,&prior,sizeof gallery));
 assert(mds_restore_apply(&restore,&editor,1,directory,failure,NULL)==MDS_RESTORE_WRITE_FAILED&&calls==1);
 assert(!memcmp(&gallery,&prior,sizeof gallery)&&!memcmp(&editor,&before,sizeof editor));
 assert(mds_backup_scan(&browser,directory)&&browser.count==2);
 assert(browser.ids[0]==1&&browser.ids[1]==0);
 char decoy[512];snprintf(decoy,sizeof decoy,"%s/Gallery1234.mdsc",directory);assert(!mkdir(decoy,0777));
 snprintf(decoy,sizeof decoy,"%s/Gallery12xx.mdsc",directory);write_file(decoy,"not a backup",12);
 snprintf(decoy,sizeof decoy,"%s/Other0000.mdsc",directory);write_file(decoy,"not a backup",12);
 assert(mds_backup_scan(&browser,directory)&&browser.count==2);
 assert(mds_backup_path(&browser,safety,sizeof safety));
 MdsRestore old;assert(mds_restore_prepare(&old,safety)==MDS_RESTORE_OK);
 assert(!memcmp(prior.miis,old.gallery.miis,sizeof prior.miis));
 for(legacy=0;legacy<2;legacy++){
  gallery=prior;editor=before;memset(image,255,sizeof image);
  assert(mds_restore_prepare(&restore,path)==MDS_RESTORE_OK);
  assert(mds_restore_apply(&restore,&editor,1,directory,persisted,&legacy)==MDS_RESTORE_OK);
  assert(!restore.prepared&&!mds_editor_dirty(&editor)&&editor.slot==99&&mds_editor_locked(&editor.draft));
  assert(gallery.generation==100);
  assert(legacy?mds_gallery_load(&decoded,image,sizeof image):mds_compact_load(&decoded,image,MDS_COMPACT_SIZE));
  assert(!memcmp(target.miis,decoded.miis,sizeof target.miis)&&!memcmp(target.used,decoded.used,sizeof target.used));
  assert(!memcmp(target.settings,decoded.settings,sizeof target.settings));
 }
 /* Replacing a file after preview is rejected even when the replacement is valid. */
 gallery=prior;mds_editor_begin(&editor,&gallery);
 assert(mds_restore_prepare(&restore,path)==MDS_RESTORE_OK);
 assert(mds_compact_encode(&gallery,image,MDS_COMPACT_SIZE));write_file(path,image,MDS_COMPACT_SIZE);
 unsigned previous_calls=calls;
 assert(mds_restore_apply(&restore,&editor,1,directory,persisted,&legacy)==MDS_RESTORE_CHANGED);
 assert(calls==previous_calls&&!memcmp(&gallery,&prior,sizeof gallery));
 snprintf(bad,sizeof bad,"%s/Gallery9999.mdsc",directory);
 image[50]^=1;write_file(bad,image,MDS_COMPACT_SIZE);
 assert(mds_restore_prepare(&restore,bad)==MDS_RESTORE_INVALID);
 write_file(bad,image,MDS_COMPACT_SIZE-1);assert(mds_restore_prepare(&restore,bad)==MDS_RESTORE_INVALID);
 write_file(bad,image,MDS_COMPACT_SIZE+1);assert(mds_restore_prepare(&restore,bad)==MDS_RESTORE_INVALID);
 /* Empty snapshots are valid, but require the same explicit apply and safety copy. */
 mds_gallery_new(&target);assert(mds_backup_export(&target,directory,candidate,sizeof candidate)==MDS_BACKUP_OK);
 assert(mds_restore_prepare(&restore,candidate)==MDS_RESTORE_OK);legacy=0;
 assert(mds_restore_apply(&restore,&editor,1,directory,persisted,&legacy)==MDS_RESTORE_OK);
 assert(editor.slot==0&&!gallery.used[0]);
 assert(mds_backup_scan(&browser,directory));
 unsigned first=browser.selected;mds_backup_step(&browser,-1);assert(browser.selected==browser.count-1);mds_backup_step(&browser,1);assert(browser.selected==first);
 assert(!mds_backup_path(&browser,candidate,2));
 assert(!mds_backup_scan(&browser,"/no/such/backup/folder")&&!browser.count);
 assert(!mds_backup_path(&browser,candidate,sizeof candidate));
 for(int result=MDS_RESTORE_OK;result<=MDS_RESTORE_MEMORY;result++)assert(mds_restore_message((MdsRestoreResult)result)[0]);
 puts("PASS: explicit restore, verified safety copy, complete Unicode/permission records, compact/legacy bank metadata, cancellation, failed-write rollback, changed/corrupt files and empty gallery");
}
