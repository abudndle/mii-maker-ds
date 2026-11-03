#include "gender_input.h"
#include <assert.h>
int main(void)
{
 assert(mds_gender_input(1,1,1,1,1,0)==MDS_GENDER_CANCEL);
 assert(mds_gender_input(1,0,0,0,-1,0)==MDS_GENDER_CANCEL);
 assert(mds_gender_input(0,0,0,0,0,1)==MDS_GENDER_MALE);
 assert(mds_gender_input(0,0,0,0,1,0)==MDS_GENDER_FEMALE);
 assert(mds_gender_input(0,1,1,0,1,0)==MDS_GENDER_FEMALE);
 assert(mds_gender_input(0,1,0,1,-1,0)==MDS_GENDER_MALE);
 assert(mds_gender_input(0,1,0,1,-1,1)==MDS_GENDER_FEMALE);
 assert(mds_gender_input(0,1,0,0,-1,-1)==MDS_GENDER_NONE);
 assert(mds_gender_input(0,0,1,0,-1,1)==MDS_GENDER_PREV);
 assert(mds_gender_input(0,0,0,1,-1,1)==MDS_GENDER_NEXT);
 assert(mds_gender_input(0,0,1,1,-1,1)==MDS_GENDER_NONE);
 assert(mds_gender_input(0,0,0,0,-1,0)==MDS_GENDER_NONE);
 return 0;
}
