#include "restore.h"
#include "backup.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int read_snapshot(const char *path,uint8_t *image)
{
 FILE *file=fopen(path,"rb");if(!file)return 0;
 int valid=fread(image,1,MDS_COMPACT_SIZE,file)==MDS_COMPACT_SIZE&&fgetc(file)==EOF&&!ferror(file);
 if(fclose(file))valid=0;
 return valid;
}
MdsRestoreResult mds_restore_prepare(MdsRestore *restore,const char *path)
{
 restore->prepared=0;
 if(!path||strlen(path)>=sizeof restore->path||!read_snapshot(path,restore->image)||
    !mds_compact_load(&restore->gallery,restore->image,MDS_COMPACT_SIZE))return MDS_RESTORE_INVALID;
 strcpy(restore->path,path);restore->prepared=1;return MDS_RESTORE_OK;
}
MdsRestoreResult mds_restore_apply(MdsRestore *restore,MdsEditor *editor,int accept,
                                 const char *directory,MdsPersist persist,void *context)
{
 if(!accept)return MDS_RESTORE_CANCELLED;
 if(!restore->prepared||!editor||!editor->gallery||editor->pending||mds_editor_dirty(editor)||!persist)
  return MDS_RESTORE_BLOCKED;
 uint8_t *current=malloc(MDS_COMPACT_SIZE);
 if(!current)return MDS_RESTORE_MEMORY;
 int unchanged=read_snapshot(restore->path,current)&&!memcmp(current,restore->image,MDS_COMPACT_SIZE);
 free(current);if(!unchanged){restore->prepared=0;return MDS_RESTORE_CHANGED;}
 MdsGallery *prior=malloc(sizeof *prior);
 if(!prior)return MDS_RESTORE_MEMORY;
 *prior=*editor->gallery;
 char safety[256];
 if(mds_backup_export(prior,directory,safety,sizeof safety)!=MDS_BACKUP_OK){free(prior);return MDS_RESTORE_SAFETY_FAILED;}
 MdsGallery *gallery=editor->gallery;*gallery=restore->gallery;
 /* The cartridge's live generation/bank controls persistence, never the
  * historical backup's metadata or its compact-file bank marker. */
 gallery->generation=prior->generation;gallery->active_bank=prior->active_bank;
 if(!persist(gallery,context)){*gallery=*prior;free(prior);return MDS_RESTORE_WRITE_FAILED;}
 free(prior);
 unsigned selected=editor->slot;
 if(selected>=MDS_SLOTS||!gallery->used[selected]){
  selected=0;while(selected<MDS_SLOTS&&!gallery->used[selected])selected++;
  if(selected==MDS_SLOTS)selected=0;
 }
 mds_editor_begin(editor,gallery);editor->slot=selected;mds_editor_request(editor,MDS_EDIT_RELOAD);
 editor->status="Gallery restored from backup.";restore->prepared=0;return MDS_RESTORE_OK;
}
const char *mds_restore_message(MdsRestoreResult result)
{
 switch(result){
 case MDS_RESTORE_OK:return "Restored. Previous gallery backed up.";
 case MDS_RESTORE_CANCELLED:return "Restore cancelled. Gallery kept.";
 case MDS_RESTORE_INVALID:return "Invalid or damaged backup.";
 case MDS_RESTORE_BLOCKED:return "Save or cancel edits before restore.";
 case MDS_RESTORE_CHANGED:return "Backup changed. Preview it again.";
 case MDS_RESTORE_SAFETY_FAILED:return "Safety backup failed. Restore stopped.";
 case MDS_RESTORE_WRITE_FAILED:return "Write failed. Safety backup retained.";
 default:return "Not enough memory for restore.";
 }
}
