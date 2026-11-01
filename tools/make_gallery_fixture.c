/* Synthetic 10-character save for private melonDS acceptance tests only.
 * All Mii names and appearance parameters are newly created test fixtures.
 * This code must never be called for a real owner's cartridge save. */
#include "save.h"
#include "save_compact.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv)
{
 if(argc<2||argc>3||(argc==3&&strcmp(argv[2],"--legacy-64k"))){fprintf(stderr,"usage: make_gallery_fixture OUT.sav [--legacy-64k]\n");return 2;}
 static uint8_t bytes[MDS_SAVE_SIZE];
 MdsGallery gallery;
 mds_gallery_new(&gallery);
 memset(bytes,255,sizeof bytes);
 for(unsigned i=0;i<10;i++){
  MdsAvatar a;
  mds_new(&a);
  snprintf(a.name,sizeof a.name,"Test%02u",i);
  a.value[0]=(uint8_t)(i&1u); /* Both original male/female bodies */
  a.value[1]=(uint8_t)(i%6);
  a.value[2]=(uint8_t)(i%12);
  a.value[5]=(uint8_t)((i*13u)%132u);
  a.value[8]=(uint8_t)((i*7u)%60u);
  a.value[43]=(uint8_t)(24+i*9u);
  a.value[44]=(uint8_t)(32+i*7u);
  a.value[45]=(uint8_t)(i%12u);
  a.value[46]=(uint8_t)(i==0u);
  a.value[51]=(uint8_t)(i==0u);
  if(!mds_gallery_store(&gallery,i,&a)){
   fputs("synthetic Mii record validation failed\n",stderr);return 1;
  }
 }
 /* Test the cartridge's real compact EEPROM format by default.
  * melonDS generally chooses a save chip from an existing .sav file size;
  * a 64 KiB legacy file can select a different emulated save type.
  * Keep --legacy-64k for separate dual-bank host regression testing. */
 size_t length=argc==3?MDS_SAVE_SIZE:MDS_COMPACT_SIZE;
 if(length==MDS_COMPACT_SIZE){
  if(!mds_compact_encode(&gallery,bytes,MDS_COMPACT_SIZE)){
   fputs("synthetic 8K EEPROM encode failed\n",stderr);return 1;
  }
 }else if(!mds_gallery_commit(&gallery,bytes,sizeof bytes)||
           !mds_gallery_commit(&gallery,bytes,sizeof bytes)){
  fputs("synthetic 64K save encode failed\n",stderr);return 1;
 }
 MdsGallery restored;
 int read=length==MDS_COMPACT_SIZE?
     mds_compact_load(&restored,bytes,MDS_COMPACT_SIZE):
     mds_gallery_load(&restored,bytes,sizeof bytes);
 if(!read){
  fputs("synthetic EEPROM save roundtrip failed\n",stderr);return 1;
 }
 unsigned total=0,personal=0;
 for(unsigned i=0;i<MDS_SLOTS;i++)if(restored.used[i]){
  total++;personal+=restored.miis[i].value[51]!=0;
  if(i<10&&strncmp(restored.miis[i].name,"Test",4)){
   fputs("synthetic name lost in save codec\n",stderr);return 1;
  }
 }
 if(total!=10||personal!=1||!restored.miis[0].value[51]){
  fputs("synthetic saved characters or gold-crown ownership invalid\n",stderr);return 1;
 }
 FILE *out=fopen(argv[1],"wb");
 if(!out){perror("fixture destination");return 1;}
 int ok=fwrite(bytes,1,length,out)==length;
 if(fclose(out))ok=0;
 if(!ok){fputs("failed to write synthetic test save\n",stderr);return 1;}
 printf("PASS: %zu-byte original-format synthetic EEPROM with 10 Miis and one Personal Mii\n",length);
 return 0;
}
