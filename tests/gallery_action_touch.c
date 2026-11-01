#include <assert.h>
#include <stdio.h>
#include "menu.h"

/* Source-derived room tabs, ten fixed boxes and arrows must remain
 * independent of the accessible action strip below the gallery grid. */
int main(void)
{
    assert(mds_gallery_action_touch(8,168)==MDS_GALLERY_ACTION_FAVORITE);
    assert(mds_gallery_action_touch(83,190)==MDS_GALLERY_ACTION_FAVORITE);
    assert(mds_gallery_action_touch(90,168)==MDS_GALLERY_ACTION_COPY);
    assert(mds_gallery_action_touch(165,190)==MDS_GALLERY_ACTION_COPY);
    assert(mds_gallery_action_touch(172,168)==MDS_GALLERY_ACTION_EDIT);
    assert(mds_gallery_action_touch(247,190)==MDS_GALLERY_ACTION_EDIT);
    const int inert[][2]={{0,168},{7,168},{84,168},{89,190},
                           {166,168},{171,190},{248,168},
                           {128,167},{128,191},{-1,175},{256,175}};
    for(unsigned i=0;i<sizeof inert/sizeof inert[0];i++)
        assert(mds_gallery_action_touch(inert[i][0],inert[i][1])==
               MDS_GALLERY_ACTION_NONE);
    for(int y=0;y<192;y++)for(int x=0;x<256;x++){
        MdsGalleryTouchAction action=mds_gallery_action_touch(x,y);
        if(action==MDS_GALLERY_ACTION_NONE)continue;
        for(unsigned page=0;page<10;page++){
            assert(mds_gallery_touch(x,y,page)==-1);
            assert(mds_gallery_room_arrow(x,y,page)==0);
        }
        assert(mds_gallery_room_touch(x,y)==-1);
    }
    puts("PASS: Favorite/Copy/Edit touch actions never overlap gallery panes");
    return 0;
}
