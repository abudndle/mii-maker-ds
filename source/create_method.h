#ifndef MDS_CREATE_METHOD_H
#define MDS_CREATE_METHOD_H
/* Creation menu acts independently of camera hardware. Photo means
 * DSi inward camera preview ONLY, never a generated Mii. */
typedef enum {
 MDS_CREATE_NONE=0,
 MDS_CREATE_SCRATCH=1,
 MDS_CREATE_PHOTO_PREVIEW=2,
 MDS_CREATE_BACK=3
} MdsCreateChoice;
MdsCreateChoice mds_create_method_select(int selection,int dsi_enabled);
MdsCreateChoice mds_create_method_touch(int x,int y,int dsi_enabled);
#endif
