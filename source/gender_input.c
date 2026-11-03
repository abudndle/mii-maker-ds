#include "gender_input.h"
MdsGenderAction mds_gender_action(int b_down,int a_down,
                                  int touch_choice,int selected,
                                  int mandatory,int *chosen)
{
 if(chosen)*chosen=-1;
 if(b_down)return mandatory?MDS_GENDER_MANDATORY:MDS_GENDER_BACK;
 /* A valid stylus target takes precedence over a simultaneous A press,
  * but a stray touch never prevents A confirming the current selection. */
 int target=touch_choice>=0&&touch_choice<=1?
            touch_choice:(a_down?selected:-1);
 if(!chosen||target<0||target>1)return MDS_GENDER_NONE;
 *chosen=target;
 return MDS_GENDER_CHOOSE;
}
