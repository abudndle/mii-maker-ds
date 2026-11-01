#ifndef MDS_HOST_MOCK_NDS_H
#define MDS_HOST_MOCK_NDS_H
typedef struct {char gameCode[4];} MdsHostNdsHeader;
extern MdsHostNdsHeader *__NDSHeader;
#define BUS_OWNER_ARM9 0
static inline void sysSetCardOwner(int owner){(void)owner;}
#endif
