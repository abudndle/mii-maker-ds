#include "avatar.h"
#include "camera_action.h"
#include <assert.h>
#include <string.h>
int main(void)
{
 MdsAvatar original,male,female,invalid;
 mds_new(&original);
 original.value[51]=1;original.value[46]=1;
 original.value[47]=0;original.value[48]=1;
 original.value[49]=12;original.value[50]=25;
 original.value[43]=93;original.value[44]=39;
 original.value[61]=2;
 strcpy(original.name,"Personal");
 strcpy(original.creator,"Test");
 male=original;female=original;
 assert(mds_creation_default(&male,0));
 assert(mds_creation_default(&female,1));
 assert(mds_valid(&male)&&mds_valid(&female));
 assert(male.value[0]==0&&female.value[0]==1);
 assert(male.value[5]!=female.value[5]);
 assert(male.value[8]!=female.value[8]);
 assert(male.value[2]!=female.value[2]);
 for(unsigned i=43;i<MDS_FIELDS;i++){
  assert(male.value[i]==original.value[i]);
  assert(female.value[i]==original.value[i]);
 }
 assert(!memcmp(male.name,original.name,MDS_NAME));
 assert(!memcmp(female.creator,original.creator,MDS_NAME));
 invalid=original;
 assert(!mds_creation_default(&invalid,2));
 assert(!memcmp(&invalid,&original,sizeof original));
 assert(!mds_creation_default(0,0));
 /* Corrupt imported drafts must fail atomically, including identity and
  * sharing fields that a starter reset intentionally preserves. */
 invalid=original;
 invalid.value[48]=255;
 MdsAvatar corrupt=invalid;
 assert(!mds_creation_default(&invalid,1));
 assert(!memcmp(&invalid,&corrupt,sizeof invalid));
 invalid=original;
 invalid.value[5]=255;
 corrupt=invalid;
 assert(!mds_creation_default(&invalid,0));
 assert(!memcmp(&invalid,&corrupt,sizeof invalid));
 invalid=original;
 memset(invalid.name,'X',sizeof invalid.name);
 corrupt=invalid;
 assert(!mds_creation_default(&invalid,1));
 assert(!memcmp(&invalid,&corrupt,sizeof invalid));
 /* Calling with the same gender reinitializes appearance consistently. */
 male.value[5]=100;
 assert(mds_creation_default(&male,0)&&male.value[5]==0);
 enum {A=1u<<0,B=1u<<1,X=1u<<10};
 assert(mds_camera_action(0,0)==MDS_CAMERA_ACTION_NONE);
 assert(mds_camera_action(X,0)==MDS_CAMERA_ACTION_SUGGEST);
 assert(mds_camera_action(X,1)==MDS_CAMERA_ACTION_NONE);
 assert(mds_camera_action(A|X,0)==MDS_CAMERA_ACTION_CAPTURE);
 assert(mds_camera_action(A|X,1)==MDS_CAMERA_ACTION_CAPTURE);
 assert(mds_camera_action(A|B|X,0)==MDS_CAMERA_ACTION_CLOSE);
 assert(mds_camera_action(B|X,1)==MDS_CAMERA_ACTION_CLOSE);
 return 0;
}
