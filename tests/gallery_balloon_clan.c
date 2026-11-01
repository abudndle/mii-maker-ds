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
    assert(s.balloon_alpha==0u&&s.favorite_alpha==0u);
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
    mds_gallery_balloon_clan_reset(&state);
    assert(!mds_gallery_balloon_clan_active(&state,2));
    assert(mds_gallery_balloon_clan_actions_visible(&state,2));
    puts("PASS: source balloon alpha/scale/touch numeric timeline and tick wrap");
    return 0;
}
