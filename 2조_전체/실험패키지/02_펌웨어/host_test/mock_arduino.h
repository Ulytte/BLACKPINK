// PC에서 wc_meter.ino를 그대로 컴파일·실행하기 위한 가짜 Arduino (검증용)
#pragma once
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cmath>
#include <string>
using std::isnan;
typedef uint8_t byte; typedef bool boolean;
#define PI 3.14159265358979323846
#define HEX 16
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define LOW 0
#define HIGH 1
#define A0 14
#define A1 15
#define A2 16
#define A3 17
#define _BV(b) (1u<<(b))
#define TOIE2 0
#define COM2B1 5
#define WGM21 1
#define WGM20 0
#define CS20 0
class __FlashStringHelper;
#define F(s) ((const __FlashStringHelper*)(s))
#define ISR(v) void v()
void TIMER2_OVF_vect();
extern uint8_t TCCR2A,TCCR2B,OCR2B,TIMSK2,PORTB,DDRB;
unsigned long micros(); unsigned long millis(); void delay(unsigned long ms); void delayMicroseconds(unsigned int us);
void noInterrupts(); void interrupts();
int analogRead(uint8_t ch); void pinMode(uint8_t p,uint8_t m); void digitalWrite(uint8_t p,uint8_t v); int digitalRead(uint8_t p);
char *dtostrf(double v, signed char w, unsigned char prec, char *s);
struct SerialMock {
  void begin(long){}
  int available(); int read();
  void print(const char*s); void print(const __FlashStringHelper*s){print((const char*)s);}
  void print(char c){char b[2]={c,0};print(b);} void print(int v){print((long)v);} void print(unsigned v){print((unsigned long)v);}
  void print(long v); void print(unsigned long v); void print(unsigned long v,int base); void print(uint8_t v,int base){print((unsigned long)v,base);}
  void print(double v,int d=2);
  template<class T> void println(T v){print(v);print("\n");} template<class T> void println(T v,int d){print(v,d);print("\n");}
  void println(){print("\n");}
};
extern SerialMock Serial;
struct WireMock { void begin(){} void beginTransmission(uint8_t a); size_t write(uint8_t v); uint8_t endTransmission(); };
extern WireMock Wire;
struct EEPROMMock { uint8_t mem[1024]; template<class T> void put(int a,const T&v){memcpy(mem+a,&v,sizeof(T));} template<class T> void get(int a,T&v){memcpy(&v,mem+a,sizeof(T));} };
extern EEPROMMock EEPROM;
#define PROGMEM
#define pgm_read_byte(p) (*(const uint8_t*)(p))
#define TOV2 0
extern uint8_t TCNT2, TIFR2;
