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
    assert(mds_gallery_balloon_clan_favorite_visible(&state,0));
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
    assert(!mds_gallery_balloon_clan_favorite_visible(&state,210));
    assert(!mds_gallery_balloon_clan_active(&state,212));
    assert(!mds_gallery_balloon_clan_style(&state,212,&s));
    assert(s.balloon_alpha==0u&&s.favorite_alpha==0u);
    assert(!mds_gallery_balloon_clan_actions_visible(&state,212));
    /* Original UnDecide affects Favorite only, never Copy/Edit parent. */
    mds_gallery_balloon_clan_play(&state,MDS_BALLOON_UNDECIDE,220);
    assert(mds_gallery_balloon_clan_style(&state,230,&s));
    assert(s.balloon_alpha==255u&&s.favorite_alpha==0u);
    assert(mds_gallery_balloon_clan_actions_visible(&state,230));
    assert(!mds_gallery_balloon_clan_favorite_visible(&state,230));
    assert(!mds_gallery_balloon_clan_style(&state,232,&s));
    assert(s.balloon_alpha==255u&&s.favorite_alpha==0u);
    mds_gallery_balloon_clan_play(&state,MDS_BALLOON_DECIDE,240);
    assert(mds_gallery_balloon_clan_style(&state,245,&s));
    assert(s.balloon_alpha==255u&&s.favorite_alpha==255u);
    assert(mds_gallery_balloon_clan_favorite_visible(&state,245));
    assert(!mds_gallery_balloon_clan_active(&state,252));
    mds_gallery_balloon_clan_play(&state,(MdsGalleryBalloonClip)255,253);
    assert(state.clip==MDS_BALLOON_DECIDE&&state.started==240);
    mds_gallery_balloon_clan_play(&state,(MdsGalleryBalloonClip)-1,254);
    assert(state.clip==MDS_BALLOON_DECIDE&&state.started==240);
    /* The first selected Mii plays Select immediately. Subsequent changes
     * play original Unselect, then Select without delaying the new Mii. */
    mds_gallery_balloon_clan_reset(&state);
    mds_gallery_balloon_clan_selection_changed(&state,100);
    assert(state.clip==MDS_BALLOON_SELECT&&state.started==100&&!state.pending_select);
    mds_gallery_balloon_clan_selection_changed(&state,103);
    assert(state.clip==MDS_BALLOON_UNSELECT&&state.started==103&&state.pending_select);
    mds_gallery_balloon_clan_selection_changed(&state,107);
    assert(state.started==103&&state.pending_select); /* rapid tap cannot starve fade */
    assert(!mds_gallery_balloon_clan_tick(&state,114));
    assert(!mds_gallery_balloon_clan_actions_visible(&state,114));
    assert(mds_gallery_balloon_clan_tick(&state,115));
    assert(state.clip==MDS_BALLOON_SELECT&&state.started==115&&!state.pending_select);
    assert(!mds_gallery_balloon_clan_actions_visible(&state,115));
    assert(mds_gallery_balloon_clan_actions_visible(&state,117));
    assert(!mds_gallery_balloon_clan_tick(&state,117));
    /* A skipped frame resumes the source clip at its real elapsed frame. */
    mds_gallery_balloon_clan_selection_changed(&state,120);
    assert(mds_gallery_balloon_clan_tick(&state,140));
    assert(state.started==132&&state.clip==MDS_BALLOON_SELECT);
    assert(mds_gallery_balloon_clan_actions_visible(&state,140));
    /* Wraparound must not defer the next selected balloon for 2^32 ticks. */
    mds_gallery_balloon_clan_reset(&state);
    mds_gallery_balloon_clan_selection_changed(&state,UINT32_MAX-5u);
    mds_gallery_balloon_clan_selection_changed(&state,UINT32_MAX-3u);
    assert(!mds_gallery_balloon_clan_tick(&state,7u));
    assert(mds_gallery_balloon_clan_tick(&state,8u));
    assert(state.started==8u&&state.clip==MDS_BALLOON_SELECT);
    /* A Favorite press uses the original Decide constant-opacity clip.
     * A successful persisted toggle plays UnDecide, which fades Favorite
     * alone, then restores it with Decide (Copy/Edit never disappear). */
    mds_gallery_balloon_clan_reset(&state);
    mds_gallery_balloon_clan_favorite_pressed(&state,300u);
    assert(state.clip==MDS_BALLOON_DECIDE&&!state.pending_decide);
    assert(mds_gallery_balloon_clan_favorite_visible(&state,300u));
    mds_gallery_balloon_clan_favorite_committed(&state,305u);
    assert(state.clip==MDS_BALLOON_UNDECIDE&&state.pending_decide);
    assert(mds_gallery_balloon_clan_actions_visible(&state,315u));
    assert(!mds_gallery_balloon_clan_favorite_visible(&state,315u));
    assert(!mds_gallery_balloon_clan_tick(&state,316u));
    assert(mds_gallery_balloon_clan_tick(&state,317u));
    assert(state.clip==MDS_BALLOON_DECIDE&&state.started==317u);
    assert(!state.pending_decide&&mds_gallery_balloon_clan_favorite_visible(&state,317u));
    assert(mds_gallery_balloon_clan_actions_visible(&state,317u));
    /* Presses during a queued fade must not interrupt its completion. */
    mds_gallery_balloon_clan_favorite_committed(&state,320u);
    mds_gallery_balloon_clan_favorite_pressed(&state,322u);
    assert(state.clip==MDS_BALLOON_UNDECIDE&&state.started==320u);
    assert(mds_gallery_balloon_clan_tick(&state,332u));
    /* A second persisted Favorite update cannot restart the pending fade
     * and keep its icon invisible indefinitely. */
    mds_gallery_balloon_clan_favorite_committed(&state,334u);
    mds_gallery_balloon_clan_favorite_committed(&state,338u);
    assert(state.clip==MDS_BALLOON_UNDECIDE&&state.started==334u);
    assert(state.pending_decide);
    assert(!mds_gallery_balloon_clan_tick(&state,345u));
    assert(mds_gallery_balloon_clan_tick(&state,346u));
    assert(state.clip==MDS_BALLOON_DECIDE&&state.started==346u);
    assert(mds_gallery_balloon_clan_favorite_visible(&state,346u));
    /* A completed persistence callback must not erase the selected Mii's
     * pending Unselect -> Select transition. */
    mds_gallery_balloon_clan_reset(&state);
    mds_gallery_balloon_clan_selection_changed(&state,350u);
    mds_gallery_balloon_clan_selection_changed(&state,352u);
    mds_gallery_balloon_clan_favorite_committed(&state,353u);
    assert(state.clip==MDS_BALLOON_UNSELECT&&state.started==352u);
    assert(state.pending_select&&!state.pending_decide);
    assert(mds_gallery_balloon_clan_tick(&state,364u));
    assert(state.clip==MDS_BALLOON_SELECT&&state.started==364u);
    mds_gallery_balloon_clan_reset(&state);
    /* Selection changes supersede Favorite feedback and still reveal a
     * new selected Mii after Unselect, even if the old icon was fading. */
    mds_gallery_balloon_clan_favorite_committed(&state,340u);
    mds_gallery_balloon_clan_selection_changed(&state,342u);
    assert(state.clip==MDS_BALLOON_UNSELECT&&state.pending_select);
    assert(!state.pending_decide);
    assert(mds_gallery_balloon_clan_tick(&state,354u));
    assert(state.clip==MDS_BALLOON_SELECT);
    /* Favorite fade/reveal must remain correct through VBlank rollover. */
    mds_gallery_balloon_clan_favorite_committed(&state,UINT32_MAX-3u);
    assert(!mds_gallery_balloon_clan_tick(&state,7u));
    assert(mds_gallery_balloon_clan_tick(&state,8u));
    assert(state.clip==MDS_BALLOON_DECIDE&&state.started==8u);
    /* Direct source clip playback cancels an unfinished queued transition. */
    mds_gallery_balloon_clan_selection_changed(&state,10u);
    assert(state.pending_select);
    mds_gallery_balloon_clan_play(&state,MDS_BALLOON_DECIDE,11u);
    assert(!state.pending_select&&!mds_gallery_balloon_clan_tick(&state,30u));
    assert(!mds_gallery_balloon_clan_tick(NULL,30u));
    mds_gallery_balloon_clan_reset(&state);
    assert(!mds_gallery_balloon_clan_active(&state,2));
    assert(mds_gallery_balloon_clan_actions_visible(&state,2));
    assert(mds_gallery_balloon_clan_favorite_visible(&state,2));
    puts("PASS: source Select/Unselect/Decide/UnDecide CLAN numeric playback");
    return 0;
}
