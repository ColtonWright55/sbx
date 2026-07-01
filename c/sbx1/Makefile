CC = cc
CFLAGS = -std=c2x -Wall -Wextra -O2

build/sbx1: src/main.c
	mkdir -p build
	$(CC) $(CFLAGS) -o build/sbx1 src/main.c

.PHONY: clean
clean:
	rm -rf build
