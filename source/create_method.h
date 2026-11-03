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
/* Atomic resolution for the optional creation menu. One input frame may
 * navigate OR choose, never navigate and choose a different Mii method.
 * Cancel always wins; valid touch wins over a simultaneous A confirmation. */
typedef struct {
 int cancel,confirm,touch,up,down,left,right;
 int x,y,selection,dsi_enabled;
} MdsCreateInput;
typedef struct {
 MdsCreateChoice choice;
 int selection;
} MdsCreateOutcome;
MdsCreateOutcome mds_create_method_input(MdsCreateInput input);
#endif
