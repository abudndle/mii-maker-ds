#include <assert.h>
#include <stdio.h>
#include "gallery_balloon_clan.h"
int main(void)
{
    MdsGalleryBalloonClan state={0};
    MdsGalleryBalloonStyle s;
    assert(!mds_gallery_balloon_clan_style(&state,0,&s));
    assert(s.favorite_scale_q16==65536u&&s.balloon_alpha==255u);
    assert(mds_gallery_balloon_clan_actions_visible(&state,0));
    mds_gallery_balloon_clan_select(&state,100);
    assert(!mds_gallery_balloon_clan_actions_visible(&state,100));
    assert(mds_gallery_balloon_clan_actions_visible(&state,102));
    assert(mds_gallery_balloon_clan_style(&state,100,&s));
    assert(s.balloon_alpha==0u&&s.favorite_alpha==255u);
    assert(mds_gallery_balloon_clan_style(&state,102,&s));
    assert(s.favorite_scale_q16>65536u);
    assert(mds_gallery_balloon_clan_style(&state,110,&s));
    assert(s.balloon_alpha==255u);
    assert(mds_gallery_balloon_clan_style(&state,112,&s));
    assert(s.favorite_alpha==255u);
    assert(mds_gallery_balloon_clan_style(&state,120,&s));
    assert(s.favorite_scale_q16==65536u);
    assert(!mds_gallery_balloon_clan_style(&state,122,&s));
    assert(s.favorite_alpha==255u&&s.balloon_alpha==255u);
    assert(!mds_gallery_balloon_clan_style(&state,122,NULL));
    mds_gallery_balloon_clan_select(&state,0xfffffffdu);
    assert(mds_gallery_balloon_clan_style(&state,1u,&s));
    /* Original Unselect: I_Favorite and N_Balloon CLVC 255->0 over 5
     * source frames, within the 6-frame non-looping clip. */
    mds_gallery_balloon_clan_play(&state,MDS_BALLOON_UNSELECT,200);
    assert(mds_gallery_balloon_clan_style(&state,200,&s));
    assert(s.balloon_alpha==255u&&s.favorite_alpha==255u);
    assert(mds_gallery_balloon_clan_style(&state,205,&s));
    assert(s.balloon_alpha>0u&&s.balloon_alpha<255u);
    assert(mds_gallery_balloon_clan_style(&state,210,&s));
    assert(s.balloon_alpha==0u&&s.favorite_alpha==0u);
    assert(!mds_gallery_balloon_clan_actions_visible(&state,210));
    assert(!mds_gallery_balloon_clan_active(&state,212));
    assert(!mds_gallery_balloon_clan_style(&state,212,&s));
    assert(s.balloon_alpha==0u&&s.favorite_alpha==0u);
    assert(!mds_gallery_balloon_clan_actions_visible(&state,212));
    /* Original UnDecide affects Favorite only, never Copy/Edit parent. */
    mds_gallery_balloon_clan_play(&state,MDS_BALLOON_UNDECIDE,220);
    assert(mds_gallery_balloon_clan_style(&state,230,&s));
    assert(s.balloon_alpha==255u&&s.favorite_alpha==0u);
    assert(mds_gallery_balloon_clan_actions_visible(&state,230));
    assert(!mds_gallery_balloon_clan_style(&state,232,&s));
    assert(s.balloon_alpha==255u&&s.favorite_alpha==0u);
    mds_gallery_balloon_clan_play(&state,MDS_BALLOON_DECIDE,240);
    assert(mds_gallery_balloon_clan_style(&state,245,&s));
    assert(s.balloon_alpha==255u&&s.favorite_alpha==255u);
    assert(!mds_gallery_balloon_clan_active(&state,252));
    mds_gallery_balloon_clan_play(&state,(MdsGalleryBalloonClip)255,253);
    assert(state.clip==MDS_BALLOON_DECIDE&&state.started==240);
    mds_gallery_balloon_clan_play(&state,(MdsGalleryBalloonClip)-1,254);
    assert(state.clip==MDS_BALLOON_DECIDE&&state.started==240);
    mds_gallery_balloon_clan_reset(&state);
    assert(!mds_gallery_balloon_clan_active(&state,2));
    assert(mds_gallery_balloon_clan_actions_visible(&state,2));
    puts("PASS: source Select/Unselect/Decide/UnDecide CLAN numeric playback");
    return 0;
}
