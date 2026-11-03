#include "gender_input.h"
MdsGenderAction mds_gender_input(int cancel,int confirm,int left,int right,
                                  int touched_gender,int current_choice)
{
 if(cancel)return MDS_GENDER_CANCEL;
 if(touched_gender==0)return MDS_GENDER_MALE;
 if(touched_gender==1)return MDS_GENDER_FEMALE;
 if(confirm){
  if(current_choice==0)return MDS_GENDER_MALE;
  if(current_choice==1)return MDS_GENDER_FEMALE;
  return MDS_GENDER_NONE;
 }
 if(left&&!right)return MDS_GENDER_PREV;
 if(right&&!left)return MDS_GENDER_NEXT;
 return MDS_GENDER_NONE;
}
