/* Independent DS preview renderer. Uses supplied CFL geometry and native tiled
 * textures; software lighting and orthographic projection are provisional. */
#include "head.h"
#include "view.h"
#include "status.h"
#include <string.h>
#include <math.h>
#include <limits.h>
#define S 128
#define MS 64
static const uint8_t skins[6][3]={{255,211,173},{255,182,107},{222,121,66},{255,170,140},{173,81,41},{99,44,24}};
static const uint8_t hairs[8][3]={{30,26,24},{64,32,16},{92,24,10},{124,58,20},{120,120,128},{78,62,16},{136,88,24},{208,160,74}};
static const uint8_t eyes[6][3]={{0,0,0},{108,112,116},{100,67,39},{96,94,48},{70,84,168},{56,112,88}};
static const uint8_t lips[5][3]={{216,82,8},{240,12,8},{245,72,72},{240,154,116},{140,80,64}};
static const uint8_t lipinner[5][3]={{130,48,24},{120,12,12},{136,32,40},{220,120,80},{70,30,10}};
static const uint8_t glasses[6][3]={{24,24,24},{96,56,16},{168,16,8},{32,48,104},{168,96,0},{120,112,104}};
static const uint8_t shirts[12][3]={{210,30,20},{255,110,25},{255,216,32},{120,210,32},{0,120,48},{10,72,180},{60,170,222},{245,90,125},{115,40,173},{72,56,24},{224,224,224},{24,24,20}};
static const uint8_t dark[3]={18,15,15},white[3]={255,255,255};
static const uint8_t er[60]={29,28,28,28,29,28,28,28,29,28,28,28,28,29,29,28,28,28,29,29,28,29,28,29,29,28,29,28,28,29,28,28,28,29,29,29,28,28,29,29,29,28,28,29,29,29,29,29,29,29,29,29,28,28,28,28,29,28,28,29};
static const uint8_t br[24]={26,26,27,25,26,25,26,25,28,25,26,24,27,27,26,26,25,25,26,26,27,26,25,27};
typedef struct {int x,y,z,u,v,light;} Vertex;
static Vertex verts[4096];
static int depth[S*S];
static uint32_t mask[MS*MS];
static uint8_t mask_key[43];
static const uint8_t *mask_resource;
static int mask_valid;
void mds_render_reset_cache(void){mask_valid=0;mask_resource=NULL;}
static float view_scale=1.35f,view_y=111.f;
static unsigned view_angle;
static const uint8_t *body_model;
static int (*render_abort)(void);
static int render_cancelled;
void mds_render_set_abort(int (*callback)(void)){render_abort=callback;}
static int cancelled(void){if(render_abort&&render_abort())render_cancelled=1;return render_cancelled;}
static float body_height=1,body_width=1;
static unsigned le16(const uint8_t*p){return p[0]|(unsigned)p[1]<<8;}
static int clamp(int v,int hi){return v<0?0:v>hi?hi:v;}
static uint32_t rgba(unsigned r,unsigned g,unsigned b,unsigned a){return r|(g<<8)|(b<<16)|(a<<24);}
static uint32_t texel(const MdsCflTexture*t,int x,int y)
{
 x=clamp(x,(int)t->width-1);y=clamp(y,(int)t->height-1);
 unsigned morton=0;for(unsigned k=0;k<3;k++)morton|=((x>>k)&1)<<(k*2)|((y>>k)&1)<<(k*2+1);
 unsigned i=((y/8)*(t->padded_width/8)+x/8)*64+morton;
 static const unsigned bpp[14]={4,8,4,8,8,16,16,16,24,16,16,32,4,8};
 if(t->format>=14||((size_t)(i+1)*bpp[t->format]+7)/8>t->pixel_bytes)return 0;
 const uint8_t*p=t->pixels;unsigned v;
 switch(t->format){
 case 0:v=(p[i/2]>>((i&1)*4)&15)*17;return rgba(v,v,v,255);
 case 1:v=p[i];return rgba(v,v,v,255);
 case 2:v=(p[i/2]>>((i&1)*4)&15)*17;return rgba(255,255,255,v);
 case 3:return rgba(255,255,255,p[i]);
 case 4:v=p[i];return rgba((v>>4)*17,(v>>4)*17,(v>>4)*17,(v&15)*17);
 case 5:v=le16(p+2*i);return rgba(v>>8,v>>8,v>>8,v&255);
 case 7:v=le16(p+2*i);return rgba((v>>11)*255/31,((v>>5)&63)*255/63,(v&31)*255/31,255);
 case 8:p+=3*i;return rgba(p[2],p[1],p[0],255);
 case 9:v=le16(p+2*i);return rgba((v>>11)*255/31,((v>>6)&31)*255/31,((v>>1)&31)*255/31,(v&1)*255);
 case 10:v=le16(p+2*i);return rgba((v>>12)*17,((v>>8)&15)*17,((v>>4)&15)*17,(v&15)*17);
 case 11:p+=4*i;return rgba(p[3],p[2],p[1],p[0]);
 default:return 0;
 }
}
static uint32_t tint(uint32_t c,const uint8_t*a,const uint8_t*b,int dual)
{
 unsigned r=c&255,g=c>>8&255,bl=c>>16&255,alpha=c>>24,out[3];
 for(int k=0;k<3;k++){
  if(dual==1)out[k]=clamp((a[k]*r+b[k]*bl)/255+g,255);
  else if(dual==2)out[k]=clamp((a[k]*r+b[k]*g)/255+bl,255);
  else out[k]=a[k]*r/255;
 }
 return rgba(out[0],out[1],out[2],alpha);
}
static void decal(const MdsCflArchive*a,unsigned sec,unsigned id,float cx,float cy,float w,float h,float rot,int origin,const uint8_t*c0,const uint8_t*c1,int dual)
{
 MdsCflItem item;MdsCflTexture tex;
 if(!mds_cfl_item(a,sec,id,&item)||!mds_cfl_texture(&item,&tex))return;
 float angle=rot*0.19634954085f,co=cosf(angle),si=sinf(angle);
 /* Invert the resource's 64-unit mask placement, with mirrored paired features. */
 float offset=origin==0?-.5f:origin==1?0.f:-1.f;
 /* Fixed-point affine stepping keeps software floating point out of pixel loops. */
 int ux=(int)(co/(w*.88961464f)*65536),uy=(int)(si/(w*.9276675f)*65536);
 int vx=(int)(-si/(h*.88961464f)*65536),vy=(int)(co/(h*.9276675f)*65536);
 int u0=(int)(((-cx/.88961464f*co-cy/.9276675f*si)/w-offset)*65536);
 int v0=(int)(((cx/.88961464f*si-cy/.9276675f*co)/h+.5f)*65536);
 for(int y=0;y<MS;y++)for(int x=0;x<MS;x++){
  if(!x&&!(y%8)&&cancelled())return;
  int u=u0+x*ux+y*uy,v=v0+x*vx+y*vy;
  if(u<0||u>=65536||v<0||v>=65536)continue;
  if(origin==1)u=65535-u;
  uint32_t c=tint(texel(&tex,u*(int)tex.width/65536,v*(int)tex.height/65536),c0,c1,dual);
  unsigned alpha=c>>24;if(!alpha)continue;
  uint32_t old=mask[y*MS+x];unsigned olda=old>>24,oa=alpha+olda*(255-alpha)/255;
  unsigned rgb[3];for(unsigned k=0;k<3;k++)rgb[k]=(((c>>(8*k)&255)*alpha)+((old>>(8*k)&255)*olda*(255-alpha)/255))/(oa?oa:1);
  mask[y*MS+x]=rgba(rgb[0],rgb[1],rgb[2],oa);
 }
}
/* Keep projected model vertices bounded before int conversion and raster edges.
 * The 128px preview cannot display coordinates beyond this guard band. */
static int screen_coordinate(int64_t numerator,int64_t denominator)
{
 int64_t v=numerator/denominator;
 if(v>1024)return 1024;
 if(v< -1024)return -1024;
 return (int)v;
}
static int edge(Vertex a,Vertex b,int x,int y){return (b.x-a.x)*(y-a.y)-(b.y-a.y)*(x-a.x);}
/* Affine attributes use 16 fractional bits. Divide at triangle setup, then
 * step across pixels with additions; DS ARM9 has no instruction-level divide. */
static int64_t plane(int a,int b,int c,int wa,int wb,int wc,int inverse)
{
 return ((int64_t)a*wa+(int64_t)b*wb+(int64_t)c*wc)*inverse/256;
}
static void triangle(Vertex a,Vertex b,Vertex c,const uint8_t*color,int masked,const MdsCflTexture*tex,uint16_t*out)
{
 /* Cheap screen-space reject before costly affine setup and rasterization.
  * Keep all original model vertices/triangles; only invisible primitives skip. */
 if((a.x<0&&b.x<0&&c.x<0)||(a.x>=S&&b.x>=S&&c.x>=S)||
    (a.y<0&&b.y<0&&c.y<0)||(a.y>=S&&b.y>=S&&c.y>=S))return;
 int area=edge(a,b,c.x,c.y);if(!area)return;if(area<0){Vertex tmp=b;b=c;c=tmp;area=-area;}
 int x0=clamp(a.x<b.x?(a.x<c.x?a.x:c.x):(b.x<c.x?b.x:c.x),127),x1=clamp(a.x>b.x?(a.x>c.x?a.x:c.x):(b.x>c.x?b.x:c.x),127);
 int y0=clamp(a.y<b.y?(a.y<c.y?a.y:c.y):(b.y<c.y?b.y:c.y),127),y1=clamp(a.y>b.y?(a.y>c.y?a.y:c.y):(b.y>c.y?b.y:c.y),127);
 int inverse=(int)((16777216u+(unsigned)area/2)/(unsigned)area);
 int ax=b.y-c.y,bx=c.y-a.y,cx=a.y-b.y,ay=c.x-b.x,by=a.x-c.x,cy=b.x-a.x;
 int ar=edge(b,c,x0,y0),brw=edge(c,a,x0,y0),cr=edge(a,b,x0,y0);
 int64_t zr=plane(a.z,b.z,c.z,ar,brw,cr,inverse),zx=plane(a.z,b.z,c.z,ax,bx,cx,inverse),zy=plane(a.z,b.z,c.z,ay,by,cy,inverse);
 int64_t lr=plane(a.light,b.light,c.light,ar,brw,cr,inverse),lx=plane(a.light,b.light,c.light,ax,bx,cx,inverse),ly=plane(a.light,b.light,c.light,ay,by,cy,inverse);
 int64_t ur=0,ux=0,uy=0,vr=0,vx=0,vy=0;
 /* Flat-colored original mesh faces often revisit the same quantized
  * light value. Reuse the identical integer RGB result without changing
  * triangle topology, shading math or texture sampling. */
 int last_flat_light=-1;
 uint16_t flat_pixel=0;
 if(masked||tex){
  ur=plane(a.u,b.u,c.u,ar,brw,cr,inverse);ux=plane(a.u,b.u,c.u,ax,bx,cx,inverse);uy=plane(a.u,b.u,c.u,ay,by,cy,inverse);
  vr=plane(a.v,b.v,c.v,ar,brw,cr,inverse);vx=plane(a.v,b.v,c.v,ax,bx,cx,inverse);vy=plane(a.v,b.v,c.v,ay,by,cy,inverse);
 }
 for(int y=y0;y<=y1;y++,ar+=ay,brw+=by,cr+=cy,zr+=zy,lr+=ly,ur+=uy,vr+=vy){
  int wa=ar,wb=brw,wc=cr;int64_t zf=zr,lf=lr,uf=ur,vf=vr;
  for(int x=x0;x<=x1;x++,wa+=ax,wb+=bx,wc+=cx,zf+=zx,lf+=lx,uf+=ux,vf+=vx){
   if(wa<0||wb<0||wc<0)continue;
   int64_t zwide=zf/65536;
   if(zwide<INT_MIN||zwide>INT_MAX)continue;
   int z=(int)zwide,idx=y*S+x;if(z<depth[idx])continue;
   unsigned alpha=255,rgb[3];int light=clamp((int)(lf/65536),255);
   if(masked||tex){
    int u=(int)(uf/65536),v=(int)(vf/65536);uint32_t col;
    if(masked)col=mask[clamp((8192-v)*(MS-1)/8192,MS-1)*MS+clamp(u*(MS-1)/8192,MS-1)];
    else col=tint(texel(tex,u*(int)tex->width/8192,(8192-v)*(int)tex->height/8192),color,color,0);
    alpha=col>>24;if(alpha<8)continue;for(int k=0;k<3;k++)rgb[k]=(col>>(8*k)&255)*light/255;
   }else{
    /* Solid faces are opaque. Cache the exact RGB555 result and avoid
     * per-pixel RGB arrays, alpha tests and channel packing. */
    if(light!=last_flat_light){
     flat_pixel=(uint16_t)(0x8000|
      ((color[0]*light/255)>>3)|
      (((color[1]*light/255)>>3)<<5)|
      (((color[2]*light/255)>>3)<<10));
     last_flat_light=light;
    }
    out[idx]=flat_pixel;depth[idx]=z;continue;
   }
   if(alpha<255){uint16_t old=out[idx];for(int k=0;k<3;k++)rgb[k]=(rgb[k]*alpha+((old>>(5*k))&31)*255/31*(255-alpha))/255;}
   out[idx]=(uint16_t)(0x8000|(rgb[0]>>3)|((rgb[1]>>3)<<5)|((rgb[2]>>3)<<10));depth[idx]=z;
  }
 }
}
static int16_t signed16(const uint8_t *p);
static int mesh(const MdsCflArchive*a,unsigned sec,unsigned id,const float*anchor,float scale,int flip,const uint8_t*color,int masked,int texsec,unsigned texid,uint16_t*out)
{
 MdsCflItem it;MdsCflGeometry g;MdsCflTexture tex,*tp=NULL;
 if(!mds_cfl_item(a,sec,id,&it)||!mds_cfl_geometry(&it,&g))return 0;
 if(texsec>=0){MdsCflItem ti;if(mds_cfl_item(a,(unsigned)texsec,texid,&ti)&&mds_cfl_texture(&ti,&tex))tp=&tex;else return 0;}
 int32_t transform[12]={0};
 if(body_model){float mat[12];memcpy(mat,body_model+8,48);for(int k=0;k<12;k++)transform[k]=(int32_t)(mat[k]*65536.f);for(int k=0;k<3;k++)transform[k*4+3]=(int32_t)(mat[k*4+3]*(k==1?body_height:body_width)*256.f);}
 int32_t local_scale=(int32_t)(scale*65536.f),projection=(int32_t)(view_scale*65536.f);
 int64_t offset_y=(int64_t)(view_y*16777216.f);
 int32_t local_anchor[3]={0};for(int k=0;k<3;k++)if(anchor)local_anchor[k]=(int32_t)(anchor[k]*256.f);
 for(unsigned i=0;i<g.count;i++){
  if(!(i%32)&&cancelled())return 0;
  const uint8_t*raw=g.vertices+(size_t)i*g.stride;
  int32_t p[3],n[3];for(int k=0;k<3;k++)p[k]=signed16(raw+k*2);
  raw+=6;const uint8_t*normal=g.normals==g.count?raw:g.common_normal;
  for(int k=0;k<3;k++)n[k]=normal?signed16(normal+k*2):(k==2?256:0);
  if(g.normals==g.count)raw+=6;
  const uint8_t*uv=g.texcoords==g.count?raw:g.common_uv;
  if(flip){p[0]=-p[0];n[0]=-n[0];}
  for(int k=0;k<3;k++)p[k]=(int32_t)((int64_t)p[k]*local_scale/65536)+local_anchor[k];
  if(body_model){
   int32_t world[3],norm[3];
   for(int k=0;k<3;k++){
    world[k]=(int32_t)(((int64_t)transform[k*4]*p[0]+(int64_t)transform[k*4+1]*p[1]+(int64_t)transform[k*4+2]*p[2])/65536);
    world[k]+=transform[k*4+3];
    norm[k]=(int32_t)(((int64_t)transform[k*4]*n[0]+(int64_t)transform[k*4+1]*n[1]+(int64_t)transform[k*4+2]*n[2])/65536);
   }
   memcpy(p,world,sizeof p);memcpy(n,norm,sizeof n);
  }
  if(view_angle){
   mds_view_rotate(&p[0],&p[2],view_angle);
   mds_view_rotate(&n[0],&n[2],view_angle);
  }
  verts[i]=(Vertex){screen_coordinate((int64_t)64*16777216+(int64_t)p[0]*projection,16777216),screen_coordinate(offset_y-(int64_t)p[1]*projection,16777216),p[2]/2,uv?signed16(uv):0,uv?signed16(uv+2):0,225+(n[2]*20+n[1]*10)/256};
 }
 unsigned count=g.indices?g.index_count:g.count;
 for(unsigned i=0;i+2<count;i+=3){if(!(i%48)&&cancelled())return 0;unsigned ia=g.indices?g.indices[i]:i,ib=g.indices?g.indices[i+1]:i+1,ic=g.indices?g.indices[i+2]:i+2;triangle(verts[ia],verts[ib],verts[ic],color,masked,tp,out);}
 return 1;
}
static int render_head(const MdsCflArchive*a,const MdsAvatar*m,uint16_t*out)
{
 if(!a||!m||!out||!mds_valid(m))return 0;
 MdsCflItem face;if(!mds_cfl_item(a,2,m->value[2],&face)||face.size<36)return 0;
 float anchors[9];memcpy(anchors,face.data,36);for(unsigned i=0;i<9;i++)if(!isfinite(anchors[i])||fabsf(anchors[i])>200)return 0;
 const uint8_t*v=m->value,*skin=skins[v[1]],*hair=hairs[v[6]];float t;
 if(!mask_valid||mask_resource!=a->data||memcmp(mask_key,v,sizeof mask_key)){
 mask_valid=0;memset(mask,0,sizeof mask);
 uint8_t eye_base[3]={0,0,0};if(v[8]==9){eye_base[0]=255;eye_base[1]=130;}else if(v[8]==20){eye_base[1]=255;eye_base[2]=255;}
 for(int side=0;side<2;side++){
  float sign=side?1:-1;int origin=side?1:2;
  t=.4f*v[10]+1;float angle=(int)v[12]+er[v[8]];if(side)angle=-angle;
  decal(a,10,v[8],32+sign*v[13]*.88961464f,v[14]*1.0760943f+18.451524f,5.34375f*t,4.5f*t*(v[11]*.12f+.64f),angle,origin,eye_base,eyes[v[9]],1);
  t=.4f*v[17]+1;angle=(int)v[19]+br[v[15]];if(side)angle=-angle;
  decal(a,11,v[15],32+sign*v[20]*.88961464f,v[21]*1.0760943f+16.549806f,5.0625f*t,4.5f*t*(v[18]*.12f+.64f),angle,origin,hairs[v[16]],dark,0);
 }
 t=.4f*v[27]+1;decal(a,17,v[25],32,v[29]*1.0760943f+29.25885f,6.1875f*t,4.5f*t*(v[28]*.12f+.64f),0,0,lips[v[26]],lipinner[v[26]],2);
 if(v[39]){t=.4f*v[40]+1;decal(a,16,1,v[41]*1.0760943f+15.631847f,v[42]*1.0760943f+17.959861f,t,t,0,0,dark,dark,0);}
 if(v[34])for(int side=1;side<=2;side++){t=.4f*v[37]+1;decal(a,18,v[34],32,v[38]*1.0760943f+31.763553f,4.5f*t,9*t,0,side,hairs[v[36]],dark,0);}
 if(render_cancelled)return 0;
 memcpy(mask_key,v,sizeof mask_key);mask_resource=a->data;mask_valid=1;
 }
 if(!mesh(a,2,v[2],NULL,1,0,skin,0,-1,0,out))return 0;
 if(v[4])mesh(a,2,v[2],NULL,1,0,white,0,14,v[4],out);
 if(v[3])mesh(a,2,v[2],NULL,1,0,dark,0,13,v[3],out);
 mesh(a,6,v[2],NULL,1,0,white,1,-1,0,out);
 unsigned h=v[5]*2;mesh(a,5,h,anchors,1,v[7],hair,0,-1,0,out);mesh(a,3,h,anchors,1,v[7],skin,0,-1,0,out);
 mesh(a,1,h,anchors,1,v[7],shirts[v[45]],0,9,v[5],out);
 mesh(a,0,v[35],anchors+6,1,0,hairs[v[36]],0,-1,0,out);
 float nose[3]={anchors[3],anchors[4]+((float)v[24]-8)*-1.5f,anchors[5]};t=v[23]*.175f+.4f;
 mesh(a,8,v[22],nose,t,0,skin,0,-1,0,out);mesh(a,7,v[22],nose,t,0,dark,0,19,v[22],out);
 if(v[30]){nose[1]=anchors[4]+((float)v[33]-11)*-1.5f+5;nose[2]=anchors[5]+2;mesh(a,4,0,nose,v[32]*.15f+.4f,0,glasses[v[31]],0,15,v[30],out);}
 return 1;
}

static int16_t signed16(const uint8_t *p){unsigned v=le16(p);return (int16_t)(v>=32768?(int)v-65536:(int)v);}
static uint32_t word32(const uint8_t *p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int32_t signed32(const uint8_t*p){uint32_t v=word32(p);return v<=INT32_MAX?(int32_t)v:-1-(int32_t)(UINT32_MAX-v);}
int mds_mii_render_view(const MdsCflArchive*a,const MdsAvatar*m,const void*bytes,size_t size,uint16_t*out,int full,unsigned angle)
{
 if(!a||!m||!out||!mds_valid(m))return 0;
 body_model=NULL;render_cancelled=0;view_angle=angle%MDS_VIEW_STEPS;
 unsigned count=0,stride=12,normal_offset=6;
 if(bytes){
  const uint8_t*p=bytes;
  if(size<56)return 0;
  if(!memcmp(p,"BOD3",4)){stride=18;normal_offset=12;}else if(memcmp(p,"BOD2",4))return 0;
  count=word32(p+4);if(count>12000||count%3||size!=56+(size_t)count*stride)return 0;
  float mat[12];memcpy(mat,p+8,48);for(unsigned k=0;k<12;k++)if(!isfinite(mat[k])||fabsf(mat[k])>4096)return 0;
  if(stride==18)for(unsigned i=0;i<count;i++)for(unsigned k=0;k<3;k++){int32_t v=signed32(p+56+i*18+k*4);if(v< -524288||v>524288)return 0;}
  body_model=p;
 }
 body_height=.85f+(m->value[43]/127.f)*.3f;
 body_width=.7f+(m->value[44]/127.f)*.6f;
 view_scale=full?.60f:body_model?1.15f:1.35f;
 float head_y=0;if(body_model)memcpy(&head_y,body_model+8+7*4,4);
 view_y=full?122.f:body_model?90.f+head_y*body_height*view_scale:111.f;
 memset(out,0,S*S*2);for(unsigned i=0;i<S*S;i++)depth[i]=INT_MIN;
 if(body_model){
  const uint8_t*source=body_model+56;
  int32_t width=(int32_t)(body_width*65536.f),height=(int32_t)(body_height*65536.f),projection=(int32_t)(view_scale*65536.f),offset=(int32_t)(view_y*65536.f);
  for(unsigned i=0;i<count;i+=3){
   if(!(i%48)&&cancelled()){body_model=NULL;return -1;}
   Vertex tri[3];const uint8_t*color=shirts[m->value[45]];
   for(unsigned j=0;j<3;j++){
    const uint8_t*p=source+(i+j)*stride;
    int32_t px=stride==18?signed32(p):signed16(p);
    int32_t pz=stride==18?signed32(p+8):signed16(p+4);
    if(view_angle)mds_view_rotate(&px,&pz,view_angle);
    int64_t x=(int64_t)px*width,y=(int64_t)(stride==18?signed32(p+4):signed16(p+2))*height,z=(int64_t)pz*width;
    unsigned material=p[normal_offset+3],bone=p[normal_offset+4];
    if(material==1)color=mds_pants_color(m);
    else if(bone==6||bone==9)color=skins[m->value[1]];
    tri[j]=(Vertex){screen_coordinate((int64_t)64*549755813888+x*projection,549755813888LL),screen_coordinate((int64_t)offset*8388608-y*projection,549755813888LL),(int)(z/65536),0,0,clamp(225+(int)(int8_t)p[normal_offset+2]*20/127+(int)(int8_t)p[normal_offset+1]*10/127,255)};
   }
   triangle(tri[0],tri[1],tri[2],color,0,NULL,out);
  }
 }
 int ready=render_head(a,m,out);body_model=NULL;return render_cancelled?-1:ready;
}
int mds_mii_render(const MdsCflArchive*a,const MdsAvatar*m,const void*bytes,size_t size,uint16_t*out,int full)
{
 return mds_mii_render_view(a,m,bytes,size,out,full,0);
}
int mds_head_render_view(const MdsCflArchive*a,const MdsAvatar*m,uint16_t*out,unsigned angle)
{
 return mds_mii_render_view(a,m,NULL,0,out,0,angle);
}
int mds_head_render(const MdsCflArchive*a,const MdsAvatar*m,uint16_t*out)
{
 return mds_head_render_view(a,m,out,0);
}
