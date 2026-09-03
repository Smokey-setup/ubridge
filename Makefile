UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
	TARGET = ubridge/libubridge.dylib
	CFLAGS = -O3 -Wall -Wextra -fPIC -dynamiclib -std=c11
	LDFLAGS = -lm -pthread
else ifeq ($(OS),Windows_NT)
	TARGET = ubridge/ubridge.dll
	CFLAGS = -O3 -Wall -Wextra -shared -std=c11
	LDFLAGS = -lm
else
	TARGET = ubridge/libubridge.so
	CFLAGS = -O3 -Wall -Wextra -fPIC -shared -std=c11
	LDFLAGS = -lm -pthread
endif

CC ?= gcc

all: $(TARGET)

$(TARGET): ubridge.c ubridge.h
	$(CC) $(CFLAGS) -o $(TARGET) ubridge.c $(LDFLAGS)

clean:
	rm -f ubridge/libubridge.so ubridge/libubridge.dylib ubridge/ubridge.dll libubridge.so libubridge.dylib ubridge.dll
