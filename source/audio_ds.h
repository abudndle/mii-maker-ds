#ifndef MDS_AUDIO_DS_H
#define MDS_AUDIO_DS_H
/* Audio is an optional NitroFS soundbank. Missing/private original audio
 * must never stop the ROM from booting or make menu input dependent on it. */
typedef enum {
 MDS_AUDIO_MOVE=0,
 MDS_AUDIO_CONFIRM=1,
 MDS_AUDIO_CANCEL=2,
 MDS_AUDIO_EVENT_COUNT=3
} MdsAudioEvent;
int mds_audio_init(void);
int mds_audio_ready(void);
void mds_audio_play(MdsAudioEvent event);
#endif
