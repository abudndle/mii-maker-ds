/* Optional original-source Mii body GPU validation ROM.
 * Nitro Engine delegates animated DSM/DSA drawing to DSMA.
 * This does NOT replace the existing 2D Mii Maker editor or provide
 * final original 3DS texture and animation fidelity.
 */
#include <nds.h>
#include <filesystem.h>
#include <NEMain.h>
#include <stdio.h>

typedef struct {
    NE_Camera *camera;
    NE_Model *model;
} Mds3DScene;

static void draw_scene(void *arg)
{
    Mds3DScene *scene=(Mds3DScene *)arg;
    if(!scene||!scene->camera||!scene->model)return;
    NE_CameraUse(scene->camera);
    NE_PolyFormat(31,0,NE_LIGHT_0,NE_CULL_NONE,0);
    NE_ModelDraw(scene->model);
}
int main(void)
{
    /* Nitro Engine owns the 3D top screen. The standard libnds 2D
     * console remains on the lower screen for diagnostics and controls. */
    irqSet(IRQ_VBLANK,NE_VBLFunc);
    irqSet(IRQ_HBLANK,NE_HBLFunc);
    irqEnable(IRQ_HBLANK);
    if(NE_Init3D()!=0)return 1;
    NE_TextureSystemReset(0,0,NE_VRAM_AB);
    consoleDemoInit();

    if(!nitroFSInit(NULL)){
        iprintf("Missing private NitroFS\nmodel assets.\n");
        for(;;)swiWaitForVBlank();
    }
    Mds3DScene scene={0};
    scene.model=NE_ModelCreate(NE_Animated);
    scene.camera=NE_CameraCreate();
    NE_Animation *clip=NE_AnimationCreate();
    if(!scene.model||!scene.camera||!clip){
        iprintf("3D allocation failed\n");
        for(;;)swiWaitForVBlank();
    }
    /* Source-derived, privately staged: not included in public builds. */
    if(!NE_ModelLoadDSMFAT(scene.model,"nitro:/models/MiiBody_dsm.bin")||
       !NE_AnimationLoadFAT(clip,"nitro:/models/MiiBody_dsa.bin")){
        iprintf("Private DSM / DSA absent\n");
        iprintf("Run dsma-private-model\n");
        for(;;)swiWaitForVBlank();
    }
    NE_ModelSetAnimation(scene.model,clip);
    NE_ModelAnimStart(scene.model,NE_ANIM_LOOP,floattof32(0.1));
    NE_CameraSet(scene.camera,6,3,-4,0,3,0,0,1,0);
    NE_ClearColorSet(NE_Black,31,63);
    NE_LightSet(0,NE_White,0,-1,-1);
    iprintf("Original Mii body\nNitro Engine / DSMA\nD-pad: rotate\nSTART: exit\n");
    while(1){
        NE_WaitForVBL(NE_UPDATE_ANIMATIONS);
        scanKeys();
        unsigned held=keysHeld();
        if(held&KEY_START)break;
        if(held&KEY_LEFT)NE_ModelRotate(scene.model,0,-2,0);
        if(held&KEY_RIGHT)NE_ModelRotate(scene.model,0,2,0);
        if(held&KEY_UP)NE_ModelRotate(scene.model,0,0,2);
        if(held&KEY_DOWN)NE_ModelRotate(scene.model,0,0,-2);
        NE_ProcessArg(draw_scene,&scene);
    }
    return 0;
}
