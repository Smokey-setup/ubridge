UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
	TARGET = libubridge.dylib
	CFLAGS = -O3 -Wall -Wextra -fPIC -dynamiclib -std=c11
	LDFLAGS = -lm
else ifeq ($(OS),Windows_NT)
	TARGET = ubridge.dll
	CFLAGS = -O3 -Wall -Wextra -shared -std=c11
	LDFLAGS = -lm
else
	TARGET = libubridge.so
	CFLAGS = -O3 -Wall -Wextra -fPIC -shared -std=c11
	LDFLAGS = -lm
endif

CC ?= gcc

all: $(TARGET)

$(TARGET): ubridge.c ubridge.h
	$(CC) $(CFLAGS) -o $(TARGET) ubridge.c $(LDFLAGS)

clean:
	rm -f $(TARGET)
