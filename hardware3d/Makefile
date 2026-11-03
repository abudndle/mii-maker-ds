# Opt-in BlocksDS Nitro Engine / DSMA GPU test ROM.
# Build only in a private workspace with Nitro Engine installed.
export BLOCKSDS ?= /opt/wonderful/thirdparty/blocksds/core
export WONDERFUL_TOOLCHAIN ?= /opt/wonderful
export BLOCKSDSEXT ?= /opt/wonderful/thirdparty/blocksds/external
NAME := mii-body-gpu-test
GAME_TITLE := Mii Body GPU Test
GAME_SUBTITLE := Original body validation
GAME_ICON := ../assets/ui/original-icon.gif
GAME_AUTHOR := Independent demake
SOURCEDIRS := source
NITROFSDIR := nitrofiles
LIBS := -lNE -lnds9 -lm
LIBDIRS := $(BLOCKSDSEXT)/nitro-engine $(BLOCKSDS)/libs/libnds
CFLAGS := -Wextra -Werror
include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile
