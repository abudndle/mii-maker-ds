#ifndef MDS_TRANSFORM_H
#define MDS_TRANSFORM_H
#include "avatar.h"
/* Category order is generated from original editor layouts. */
int mds_transform_touch(MdsAvatar *,int *,unsigned,const char *);
/* Return the actual source CLYT adjustment button matching a D-pad change.
 * NULL for feature/color fields that have no corresponding change button. */
const char *mds_transform_button_for_field(unsigned category,int field,int direction);
#endif
