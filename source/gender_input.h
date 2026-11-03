#ifndef MDS_GENDER_INPUT_H
#define MDS_GENDER_INPUT_H
/* Keep first-boot Personal Mii creation mandatory while giving B priority
 * over simultaneous A/touch; optional creation may cancel without mutation.
 * Touch choice is -1 if no valid male/female button was pressed. */
typedef enum {
 MDS_GENDER_NONE=0,
 MDS_GENDER_CHOOSE,
 MDS_GENDER_BACK,
 MDS_GENDER_MANDATORY
} MdsGenderAction;
MdsGenderAction mds_gender_action(int b_down,int a_down,
                                  int touch_choice,int selected,
                                  int mandatory,int *chosen);
#endif
