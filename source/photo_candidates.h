#ifndef MDS_PHOTO_CANDIDATES_H
#define MDS_PHOTO_CANDIDATES_H
#include "editor.h"

/* An editor-only staging area for three externally computed photo candidates.
 * This is not a face detector or candidate generator.  It never saves.
 * A future authentic recognition backend must provide all three valid avatars. */
#define MDS_PHOTO_CANDIDATE_COUNT 3u
typedef struct {
    MdsAvatar choices[MDS_PHOTO_CANDIDATE_COUNT];
    MdsAvatar original;
    MdsEditor *editor;
    unsigned selected;
    int active;
} MdsPhotoCandidates;

void mds_photo_candidates_reset(MdsPhotoCandidates *state);
int mds_photo_candidates_begin(MdsPhotoCandidates *state,MdsEditor *editor,
                               const MdsAvatar choices[MDS_PHOTO_CANDIDATE_COUNT]);
int mds_photo_candidates_step(MdsPhotoCandidates *state,int direction);
int mds_photo_candidates_cancel(MdsPhotoCandidates *state);
int mds_photo_candidates_accept(MdsPhotoCandidates *state);
#endif
