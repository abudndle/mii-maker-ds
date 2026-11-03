#include "avatar.h"
#include <assert.h>
#include <string.h>

int main(void)
{
 MdsAvatar draft,male,female,prior,out;
 mds_new(&draft);
 draft.value[51]=1;draft.value[46]=1;
 draft.value[47]=0;draft.value[48]=1;
 draft.value[49]=7;draft.value[50]=22;
 draft.value[43]=120;draft.value[44]=12;
 draft.value[45]=8;draft.value[61]=2;
 strcpy(draft.name,"Personal");
 strcpy(draft.creator,"Owner");
 prior=draft;
 assert(mds_creation_preview(&draft,0,&male));
 assert(mds_creation_preview(&draft,1,&female));
 assert(mds_valid(&male)&&mds_valid(&female));
 assert(!memcmp(&draft,&prior,sizeof draft));
 assert(male.value[0]==0&&female.value[0]==1);
 assert(male.value[5]!=female.value[5]);
 assert(male.value[8]!=female.value[8]);
 for(unsigned i=43;i<MDS_FIELDS;i++){
  assert(male.value[i]==prior.value[i]);
  assert(female.value[i]==prior.value[i]);
 }
 assert(!strcmp(male.name,prior.name));
 assert(!strcmp(female.creator,prior.creator));
 out=male;
 assert(!mds_creation_preview(&draft,2,&out));
 assert(!memcmp(&out,&male,sizeof out));
 assert(!mds_creation_preview(0,0,&out));
 assert(!mds_creation_preview(&draft,0,0));
 /* A previous Mii must never be consumed or reset merely to draw preview. */
 assert(!memcmp(&draft,&prior,sizeof draft));
 MdsAvatar invalid=draft;
 invalid.value[5]=255;
 assert(!mds_creation_preview(&invalid,0,&out));
 assert(!memcmp(&out,&male,sizeof out));
 /* Aliasing the draft and output is allowed for explicit staged conversion. */
 out=draft;
 assert(mds_creation_preview(&out,1,&out));
 assert(!memcmp(&out,&female,sizeof out));
 return 0;
}
