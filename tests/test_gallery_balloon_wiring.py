#!/usr/bin/env python3
"""Ensure source balloon animation only affects artwork, never touch bounds."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
ui=(root/"source/ui.c").read_text()
menu=(root/"source/menu.c").read_text()
art=(root/"source/original_gallery_art.c").read_text()
source=(root/"source/gallery_balloon_clan.c").read_text()
assert 'mds_gallery_balloon_clan_select(&gallery_balloon_state,now)' in ui
assert 'mds_gallery_balloon_clan_active(&gallery_balloon_state,now)' in ui
assert 'mds_gallery_balloon_clan_reset(&gallery_balloon_state)' in ui
assert 'mds_gallery_balloon_clan_style(&gallery_balloon_state,now,&balloon)' in ui
assert 'balloon.favorite_scale_q16' in ui
assert 'balloon.balloon_alpha*balloon.favorite_alpha' in ui
assert 'mds_original_gallery_action_icon_alpha(bottom,256,192,' in ui
assert 'original_sprite_blit_alpha(' in art
assert 'if(pixel&0x8000u)' in art
assert 'if(x<84)return MDS_GALLERY_ACTION_FAVORITE;' in menu
assert 'if(x>=90&&x<166)return MDS_GALLERY_ACTION_COPY;' in menu
assert 'if(x>=172)return MDS_GALLERY_ACTION_EDIT;' in menu
assert 'static const MdsClanKey balloon_alpha[]' in source
assert 'static const MdsClanKey favorite_scale[]' in source
assert not list((root/"source").glob("*.bclan"))
print("PASS: source balloon CLAN playback, alpha blending and stable touch bounds")
