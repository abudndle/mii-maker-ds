/* Standalone public-domain-compatible homebrew diagnostic.
 * No Nintendo game resources or original Mii Maker source are linked.
 */
#include <nds.h>
#include <stdio.h>

int main(void) {
    consoleDemoInit();
    printf("PUBLIC DS TEST ROM\n");
    printf("==================\n\n");
    printf("Synthetic homebrew only\n");
    printf("No original game assets\n\n");
    printf("A: increment counter\n");
    printf("START: reset counter\n\n");
    int counter = 0;
    while (1) {
        swiWaitForVBlank();
        scanKeys();
        unsigned int down = keysDown();
        if (down & KEY_A) ++counter;
        if (down & KEY_START) counter = 0;
        printf("\x1b[10;0HCounter: %d      ", counter);
    }
}
