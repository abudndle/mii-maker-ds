#ifndef MDS_GENDER_INPUT_H
#define MDS_GENDER_INPUT_H
/* Gender selection is one transaction per input frame. Cancel wins over
 * confirm/touch, while opposing directions never move selection twice. */
typedef enum {
 MDS_GENDER_NONE=0, MDS_GENDER_PREV, MDS_GENDER_NEXT,
 MDS_GENDER_MALE, MDS_GENDER_FEMALE, MDS_GENDER_CANCEL
} MdsGenderAction;
MdsGenderAction mds_gender_input(int cancel,int confirm,int left,int right,
                                  int touched_gender,int current_choice);
#endif
