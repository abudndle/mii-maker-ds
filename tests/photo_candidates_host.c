#include "photo_candidates.h"
#include <assert.h>
#include <string.h>
static MdsGallery gallery;
static MdsEditor editor;
static MdsPhotoCandidates state;
static MdsAvatar options[3];
static void setup(void)
{
    memset(&gallery,0,sizeof gallery);
    memset(&editor,0,sizeof editor);
    mds_photo_candidates_reset(&state);
    editor.gallery=&gallery;
    mds_new(&editor.draft);
    editor.draft.value[51]=1; /* first Personal Mii */
    editor.draft.value[46]=1;
    editor.draft.value[47]=1;
    editor.draft.value[48]=1;
    editor.draft.value[0]=1; /* preserve manually selected gender */
    for(unsigned i=0;i<3;i++){
        mds_new(&options[i]);
        options[i].value[2]=(unsigned char)(i+2); /* face shape */
        options[i].value[5]=(unsigned char)(i+12); /* hair */
        options[i].value[0]=0; /* must never change existing gender */
        options[i].value[51]=0;
        options[i].value[46]=0;
        options[i].value[47]=0;
        options[i].value[48]=0;
    }
}
int main(void)
{
    setup();
    MdsAvatar prior=editor.draft;
    assert(mds_photo_candidates_begin(&state,&editor,options));
    assert(state.active && state.selected==0);
    assert(editor.draft.value[2]==2 && editor.draft.value[5]==12);
    assert(editor.draft.value[0]==1 && editor.draft.value[51]==1);
    assert(editor.draft.value[46]==1 && editor.draft.value[47]==1);
    assert(editor.draft.value[48]==1);
    assert(mds_photo_candidates_step(&state,-1) && state.selected==2);
    assert(editor.draft.value[2]==4);
    assert(mds_photo_candidates_step(&state,1) && state.selected==0);
    assert(mds_photo_candidates_step(&state,1) && state.selected==1);
    assert(editor.draft.value[2]==3);
    assert(mds_photo_candidates_cancel(&state));
    assert(!memcmp(&editor.draft,&prior,sizeof prior));
    assert(!state.active && !mds_photo_candidates_cancel(&state));
    assert(mds_photo_candidates_begin(&state,&editor,options));
    assert(mds_photo_candidates_step(&state,1));
    assert(mds_photo_candidates_accept(&state));
    assert(!state.active && !mds_photo_candidates_accept(&state));
    assert(editor.draft.value[2]==3 && editor.draft.value[51]==1);
    assert(editor.draft.value[0]==1);
    assert(!memcmp(&editor.baseline,&(MdsAvatar){0},sizeof editor.baseline));

    /* Reject pending confirmation, received/locked Miis and bad choices. */
    setup();editor.pending=MDS_EDIT_DELETE;
    assert(!mds_photo_candidates_begin(&state,&editor,options));
    editor.pending=MDS_EDIT_NONE;
    gallery.used[0]=1;gallery.miis[0].value[61]=1;
    assert(!mds_photo_candidates_begin(&state,&editor,options));
    gallery.used[0]=0;
    options[2].value[5]=255;
    assert(!mds_photo_candidates_begin(&state,&editor,options));
    assert(!state.active);
    assert(mds_photo_candidates_step(&state,1)==0);
    assert(mds_photo_candidates_begin(NULL,&editor,options)==0);
    return 0;
}
