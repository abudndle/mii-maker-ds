#include "photo_candidates.h"
#include <string.h>

/* Only visual appearance fields may be inferred from a photograph.
 * Gender, name, creator, birthday, identity, ownership, sharing,
 * special/received flags, and favorite status always remain unchanged. */
enum { FIRST_APPEARANCE_FIELD=1, LAST_APPEARANCE_FIELD=44 };

void mds_photo_candidates_reset(MdsPhotoCandidates *s)
{
    if(s)memset(s,0,sizeof *s);
}
static void preview(MdsPhotoCandidates *s)
{
    MdsAvatar *draft=&s->editor->draft;
    *draft=s->original;
    for(unsigned i=FIRST_APPEARANCE_FIELD;i<=LAST_APPEARANCE_FIELD;i++)
        draft->value[i]=s->choices[s->selected].value[i];
}
int mds_photo_candidates_begin(MdsPhotoCandidates *s,MdsEditor *e,
                               const MdsAvatar choices[MDS_PHOTO_CANDIDATE_COUNT])
{
    if(!s||!e||!choices||s->active||!e->gallery||
       e->slot>=MDS_SLOTS||e->pending||
       (e->gallery->used[e->slot]&&
        mds_editor_locked(&e->gallery->miis[e->slot])))return 0;
    for(unsigned i=0;i<MDS_PHOTO_CANDIDATE_COUNT;i++)
        if(!mds_valid(&choices[i]))return 0;
    if(!mds_valid(&e->draft))return 0;
    /* Copy choices before touching editor memory: caller may use the
     * current draft as an input candidate. */
    for(unsigned i=0;i<MDS_PHOTO_CANDIDATE_COUNT;i++)s->choices[i]=choices[i];
    s->original=e->draft;
    s->editor=e;
    s->selected=0;
    s->active=1;
    preview(s);
    e->status="Photo candidate 1/3. A choose / B cancel";
    return 1;
}
int mds_photo_candidates_step(MdsPhotoCandidates *s,int direction)
{
    if(!s||!s->active||!s->editor||!direction)return 0;
    unsigned next=(s->selected+(direction>0?1u:2u))%MDS_PHOTO_CANDIDATE_COUNT;
    s->selected=next;
    preview(s);
    s->editor->status=next==0?"Photo candidate 1/3":
                      next==1?"Photo candidate 2/3":"Photo candidate 3/3";
    return 1;
}
int mds_photo_candidates_cancel(MdsPhotoCandidates *s)
{
    if(!s||!s->active||!s->editor)return 0;
    s->editor->draft=s->original;
    s->editor->status="Photo selection cancelled. Draft restored.";
    mds_photo_candidates_reset(s);
    return 1;
}
int mds_photo_candidates_accept(MdsPhotoCandidates *s)
{
    if(!s||!s->active||!s->editor)return 0;
    /* The preview is already in the draft. Never invoke cartridge save:
     * START in the ordinary editor remains the only persistence path. */
    s->editor->status="Photo candidate chosen. START to save.";
    mds_photo_candidates_reset(s);
    return 1;
}
