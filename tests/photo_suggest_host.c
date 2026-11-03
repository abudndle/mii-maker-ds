#include "photo_suggest.h"
#include <assert.h>
#include <string.h>
static uint16_t picture[256*192];
static uint16_t gray(unsigned l){return (uint16_t)(l|(l<<5)|(l<<10));}
static void image(void)
{
    for(unsigned y=0;y<192;y++)for(unsigned x=0;x<256;x++)
        picture[y*256u+x]=gray(20u);
    /* The pre-existing cue only checks two fixed dark patches. */
    for(unsigned y=64;y<84;y++)for(unsigned x=72;x<108;x++)
        picture[y*256u+x]=gray(8u);
    for(unsigned y=64;y<84;y++)for(unsigned x=148;x<184;x++)
        picture[y*256u+x]=gray(8u);
}
int main(void)
{
    MdsAvatar source,choices[3],prior[3];mds_new(&source);
    source.value[0]=1;source.value[46]=1;source.value[51]=1;
    source.value[47]=0;source.value[48]=0;source.value[61]=2;
    image();
    memset(choices,0xa5,sizeof choices);memcpy(prior,choices,sizeof prior);
    assert(!mds_photo_suggest(0,256,192,&source,choices));
    assert(!mds_photo_suggest(picture,255,192,&source,choices));
    assert(!mds_photo_suggest(picture,256,191,&source,choices));
    assert(!mds_photo_suggest(picture,256,192,0,choices));
    assert(!mds_photo_suggest(picture,256,192,&source,0));
    assert(!memcmp(choices,prior,sizeof choices));
    assert(mds_photo_suggest(picture,256,192,&source,choices));
    for(unsigned i=0;i<3u;i++){
        assert(mds_valid(&choices[i]));
        assert(choices[i].value[2]==i);
        assert(choices[i].value[5]==i*7u);
        assert(!memcmp(choices[i].name,source.name,MDS_NAME));
        assert(!memcmp(choices[i].creator,source.creator,MDS_NAME));
        assert(choices[i].value[0]==source.value[0]);
        for(unsigned j=45;j<62;j++)assert(choices[i].value[j]==source.value[j]);
    }
    assert(choices[0].value[2]!=choices[1].value[2]);
    assert(choices[1].value[5]!=choices[2].value[5]);
    image();for(unsigned y=64;y<84;y++)for(unsigned x=148;x<184;x++)
        picture[y*256u+x]=gray(23u);
    memcpy(prior,choices,sizeof prior);
    assert(!mds_photo_suggest(picture,256,192,&source,choices));
    assert(!memcmp(choices,prior,sizeof choices));
    /* Position and spacing of synthetic dark regions affect the suggested
     * eye spacing (Mii field 13) and vertical placement (field 14). */
    image();
    assert(mds_photo_suggest(picture,256,192,&source,choices));
    unsigned narrow_spacing=choices[0].value[13];
    unsigned upper_eye_height=choices[0].value[14];
    image();
    for(unsigned y=64;y<84;y++)for(unsigned x=72;x<108;x++)
        picture[y*256u+x]=gray(20);
    for(unsigned y=64;y<84;y++)for(unsigned x=148;x<184;x++)
        picture[y*256u+x]=gray(20);
    for(unsigned y=72;y<96;y++)for(unsigned x=64;x<100;x++)
        picture[y*256u+x]=gray(8);
    for(unsigned y=72;y<96;y++)for(unsigned x=172;x<208;x++)
        picture[y*256u+x]=gray(8);
    assert(mds_photo_suggest(picture,256,192,&source,choices));
    assert(choices[0].value[13]>narrow_spacing);
    assert(choices[0].value[14]<upper_eye_height);
    for(unsigned i=0;i<3u;i++){
        assert(choices[i].value[13]<=12);
        assert(choices[i].value[14]<=18);
        assert(choices[i].value[0]==source.value[0]);
        assert(choices[i].value[51]==source.value[51]);
    }
    /* A stripe-like upper shadow must not be mistaken for a pair. */
    image();
    for(unsigned y=64;y<86;y++)for(unsigned x=48;x<208;x++)
        picture[y*256u+x]=gray(8);
    memcpy(prior,choices,sizeof prior);
    assert(!mds_photo_suggest(picture,256,192,&source,choices));
    assert(!memcmp(prior,choices,sizeof prior));
    image();source.value[5]=255;
    assert(!mds_photo_suggest(picture,256,192,&source,choices));
    return 0;
}
