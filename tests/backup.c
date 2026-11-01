#define _POSIX_C_SOURCE 200809L
#include "backup.h"
#include "save_compact.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>
static MdsGallery gallery,prior,restored;
static uint8_t data[MDS_COMPACT_SIZE];
static void load(const char *path)
{
 FILE *file=fopen(path,"rb");assert(file);
 assert(fread(data,1,sizeof data,file)==sizeof data&&fgetc(file)==EOF);assert(!fclose(file));
 assert(mds_compact_load(&restored,data,sizeof data));
 assert(!memcmp(gallery.used,restored.used,sizeof gallery.used));
 assert(!memcmp(gallery.miis,restored.miis,sizeof gallery.miis));
 assert(!memcmp(gallery.settings,restored.settings,sizeof gallery.settings));
}
int main(int argc,char **argv)
{
 assert(argc==2);char directory[256],path[256],second[256],partial[256];
 snprintf(directory,sizeof directory,"%s/Backups",argv[1]);
 mds_gallery_new(&gallery);
 for(unsigned i=0;i<100;i++){
  MdsAvatar avatar;mds_new(&avatar);snprintf(avatar.name,sizeof avatar.name,"Mii%03u",i);
  for(unsigned f=0;f<MDS_FIELDS;f++)avatar.value[f]=(uint8_t)(i%(mds_fields[f].maximum+1));
  avatar.value[51]=i==0;
  assert(mds_gallery_store(&gallery,i,&avatar));
 }
 strcpy(gallery.miis[0].name,"\xe6\x97\xa5\xe6\x9c\xac\xf0\x9f\x98\x80");
 gallery.settings[2]=27;gallery.generation=91;gallery.active_bank=1;prior=gallery;
 assert(mds_backup_export(&gallery,directory,path,sizeof path)==MDS_BACKUP_OK);load(path);
 assert(restored.generation==92&&!memcmp(&prior,&gallery,sizeof gallery));
 assert(mds_backup_export(&gallery,directory,second,sizeof second)==MDS_BACKUP_OK);
 assert(strcmp(path,second));load(path);load(second);
 /* A partial filesystem write must remove only its own incomplete file. */
 struct rlimit limit,small;assert(!getrlimit(RLIMIT_FSIZE,&limit));small=limit;small.rlim_cur=1024;
 void (*handler)(int)=signal(SIGXFSZ,SIG_IGN);assert(handler!=SIG_ERR);
 assert(!setrlimit(RLIMIT_FSIZE,&small));
 assert(mds_backup_export(&gallery,directory,partial,sizeof partial)==MDS_BACKUP_WRITE);
 assert(!setrlimit(RLIMIT_FSIZE,&limit));assert(signal(SIGXFSZ,handler)!=SIG_ERR);
 assert(!partial[0]);load(path);load(second);
 /* The failed file was cleaned up; its unique name can be used next time. */
 assert(mds_backup_export(&gallery,directory,partial,sizeof partial)==MDS_BACKUP_OK);load(partial);
 assert(strstr(partial,"Gallery0002.mdsc"));
 char invalid[256];assert(mds_backup_export(NULL,directory,invalid,sizeof invalid)==MDS_BACKUP_INVALID);
 assert(mds_backup_export(&gallery,directory,invalid,2)==MDS_BACKUP_PATH);
 gallery.miis[0].value[5]=255;
 assert(mds_backup_export(&gallery,directory,invalid,sizeof invalid)==MDS_BACKUP_INVALID&&!invalid[0]);
 gallery=prior;
 assert(mds_backup_export(&gallery,path,invalid,sizeof invalid)==MDS_BACKUP_FOLDER);
 char missing[256];snprintf(missing,sizeof missing,"%s/missing/child",argv[1]);
 assert(mds_backup_export(&gallery,missing,invalid,sizeof invalid)==MDS_BACKUP_FOLDER);
 data[100]^=1;assert(!mds_compact_load(&restored,data,sizeof data));
 assert(!memcmp(&gallery,&prior,sizeof gallery));
 for(int result=MDS_BACKUP_OK;result<=MDS_BACKUP_VERIFY;result++)assert(mds_backup_message((MdsBackupResult)result)[0]);
 puts("PASS: verified 100-slot Unicode backup, complete records/settings, unique files, partial-write cleanup, invalid paths/data and unchanged cartridge gallery");
}
