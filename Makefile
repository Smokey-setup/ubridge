UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	TARGET = libubridge.dylib
	CFLAGS = -O3 -Wall -fPIC -dynamiclib
else ifeq ($(OS),Windows_NT)
	TARGET = ubridge.dll
	CFLAGS = -O3 -Wall -shared
else
	TARGET = libubridge.so
	CFLAGS = -O3 -Wall -fPIC -shared
endif

CC = gcc

all: $(TARGET)

$(TARGET): ubridge.c ubridge.h
	$(CC) $(CFLAGS) -o $(TARGET) ubridge.c

clean:
	rm -f $(TARGET)
