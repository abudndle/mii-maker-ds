#include "transform.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(void){MdsAvatar a;int field=8;mds_new(&a);
 assert(mds_transform_touch(&a,&field,4,"B_Change_00")&&field==14&&a.value[14]==10);
 assert(mds_transform_touch(&a,&field,4,"B_Change_01")&&a.value[14]==9);
 assert(mds_transform_touch(&a,&field,4,"B_Change_03")&&a.value[10]==5);
 assert(mds_transform_touch(&a,&field,4,"B_Change_04")&&a.value[12]==4);
 assert(mds_transform_touch(&a,&field,4,"B_Change_07")&&a.value[13]==7);
 assert(mds_transform_touch(&a,&field,4,"B_Change_09")&&a.value[11]==4);
 assert(mds_transform_touch(&a,&field,4,"B_ChangeReset")&&a.value[10]==4&&a.value[11]==3&&a.value[12]==3);
 a.value[14]=0;assert(mds_transform_touch(&a,&field,4,"B_Change_01")&&a.value[14]==0);
 a.value[10]=7;assert(mds_transform_touch(&a,&field,4,"B_Change_03")&&a.value[10]==7);
 assert(mds_transform_touch(&a,&field,7,"B_Change_05")&&field==28&&a.value[28]==4);
 assert(mds_transform_touch(&a,&field,11,"B_Change_04")&&field==41&&a.value[41]==9);
 assert(!mds_transform_touch(&a,&field,1,"B_Change_03"));assert(!mds_transform_touch(&a,&field,50,"B_Change_03"));
 const char *(*map)(unsigned,int,int)=mds_transform_button_for_field;
 assert(!strcmp(map(4,14,1),"B_Change_00"));
 assert(!strcmp(map(4,14,-1),"B_Change_01"));
 assert(!strcmp(map(4,10,-1),"B_Change_02"));
 assert(!strcmp(map(4,10,1),"B_Change_03"));
 assert(!strcmp(map(4,12,1),"B_Change_04"));
 assert(!strcmp(map(4,12,-1),"B_Change_05"));
 assert(!strcmp(map(4,13,-1),"B_Change_06"));
 assert(!strcmp(map(4,13,1),"B_Change_07"));
 assert(!strcmp(map(4,11,-1),"B_Change_08"));
 assert(!strcmp(map(4,11,1),"B_Change_09"));
 assert(!strcmp(map(5,21,1),"B_Change_00"));
 assert(!strcmp(map(7,28,-1),"B_Change_04"));
 assert(!strcmp(map(7,28,1),"B_Change_05"));
 assert(!strcmp(map(11,41,1),"B_Change_04"));
 assert(!strcmp(map(11,41,-1),"B_Change_05"));
 assert(!strcmp(map(3,7,1),"B_Change_04"));
 assert(map(3,7,-1)==NULL);
 assert(map(4,8,1)==NULL); /* Eye selection uses original select clip. */
 assert(map(4,9,-1)==NULL);/* Color palette has no change-button press. */
 assert(map(4,14,0)==NULL);
 assert(map(13,14,1)==NULL);
 puts("PASS: original transform icon semantics, field routing, bounded limits and reset");}
