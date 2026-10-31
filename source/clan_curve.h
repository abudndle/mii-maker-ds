#ifndef MDS_CLAN_CURVE_H
#define MDS_CLAN_CURVE_H
#include <stdint.h>
#include <stddef.h>
/* Fixed-point Q16.16 CLAN Hermite interpolation (no ARM9 FPU required). */
typedef struct {int32_t frame,value,tangent;} MdsClanKey;
int32_t mds_clan_curve_eval(const MdsClanKey *,size_t count,int32_t frame);
int32_t mds_clan_visibility_eval(const MdsClanKey *,size_t count,int32_t frame);
#endif
