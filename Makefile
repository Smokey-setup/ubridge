CC = gcc
CFLAGS = -O3 -Wall -fPIC -shared
TARGET = libubridge.so

all: $(TARGET)

$(TARGET): ubridge.c ubridge.h
$(CC) $(CFLAGS) -o $(TARGET) ubridge.c

clean:
rm -f $(TARGET)
