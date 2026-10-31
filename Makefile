# BlocksDS supported build. Override BLOCKSDS/WONDERFUL_TOOLCHAIN if installed elsewhere.
export BLOCKSDS ?= /opt/wonderful/thirdparty/blocksds/core
export WONDERFUL_TOOLCHAIN ?= /opt/wonderful
NAME := mii-ds
GAME_TITLE := Mii Maker DS
GAME_SUBTITLE := Create and edit Mii characters
GAME_ICON := assets/ui/original-icon.gif
GAME_AUTHOR := Independent demake
SOURCEDIRS := source
NITROFSDIR := nitrofiles
LIBS := -lnds9 -lm
CFLAGS := -Wextra -Werror $(EXTRA_CFLAGS)
ifeq ($(SDK_STAGE),1)
include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile
NDSTOOL_ARGS += -g MDSD

# Changes to the banner or any embedded asset must repack the ROM.
$(ROM): Makefile $(GAME_ICON) $(shell find nitrofiles -type f)

else
.DEFAULT_GOAL := all
.PHONY: all $(NAME).nds clean dump
all: $(NAME).nds
$(NAME).nds:
	python3 tools/build_preflight.py
	python3 tools/check_assets.py $(if $(findstring MDS_IMPORT_TEST_FILES,$(EXTRA_CFLAGS)),--allow-test-import,)
	+$(MAKE) SDK_STAGE=1 $(NAME).nds
	python3 tools/fix_nds_regions.py $@
clean dump:
	+$(MAKE) SDK_STAGE=1 $@
endif
