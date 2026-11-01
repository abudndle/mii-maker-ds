/* User-supplied 3DS EDITSelectBase CLAN numeric metadata only.
 * Original BCLAN files must stay private; no original animation payloads.
 * See docs/ORIGINAL_3DS_RESOURCE_RECOVERY.md for source SHA-256 values.
 * Track/channel keys and 0x10000 Q16 values come from verified BCLAN data. */
#ifndef MDS_GALLERY_NAV_CLAN_GENERATED_H
#define MDS_GALLERY_NAV_CLAN_GENERATED_H
#include "clan_curve.h"
#define MDS_SOURCE_EDITSELECTBASE_SCROLLL_FRAMES 11u
#define MDS_SOURCE_EDITSELECTBASE_SCROLLR_FRAMES 11u
#define MDS_SOURCE_EDITSELECTBASE_INVALID_FRAMES 11u
#define MDS_SOURCE_SELECTMII_UNDECIDE_FRAMES 6u
#define MDS_SOURCE_SELECTMII_DECIDE_FRAMES 6u
/* P_ArrowL / P_ArrowR, CLPA 0x0000 horizontal translations */
static const MdsClanKey gallery_nav_left_l_x[]={
    {0,0,-196608},{65536,-196608,0}
};
static const MdsClanKey gallery_nav_left_r_x[]={
    {0,0,196608},{65536,196608,0}
};
static const MdsClanKey gallery_nav_right_l_x[]={
    {0,-196608,0},{65536,0,0}
};
static const MdsClanKey gallery_nav_right_r_x[]={
    {0,196608,0},{65536,0,0}
};
/* P_ArrowLSdw_00, CLVC 0x1000: source pane alpha */
static const MdsClanKey gallery_nav_left_shadow_alpha[]={
    {0,13107200,0},{65536,0,0}
};
static const MdsClanKey gallery_nav_right_shadow_alpha[]={
    {0,0,0},{65536,13107200,0}
};
/* P_Mii_00 SelectMii_UnDecide, CLMC 0x400/0x500/0x600.
 * The source Decide state fixes RGB at (251,199,186); UnDecide goes
 * towards (216,233,214) over source frame 0..1. */
static const MdsClanKey gallery_confirm_red[]={
    {0,16449536,0},{65536,14155776,0}
};
static const MdsClanKey gallery_confirm_green[]={
    {0,13041664,0},{65536,15269888,0}
};
static const MdsClanKey gallery_confirm_blue[]={
    {0,12189696,0},{65536,14024704,0}
};
/* EDITSelectBase_Invalid P_ArrowL/P_ArrowR tracks are constant zero.
 * There is NO verified nontrivial arrow-bounce curve in that clip. */
static const MdsClanKey gallery_nav_invalid_arrow_x[]={{0,0,0}};
#endif
