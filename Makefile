UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	TARGET = libubridge.dylib
else ifeq ($(OS),Windows_NT)
	TARGET = ubridge.dll
else
	TARGET = libubridge.so
endif

CC = gcc
CFLAGS = -O3 -Wall -fPIC -shared

all: $(TARGET)

$(TARGET): ubridge.c ubridge.h
	$(CC) $(CFLAGS) -o $(TARGET) ubridge.c

clean:
	rm -f $(TARGET)
