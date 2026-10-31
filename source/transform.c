#include "transform.h"
#include <string.h>
/* Down/Up, Reduction/Enlargement, RotateR/L, Near/Wide,
 * NarrowLength/SpreadLength: meanings taken from original icon resources. */
typedef struct {int y,size,rotation,spacing,stretch,x;} Fields;
static const Fields fields[13]={
 {-1,-1,-1,-1,-1,-1},{-1,-1,-1,-1,-1,-1},{-1,-1,-1,-1,-1,-1},{-1,-1,-1,-1,-1,-1},
 {14,10,12,13,11,-1},{21,17,19,20,18,-1},{24,23,-1,-1,-1,-1},{29,27,-1,-1,28,-1},
 {33,32,-1,-1,-1,-1},{38,37,-1,-1,-1,-1},{-1,-1,-1,-1,-1,-1},{42,40,-1,-1,-1,41},{-1,-1,-1,-1,-1,-1}
};
static void bounded(MdsAvatar*a,int f,int delta){if(f<0)return;int v=a->value[f]+delta;if(v<0)v=0;if(v>mds_fields[f].maximum)v=mds_fields[f].maximum;a->value[f]=(uint8_t)v;}
int mds_transform_touch(MdsAvatar*a,int*field,unsigned category,const char*name)
{
 if(!a||!field||!name||category>=13)return 0;
 Fields c=fields[category];
 if(!strcmp(name,"B_ChangeReset")){
  const int targets[6]={c.y,c.size,c.rotation,c.spacing,c.stretch,c.x};const int *p=targets;int changed=0;for(unsigned i=0;i<6;i++)if(p[i]>=0){a->value[p[i]]=mds_fields[p[i]].initial;changed=1;}
  return changed;
 }
 if(strncmp(name,"B_Change_",9)||strlen(name)!=11||name[9]<'0'||name[9]>'9'||name[10]<'0'||name[10]>'9')return 0;
 unsigned button=(unsigned)(name[9]-'0')*10u+(unsigned)(name[10]-'0');int f=-1,delta=0;
 if(button<2){f=c.y;delta=button==0?1:-1;}
 else if(button<4){f=c.size;delta=button==2?-1:1;}
 else if((category==4||category==5)&&button<10){
  if(button<6){f=c.rotation;delta=button==4?1:-1;}
  else if(button<8){f=c.spacing;delta=button==6?-1:1;}
  else{f=c.stretch;delta=button==8?-1:1;}
 }else if(category==7&&button<6){f=c.stretch;delta=button==4?-1:1;}
 else if(category==11&&button<6){f=c.x;delta=button==4?1:-1;}
 if(f<0)return 0;
 bounded(a,f,delta);*field=f;return 1;
}
