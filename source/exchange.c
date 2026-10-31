#include "exchange.h"
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
void mds_import_reset(MdsImport*b){memset(b,0,sizeof *b);b->status="Choose a 96-byte Mii file.";}
static unsigned lower(unsigned c){return c>='A'&&c<='Z'?c+32:c;}
static int supported(const char*s)
{
 size_t n=strlen(s);if(n<6||n>=MDS_IMPORT_FILENAME||strchr(s,'/')||strchr(s,'\\'))return 0;
 const char*ext=s+n-5;
 return ext[0]=='.'&&(lower(ext[1])=='c'||lower(ext[1])=='f')&&lower(ext[2])=='f'&&lower(ext[3])=='s'&&lower(ext[4])=='d';
}
static int compare(const void*a,const void*b){return strcmp(a,b);}
int mds_import_select(MdsImport*b,unsigned selected)
{
 b->valid=0;if(!b->count||selected>=b->count)return 0;b->selected=selected;
 char path[256];snprintf(path,sizeof path,"%.95s/%.95s",b->directory,b->files[selected]);
 FILE*f=fopen(path,"rb");if(!f){b->status="Could not open Mii file.";return 0;}
 uint8_t data[MDS_CFSD_SIZE+1];size_t n=fread(data,1,sizeof data,f);int failed=ferror(f);if(fclose(f))failed=1;
 if(failed||!mds_cfs_decode(&b->record,data,n)){b->status="Invalid or unsupported Mii file.";return 0;}
 b->valid=1;b->status=b->record.avatar.value[48]?"A: Import   B: Back":"A: Import as read-only Mii";return 1;
}
int mds_import_scan(MdsImport*b,const char*directory)
{
 mds_import_reset(b);
 if(!directory||strlen(directory)>=sizeof b->directory){b->status="Import folder path is too long.";return 0;}
 strcpy(b->directory,directory);DIR*d=opendir(directory);
 if(!d){b->status="Put .cfsd files in MiiMaker/Import.";return 0;}
 struct dirent*entry;
 while((entry=readdir(d))){
  if(!supported(entry->d_name))continue;
  char path[256];struct stat st;snprintf(path,sizeof path,"%.95s/%.95s",directory,entry->d_name);
  if(stat(path,&st)||!S_ISREG(st.st_mode))continue;
  if(b->count==MDS_IMPORT_FILES){b->truncated=1;continue;}
  strcpy(b->files[b->count++],entry->d_name);
 }
 closedir(d);qsort(b->files,b->count,sizeof b->files[0],compare);
 if(!b->count){b->status="No .cfsd or .ffsd files found.";return 0;}
 return mds_import_select(b,0);
}
int mds_import_step(MdsImport*b,int delta)
{
 if(!b->count)return 0;
 int n=((int)b->selected+delta)%(int)b->count;if(n<0)n+=(int)b->count;return mds_import_select(b,(unsigned)n);
}
