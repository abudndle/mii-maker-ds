#define _POSIX_C_SOURCE 200809L
#include "backup.h"
#include "save_compact.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>
int mds_backup_scan(MdsBackupBrowser *browser,const char *directory)
{
 memset(browser,0,sizeof *browser);browser->status="No gallery backups found.";
 if(!directory||strlen(directory)>=sizeof browser->directory){browser->status="Backup folder path is too long.";return 0;}
 strcpy(browser->directory,directory);
 DIR *folder=opendir(directory);
 if(!folder){browser->status="Could not open backup folder.";return 0;}
 uint8_t present[MDS_BACKUP_LIMIT/8]={0};struct dirent *entry;int failed=0;
 for(;;){
  errno=0;entry=readdir(folder);
  if(!entry){failed=errno!=0;break;}
  const char *name=entry->d_name;
  if(strlen(name)!=16||strncmp(name,"Gallery",7)||strcmp(name+11,".mdsc"))continue;
  unsigned id=0;int valid=1;
  for(unsigned i=7;i<11;i++){if(name[i]<'0'||name[i]>'9'){valid=0;break;}id=id*10+(unsigned)(name[i]-'0');}
  if(!valid)continue;
  char path[128];struct stat info;snprintf(path,sizeof path,"%.95s/%.16s",directory,name);
  if(stat(path,&info)||!S_ISREG(info.st_mode))continue;
  present[id/8]|=(uint8_t)(1u<<(id%8));
 }
 if(closedir(folder))failed=1;
 if(failed){browser->status="Could not read backup folder.";return 0;}
 for(unsigned i=MDS_BACKUP_LIMIT;i-->0;)if(present[i/8]&(1u<<(i%8)))browser->ids[browser->count++]=(uint16_t)i;
 if(browser->count)browser->status="Choose a backup to preview.";
 return 1;
}
void mds_backup_step(MdsBackupBrowser *browser,int direction)
{
 if(!browser->count)return;
 int count=(int)browser->count;
 browser->selected=(unsigned)(((int)browser->selected+direction%count+count)%count);
}
int mds_backup_path(const MdsBackupBrowser *browser,char *path,size_t size)
{
 if(!path||!size)return 0;
 path[0]=0;
 if(!browser->count||browser->selected>=browser->count||browser->ids[browser->selected]>=MDS_BACKUP_LIMIT)return 0;
 int length=snprintf(path,size,"%s/Gallery%04u.mdsc",browser->directory,browser->ids[browser->selected]);
 if(length<0||(size_t)length>=size){path[0]=0;return 0;}
 return 1;
}
MdsBackupResult mds_backup_export(const MdsGallery *gallery,const char *directory,char *path,size_t path_size)
{
 if(!path||!path_size)return MDS_BACKUP_PATH;
 path[0]=0;
 if(!gallery)return MDS_BACKUP_INVALID;
 if(!directory||!directory[0]||strlen(directory)>220||path_size<strlen(directory)+18)return MDS_BACKUP_PATH;
 uint8_t *data=malloc(MDS_COMPACT_SIZE*2);
 if(!data)return MDS_BACKUP_MEMORY;
 if(!mds_compact_encode(gallery,data,MDS_COMPACT_SIZE)){free(data);return MDS_BACKUP_INVALID;}
 if(mkdir(directory,0777)&&errno!=EEXIST){free(data);return MDS_BACKUP_FOLDER;}
 struct stat folder;
 if(stat(directory,&folder)||!S_ISDIR(folder.st_mode)){free(data);return MDS_BACKUP_FOLDER;}
 char candidate[256];int fd=-1;
 for(unsigned i=0;i<10000;i++){
  snprintf(candidate,sizeof candidate,"%s/Gallery%04u.mdsc",directory,i);
  fd=open(candidate,O_WRONLY|O_CREAT|O_EXCL,0666);
  if(fd>=0)break;
  if(errno!=EEXIST){free(data);return MDS_BACKUP_WRITE;}
 }
 if(fd<0){free(data);return MDS_BACKUP_FULL;}
 MdsBackupResult result=MDS_BACKUP_WRITE;
 FILE *file=fdopen(fd,"wb");
 if(!file){close(fd);goto fail;}
 int written=fwrite(data,1,MDS_COMPACT_SIZE,file)==MDS_COMPACT_SIZE;
 if(fflush(file))written=0;
 if(fclose(file))written=0;
 if(!written)goto fail;
 result=MDS_BACKUP_VERIFY;
 file=fopen(candidate,"rb");
 if(!file)goto fail;
 int verified=fread(data+MDS_COMPACT_SIZE,1,MDS_COMPACT_SIZE,file)==MDS_COMPACT_SIZE&&
              fgetc(file)==EOF&&!ferror(file)&&!memcmp(data,data+MDS_COMPACT_SIZE,MDS_COMPACT_SIZE);
 if(fclose(file))verified=0;
 if(!verified)goto fail;
 memcpy(path,candidate,strlen(candidate)+1);free(data);return MDS_BACKUP_OK;
fail:
 remove(candidate);free(data);return result;
}
const char *mds_backup_message(MdsBackupResult result)
{
 switch(result){
 case MDS_BACKUP_OK:return "Gallery backup saved and verified.";
 case MDS_BACKUP_INVALID:return "Invalid gallery: backup refused.";
 case MDS_BACKUP_MEMORY:return "Not enough memory for backup.";
 case MDS_BACKUP_PATH:return "Backup path is unavailable.";
 case MDS_BACKUP_FOLDER:return "Could not create backup folder.";
 case MDS_BACKUP_FULL:return "Backup filenames are occupied.";
 case MDS_BACKUP_VERIFY:return "Backup readback failed.";
 default:return "Could not write gallery backup.";
 }
}
