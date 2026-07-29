AS      := as
LD      := ld
BUILD   := build
SRCS    := $(wildcard *.asm)
BINS    := $(addprefix $(BUILD)/,$(SRCS:.asm=))

.PHONY: all clean

all: $(BINS)

$(BUILD)/%: $(BUILD)/%.o | $(BUILD)
	$(LD) -o $@ $<

$(BUILD)/%.o: %.asm | $(BUILD)
	$(AS) -o $@ $<

$(BUILD):
	mkdir -p $(BUILD)

clean:
	rm -rf $(BUILD)
