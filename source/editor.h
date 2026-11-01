#ifndef MDS_EDITOR_H
#define MDS_EDITOR_H
#include "save.h"
typedef enum { MDS_EDIT_NONE, MDS_EDIT_PREV, MDS_EDIT_NEXT, MDS_EDIT_NEW, MDS_EDIT_DELETE, MDS_EDIT_RELOAD, MDS_EDIT_COPY_RECEIVED } MdsEditAction;
typedef struct {
    MdsGallery *gallery;
    MdsAvatar draft,baseline;
    unsigned slot;
    int field;
    MdsEditAction pending;
    const char *status;
} MdsEditor;
typedef int (*MdsPersist)(MdsGallery *,void *);
void mds_editor_begin(MdsEditor *,MdsGallery *);
int mds_editor_locked(const MdsAvatar *);
int mds_editor_dirty(const MdsEditor *);
int mds_editor_request(MdsEditor *,MdsEditAction);
int mds_editor_confirm(MdsEditor *,int,MdsPersist,void *);
int mds_editor_import(MdsEditor *,const MdsAvatar *,MdsPersist,void *);
int mds_editor_copy(MdsEditor *,MdsPersist,void *);
/* Toggle a saved ordinary Mii's Favorite with atomic persistence/rollback. */
int mds_editor_toggle_favorite(MdsEditor *,MdsPersist,void *);
/* Move a gallery Mii into an empty slot or swap two occupied slots. */
int mds_editor_move(MdsEditor *,unsigned destination,MdsPersist,void *);
/* Begin a new Mii in a specific empty gallery slot. */
int mds_editor_create(MdsEditor *,unsigned);
int mds_editor_save(MdsEditor *,MdsPersist,void *);
#endif
