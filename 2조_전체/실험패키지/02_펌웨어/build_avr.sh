#!/bin/bash
# Arduino IDE 없이 avr-gcc로 Uno용 빌드 (검증용). 팀은 Arduino IDE에서 그냥 업로드하면 됨.
set -e
HW=/usr/share/arduino/hardware/arduino/avr
B=${BUILD:-/tmp/wc_build}; rm -rf $B; mkdir -p $B/core $B/lib
F="-mmcu=atmega328p -DF_CPU=16000000L -DARDUINO=10819 -DARDUINO_AVR_UNO -DARDUINO_ARCH_AVR -Os -ffunction-sections -fdata-sections -Wall -Wextra"
INC="-I$HW/cores/arduino -I$HW/variants/standard -I$HW/libraries/Wire/src -I$HW/libraries/Wire/src/utility -I$HW/libraries/EEPROM/src"
for s in $HW/cores/arduino/*.c $HW/libraries/Wire/src/utility/twi.c; do avr-gcc $F $INC -c $s -o $B/core/$(basename $s).o 2>/dev/null; done
for s in $HW/cores/arduino/*.cpp $HW/libraries/Wire/src/Wire.cpp; do avr-g++ $F -std=gnu++11 -fno-exceptions -fno-threadsafe-statics $INC -c $s -o $B/core/$(basename $s).o 2>/dev/null; done
avr-gcc $F -x assembler-with-cpp $INC -c $HW/cores/arduino/wiring_pulse.S -o $B/core/wiring_pulse.S.o
( echo '#include <Arduino.h>'; echo '#line 1 "wc_meter.ino"'; cat wc_meter/wc_meter.ino ) > $B/sketch.cpp
avr-g++ $F -std=gnu++11 -fno-exceptions -fno-threadsafe-statics $INC -c $B/sketch.cpp -o $B/sketch.o
avr-gcc -mmcu=atmega328p -Os -Wl,--gc-sections $B/sketch.o $B/core/*.o -o $B/wc_meter.elf -lm
avr-objcopy -O ihex -R .eeprom $B/wc_meter.elf $B/wc_meter.hex
avr-size -C --mcu=atmega328p $B/wc_meter.elf | grep -E "Program|Data"
