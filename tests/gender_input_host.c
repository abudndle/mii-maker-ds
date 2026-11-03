#include "gender_input.h"
#include <assert.h>
int main(void)
{
 int selected=19;
 assert(mds_gender_action(0,0,-1,1,1,&selected)==MDS_GENDER_NONE);
 assert(selected==-1);
 assert(mds_gender_action(0,1,-1,0,1,&selected)==MDS_GENDER_CHOOSE);
 assert(selected==0);
 assert(mds_gender_action(0,1,1,0,0,&selected)==MDS_GENDER_CHOOSE);
 assert(selected==1);
 assert(mds_gender_action(0,1,-1,1,0,&selected)==MDS_GENDER_CHOOSE);
 assert(selected==1);
 assert(mds_gender_action(0,0,0,1,1,&selected)==MDS_GENDER_CHOOSE);
 assert(selected==0);
 assert(mds_gender_action(1,1,1,0,1,&selected)==MDS_GENDER_MANDATORY);
 assert(selected==-1);
 assert(mds_gender_action(1,1,0,1,0,&selected)==MDS_GENDER_BACK);
 assert(selected==-1);
 assert(mds_gender_action(1,0,-1,0,0,&selected)==MDS_GENDER_BACK);
 assert(selected==-1);
 assert(mds_gender_action(0,1,2,1,0,&selected)==MDS_GENDER_CHOOSE);
 assert(selected==1);
 assert(mds_gender_action(0,0,2,1,0,&selected)==MDS_GENDER_NONE);
 assert(selected==-1);
 assert(mds_gender_action(0,1,-1,2,0,&selected)==MDS_GENDER_NONE);
 assert(selected==-1);
 assert(mds_gender_action(0,1,0,0,0,0)==MDS_GENDER_NONE);
 return 0;
}
