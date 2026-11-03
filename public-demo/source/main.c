/* Standalone public-domain-compatible homebrew diagnostic.
 * No Nintendo game resources or original Mii Maker source are linked.
 */
#include <nds.h>
#include <stdio.h>

int main(void) {
    consoleDemoInit();
    iprintf("PUBLIC DS TEST ROM\n");
    iprintf("==================\n\n");
    iprintf("Synthetic homebrew only\n");
    iprintf("No original game assets\n\n");
    iprintf("A: increment counter\n");
    iprintf("START: reset counter\n\n");
    int counter = 0;
    while (1) {
        swiWaitForVBlank();
        scanKeys();
        unsigned int down = keysDown();
        if (down & KEY_A) ++counter;
        if (down & KEY_START) counter = 0;
        iprintf("\x1b[10;0HCounter: %d      ", counter);
    }
}
