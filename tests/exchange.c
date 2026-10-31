#include "exchange.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include "cfs_fixture.h"
static MdsImport browser;
static void write_file(const char*path,const void*p,size_t n){FILE*f=fopen(path,"wb");assert(f);assert(fwrite(p,1,n,f)==n);assert(!fclose(f));}
int main(int argc,char**argv){
 assert(argc==2);char path[256];
 assert(!mds_import_scan(&browser,"/nonexistent/mii-maker-import-test"));assert(!browser.count&&!browser.valid);
 snprintf(path,sizeof path,"%s/00-broken.cfsd",argv[1]);write_file(path,cfs_fixture,95);
 snprintf(path,sizeof path,"%s/02-valid.cfsd",argv[1]);write_file(path,cfs_fixture,96);
 snprintf(path,sizeof path,"%s/01-valid.FFSD",argv[1]);write_file(path,cfs_fixture,96);
 snprintf(path,sizeof path,"%s/ignored.dat",argv[1]);write_file(path,cfs_fixture,96);
 snprintf(path,sizeof path,"%s/directory.cfsd",argv[1]);assert(!mkdir(path,0700));
 assert(!mds_import_scan(&browser,argv[1]));assert(browser.count==3&&!browser.valid&&!strcmp(browser.files[0],"00-broken.cfsd"));
 assert(mds_import_step(&browser,1)&&browser.selected==1&&browser.valid&&!strcmp(browser.record.avatar.name,"CodecTest"));
 assert(mds_import_step(&browser,-2)&&browser.selected==2);assert(!mds_import_select(&browser,100));assert(!browser.valid);
 for(unsigned i=0;i<105;i++){snprintf(path,sizeof path,"%s/overflow%03u.cfsd",argv[1],i);write_file(path,cfs_fixture,96);}
 mds_import_scan(&browser,argv[1]);assert(browser.count==100&&browser.truncated);
 puts("PASS: CFSD/FFSD scan, extension filtering, folders ignored, sorting, malformed selection, wrapping, file cap and missing directory");
}
