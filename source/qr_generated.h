/* Original QR and photo-selector touch bounds. */
typedef struct {int page,x,y,w,h,action;} MdsQrHit;
static const MdsQrHit qr_hits[]={
{0,28,11,200,42,4},
{0,28,64,200,42,1},
{0,28,115,200,42,2},
{1,46,63,69,69,3},
{1,142,63,69,69,2},
};
#define MDS_QR_HITS (sizeof(qr_hits)/sizeof(qr_hits[0]))
