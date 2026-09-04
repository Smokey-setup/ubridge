UNAME_S := $(shell uname -s)

CC ?= gcc
COMMON_CFLAGS = -O3 -Wall -Wextra -Wpedantic -Werror -std=c11

ifeq ($(UNAME_S),Darwin)
	TARGET = ubridge/libubridge.dylib
	CFLAGS = $(COMMON_CFLAGS) -fPIC -dynamiclib -fvisibility=hidden
	LDFLAGS = -lm -pthread
	ROOT_LIB = libubridge.dylib
else ifeq ($(OS),Windows_NT)
	TARGET = ubridge/ubridge.dll
	CFLAGS = $(COMMON_CFLAGS) -shared -DUBRIDGE_BUILD
	LDFLAGS = -lm
	ROOT_LIB = ubridge.dll
else
	TARGET = ubridge/libubridge.so
	CFLAGS = $(COMMON_CFLAGS) -fPIC -shared -fvisibility=hidden
	LDFLAGS = -lm -pthread
	ROOT_LIB = libubridge.so
endif

all: $(TARGET) $(ROOT_LIB)

$(TARGET): ubridge.c ubridge.h
	@mkdir -p ubridge
	$(CC) $(CFLAGS) -o $@ ubridge.c $(LDFLAGS)

$(ROOT_LIB): $(TARGET)
	cp $(TARGET) $(ROOT_LIB)

clean:
	rm -f ubridge/libubridge.so ubridge/libubridge.dylib ubridge/ubridge.dll
	rm -f libubridge.so libubridge.dylib ubridge.dll
