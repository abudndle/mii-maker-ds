#include "avatar.h"
#include <string.h>
#include <stdio.h>
const MdsField mds_fields[MDS_FIELDS]={
 {"Gender",1,0},{"Skin",5,1},{"Face shape",11,0},{"Wrinkles",11,0},{"Makeup",11,0},
 {"Hair style",131,0},{"Hair color",7,0},{"Hair flip",1,0},
 {"Eye style",59,0},{"Eye color",5,0},{"Eye size",7,4},{"Eye stretch",6,3},{"Eye rotation",7,3},{"Eye spacing",12,6},{"Eye height",18,9},
 {"Brow style",23,0},{"Brow color",7,0},{"Brow size",8,4},{"Brow stretch",6,3},{"Brow rotation",11,6},{"Brow spacing",12,6},{"Brow height",18,9},
 {"Nose style",17,0},{"Nose size",8,4},{"Nose height",18,9},
 {"Mouth style",35,0},{"Lip color",4,0},{"Mouth size",8,4},{"Mouth stretch",6,3},{"Mouth height",18,9},
 {"Glasses",8,0},{"Glasses color",5,0},{"Glasses size",7,4},{"Glasses height",20,10},
 {"Mustache",5,0},{"Beard",3,0},{"Facial hair color",7,0},{"Mustache size",8,4},{"Mustache height",16,8},
 {"Mole",1,0},{"Mole size",8,4},{"Mole X",16,8},{"Mole Y",30,15},
 {"Height",127,64},{"Build",127,64},{"Favorite color",11,0},{"Favorite",1,0},{"Sharing allowed",1,1},{"Copy allowed",1,1},
 {"Birthday month",12,0},{"Birthday day",31,0},{"Personal Mii",1,0},
 {"Name char 1",95,45},{"Name char 2",95,73},{"Name char 3",95,73},{"Name char 4",95,0},{"Name char 5",95,0},
 {"Creator char 1",95,0},{"Creator char 2",95,0},{"Creator char 3",95,0},{"Creator char 4",95,0},{"Import status",3,0}
};
/* Last ten fields offer a basic console input UI. Full UTF-8 names live separately. */
void mds_new(MdsAvatar *a){if(!a)return;memset(a,0,sizeof *a);strcpy(a->name,"Mii");for(unsigned i=0;i<MDS_FIELDS;i++)a->value[i]=mds_fields[i].initial;}
/* Creation-only provisional starting presets. These are not extracted
 * Nintendo 3DS parameter bytes; a private source-asset comparison is still
 * needed. The female start has a visibly different hairstyle, eyes and
 * shape, rather than just changing the gender bit of the male draft. */
int mds_creation_default(MdsAvatar *avatar,unsigned gender)
{
    /* Reject corrupt drafts before changing any fields. A fresh starter must
     * never launder invalid saved identity/permission bytes into an apparently
     * valid avatar, nor partially rewrite the caller on failure. */
    if(!avatar||gender>1u||!mds_valid(avatar))return 0;
    MdsAvatar initial;
    mds_new(&initial);
    /* Only a fresh creation draft should use these appearance defaults.
     * Preserve name, birthday, Personal crown, Favorite, permissions,
     * import state, height and build from the existing draft. */
    for(unsigned i=1u;i<=42u;i++)
        avatar->value[i]=initial.value[i];
    avatar->value[0]=(uint8_t)gender;
    if(gender){
        avatar->value[2]=1; /* rounded face */
        avatar->value[5]=36;/* medium-length female starting hair */
        avatar->value[6]=1;
        avatar->value[8]=4; /* female starting eye shape */
        avatar->value[15]=2;
        avatar->value[25]=3;
    }else{
        avatar->value[2]=0;
        avatar->value[5]=0; /* short male starting hair */
        avatar->value[6]=1;
        avatar->value[8]=0;
        avatar->value[15]=0;
        avatar->value[25]=0;
    }
    return 1;
}
int mds_creation_preview(const MdsAvatar *draft,unsigned gender,MdsAvatar *out)
{
    if(!draft||!out||gender>1u||!mds_valid(draft))return 0;
    MdsAvatar staged=*draft;
    if(!mds_creation_default(&staged,gender))return 0;
    *out=staged;
    return 1;
}
int mds_valid(const MdsAvatar *a){if(!a)return 0;if(!memchr(a->name,0,MDS_NAME)||!memchr(a->creator,0,MDS_NAME))return 0;for(unsigned i=0;i<MDS_FIELDS;i++)if(a->value[i]>mds_fields[i].maximum)return 0;return 1;}
void mds_adjust(MdsAvatar *a,unsigned f,int d){if(!a||f>=MDS_FIELDS)return;int n=mds_fields[f].maximum+1;int64_t v=((int64_t)a->value[f]+d)%n;a->value[f]=(uint8_t)(v<0?v+n:v);if(f>=52&&f<61){char *s=f<57?a->name:a->creator;unsigned start=f<57?52:57,limit=f<57?5:4;for(unsigned j=0;j<limit;j++)s[j]=(char)(a->value[start+j]+32);s[limit]=0;}}
static uint32_t crc32(const uint8_t *p,size_t n){uint32_t c=~0u;for(size_t i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^(0xedb88320u&-(c&1));}return ~c;}
/* A serialized record is 134 bytes, while a live avatar is smaller.
 * Overlapping buffers would make memcpy undefined during encoding, or
 * overwrite the source packet when a successful decode commits its avatar.
 * Compare relative offsets to avoid overflowing addresses on ARM9. */
static int packet_overlaps_avatar(const MdsAvatar *a,const uint8_t *p)
{
 uintptr_t avatar_addr=(uintptr_t)(const void *)a;
 uintptr_t packet_addr=(uintptr_t)(const void *)p;
 return (packet_addr>=avatar_addr&&packet_addr-avatar_addr<sizeof *a)||
        (packet_addr<avatar_addr&&avatar_addr-packet_addr<MDS_PACKET);
}
int mds_encode(const MdsAvatar *a,uint8_t *p,size_t n){if(!a||!p||n<MDS_PACKET||packet_overlaps_avatar(a,p)||!mds_valid(a))return 0;memcpy(p,"MDS3",4);memcpy(p+4,a->name,32);memcpy(p+36,a->creator,32);memcpy(p+68,a->value,62);uint32_t c=crc32(p,130);for(int i=0;i<4;i++)p[130+i]=(uint8_t)(c>>(8*i));return 1;}
int mds_decode(MdsAvatar *a,const uint8_t *p,size_t n){if(!a||!p||n!=MDS_PACKET||packet_overlaps_avatar(a,p)||(memcmp(p,"MDS2",4)&&memcmp(p,"MDS3",4)))return 0;uint32_t c=0;for(int i=0;i<4;i++)c|=(uint32_t)p[130+i]<<(8*i);if(c!=crc32(p,130))return 0;MdsAvatar tmp;memcpy(tmp.name,p+4,32);memcpy(tmp.creator,p+36,32);memcpy(tmp.value,p+68,62);if(!memcmp(p,"MDS2",4)){tmp.value[61]=0;if(tmp.value[51])tmp.value[46]=1;}if(!mds_valid(&tmp))return 0;*a=tmp;return 1;}
int mds_write(const MdsAvatar *a,const char *path){if(!path)return 0;uint8_t b[MDS_PACKET];if(!mds_encode(a,b,sizeof b))return 0;FILE *f=fopen(path,"wb");if(!f)return 0;int ok=fwrite(b,1,sizeof b,f)==sizeof b;int closed=fclose(f)==0;return ok&&closed;}
int mds_read(MdsAvatar *a,const char *path){if(!a||!path)return 0;uint8_t b[MDS_PACKET+1];FILE *f=fopen(path,"rb");if(!f)return 0;size_t n=fread(b,1,sizeof b,f);fclose(f);return mds_decode(a,b,n);}
int mds_service_available(MdsMode mode,MdsService service,unsigned mask){if((unsigned)service>(unsigned)MDS_WII_LINK)return 0;if(service==MDS_CAMERA&&mode!=MDS_DSI)return 0;return !!(mask&(1u<<service));}
