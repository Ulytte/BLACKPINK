// 회로 모델 + 시나리오 실행기. 표준입력으로 시나리오를 받는다.
//   set R 200 | set clip sine|sq|none | set T 22 | set alphaT 0.02 | set noise 1 | set hum 0.05 | set ds 0|1
//   set rq 330 | set r1 330 | cmd <명령> | press <ms> | reboot | lcd | wait <ms>
#include "mock_arduino.h"
#include <random>
#include <deque>
#include <iostream>
uint8_t TCCR2A,TCCR2B,OCR2B=108,TIMSK2,PORTB,DDRB,TCNT2,TIFR2;
SerialMock Serial; WireMock Wire; EEPROMMock EEPROM;
void setup(); void loop();
// ---------- 모델 파라미터 ----------
double R20=200, Tpaste=20, alphaT=0.02, R1t=330, RQt=330, noiseLSB=1, hum=0, CS=10e-6, Cdl=40e-6, Rlk=100e3, VG=1.813;
double rH9=28,rL9=24,rH8=29,rL8=23;   // 핀 출력저항 (D8을 일부러 조금 다르게)
int clip=1;   // 0 none 1 sine 2 square
bool dsPresent=true; long btnUntil=-1;
// ---------- 상태 ----------
double T_us=0, nextTick=16, f1=2.11, f2=2.11, vcs=2.11-1.813, vdl=0, vdlq=0;
std::mt19937 rng(12345); std::normal_distribution<double> g(0,1);
double Rnow(){ return R20/(1+alphaT*(Tpaste-20)); }
struct V { double vd,vn,v9,v1; };
V node(){
  double vbuf=std::min(std::max(f2,0.02),3.5); V o; double R=Rnow();
  double vd=vbuf-vcs; double i=0;
  if(clip==1){ i=(vd-VG-vdl)/(R1t+R); o.vn=VG+vdl+i*R; } else o.vn=vd;
  o.vd=vd;
  bool o9=DDRB&2, o8=DDRB&1; double s9=(PORTB&2)?5:0, s8=(PORTB&1)?5:0;
  if(o9&&o8&&clip==2){ double r9=s9?rH9:rL9, r8=s8?rH8:rL8; double I=(s9-s8-vdlq)/(r9+RQt+R+r8);
    o.v9=s9-I*r9; double v4=s8+I*r8; o.v1=v4+I*R+vdlq; }
  else { o.v9=o9?s9:0; o.v1=o.v9; }
  return o;
}
void step(double dt){
  double vin=5.0*OCR2B/256.0, tau=1/(2*PI*2300.0);
  { double k=1-exp(-dt*1e-6/tau); f1+=k*(vin-f1); f2+=k*(f1-f2); }
  double vbuf=std::min(std::max(f2,0.02),3.5), vd=vbuf-vcs, R=Rnow();
  double i = clip==1 ? (vd-VG-vdl)/(R1t+R) : 0;
  vcs+=i/CS*dt*1e-6; vdl+=(i-vdl/Rlk)/Cdl*dt*1e-6;
  bool o9=DDRB&2,o8=DDRB&1; double s9=(PORTB&2)?5:0,s8=(PORTB&1)?5:0;
  if(o9&&o8&&clip==2){ double r9=s9?rH9:rL9,r8=s8?rH8:rL8; double I=(s9-s8-vdlq)/(r9+RQt+R+r8); vdlq+=(I-vdlq/Rlk)/Cdl*dt*1e-6; }
  else vdlq-=vdlq/(Rlk*Cdl)*dt*1e-6;
}
void advance(double us){
  while(us>0){ double d=std::min(us,(TIMSK2||(DDRB&3))?2.0:200.0); step(d); T_us+=d; us-=d;
    while(T_us>=nextTick){ nextTick+=16; if(TIMSK2&_BV(TOIE2)) TIMER2_OVF_vect(); } }
}
static void updTCNT(){ TCNT2=(uint8_t)(fmod(T_us,16.0)/16.0*256); }
unsigned long micros(){ advance(1); return (unsigned long)T_us; }
unsigned long millis(){ return (unsigned long)(T_us/1000); }
void delay(unsigned long ms){ advance(ms*1000.0); }
void delayMicroseconds(unsigned int us){ advance(us); }
void noInterrupts(){ updTCNT(); } void interrupts(){}
int analogRead(uint8_t ch){
  advance(12); V o=node(); double v=0, h=hum*sin(2*PI*60*T_us*1e-6);
  switch(ch){case A0:v=o.vn+h;break;case A1:v=o.vd;break;case A2:v=o.v9;break;case A3:v=o.v1+(clip==2?h:0);break;}
  double c=v/5*1023+noiseLSB*g(rng); int k=(int)lround(c); k=k<0?0:k>1023?1023:k;
  advance(100); return k;
}
void pinMode(uint8_t p,uint8_t m){ if(p==9){ if(m==OUTPUT)DDRB|=2; else DDRB&=~2;} if(p==8){ if(m==OUTPUT)DDRB|=1; else DDRB&=~1;} }
void digitalWrite(uint8_t p,uint8_t v){ if(p==9){ if(v)PORTB|=2; else PORTB&=~2;} if(p==8){ if(v)PORTB|=1; else PORTB&=~1;} }
int digitalRead(uint8_t p){ if(p==7) return (btnUntil>=0 && millis()<(unsigned long)btnUntil)?LOW:HIGH; return HIGH; }
char *dtostrf(double v, signed char w, unsigned char prec, char *s){ sprintf(s,"%*.*f",w,prec,v); return s; }
// ---------- Serial ----------
std::deque<char> inq; std::string outbuf;
int SerialMock::available(){ return inq.size(); }
int SerialMock::read(){ char c=inq.front(); inq.pop_front(); return c; }
void SerialMock::print(const char*s){ fputs(s,stdout); }
void SerialMock::print(long v){ printf("%ld",v); } void SerialMock::print(unsigned long v){ printf("%lu",v); }
void SerialMock::print(unsigned long v,int b){ if(b==16) printf("%lX",v); else printf("%lu",v); }
void SerialMock::print(double v,int d){ printf("%.*f",d,v); }
// ---------- DS18B20 (바이트 단위) ----------
int owState=0, owPos=0; uint8_t sp[9];
uint8_t crc8x(const uint8_t*p,int n){uint8_t c=0;while(n--){uint8_t in=*p++;for(int i=0;i<8;i++){uint8_t m=(c^in)&1;c>>=1;if(m)c^=0x8C;in>>=1;}}return c;}
bool owReset(){ advance(960); owState=0; return dsPresent; }
void owWrite(uint8_t v){ advance(560); if(v==0xBE){ int16_t raw=(int16_t)lround(Tpaste*16); sp[0]=raw&0xFF; sp[1]=(raw>>8)&0xFF; sp[2]=0x4B;sp[3]=0x46;sp[4]=0x7F;sp[5]=0xFF;sp[6]=0x0C;sp[7]=0x10; sp[8]=crc8x(sp,8); owPos=0; owState=2; } }
uint8_t owRead(){ advance(560); if(!dsPresent) return 0xFF; return owState==2&&owPos<9? sp[owPos++]:0xFF; }
// ---------- LCD 디코더 ----------
uint8_t curAddr; bool en=false, mode8=true, haveHi=false; uint8_t hi, lastv; int cur=0; char scr[2][17];
void lcdApply(uint8_t b,bool rs){
  if(!rs){ if(b==1){memset(scr,' ',sizeof scr);scr[0][16]=scr[1][16]=0;cur=0;} else if(b&0x80){ uint8_t a=b&0x7F; cur=(a>=0x40?16:0)+(a&0x0F);} }
  else { if(cur<32){ scr[cur/16][cur%16]=b; cur++; } }
}
void WireMock::beginTransmission(uint8_t a){ curAddr=a; }
size_t WireMock::write(uint8_t v){
  if(curAddr!=0x27) return 1;
  bool e=v&4; if(en && !e){ uint8_t nib=lastv&0xF0; bool rs=lastv&1;
    if(mode8){ if(nib==0x20) mode8=false; }
    else if(!haveHi){ hi=nib; haveHi=true; } else { haveHi=false; lcdApply(hi|(nib>>4),rs); } }
  en=e; lastv=v; return 1; }
uint8_t WireMock::endTransmission(){ return curAddr==0x27?0:2; }
// ---------- 시나리오 ----------
void pump(){ for(int k=0;k<5;k++) loop(); }
int main(){
  memset(EEPROM.mem,0xFF,sizeof EEPROM.mem); memset(scr,' ',sizeof scr); scr[0][16]=scr[1][16]=0;
  setup(); std::string line;
  while(std::getline(std::cin,line)){
    if(line.empty()||line[0]=='#') continue;
    printf(">>> %s\n",line.c_str());
    char a[32]={0},b[64]={0}; sscanf(line.c_str(),"%31s %63[^\n]",a,b);
    std::string A=a,B=b;
    if(A=="set"){ char k[16]; double v=0; char s[16]={0}; sscanf(b,"%15s %15s",k,s); v=atof(s); std::string K=k;
      if(K=="R")R20=v; else if(K=="T")Tpaste=v; else if(K=="alphaT")alphaT=v; else if(K=="noise")noiseLSB=v; else if(K=="hum")hum=v;
      else if(K=="ds")dsPresent=v!=0; else if(K=="rq")RQt=v; else if(K=="r1")R1t=v;
      else if(K=="clip"){ std::string S=s; clip= S=="sine"?1: S=="sq"?2:0; } }
    else if(A=="cmd"){ for(char c: B) inq.push_back(c); inq.push_back('\n'); pump(); }
    else if(A=="press"){ int ms=atoi(b); btnUntil=millis()+ms; while(millis()<(unsigned long)btnUntil){ loop(); advance(1000);} for(int k=0;k<3;k++){loop();advance(1000);} }
    else if(A=="reboot"){ T_us+=1e6; setup(); }
    else if(A=="wait"){ advance(atof(b)*1000); }
    else if(A=="lcd"){ printf("LCD|%s|\nLCD|%s|\n",scr[0],scr[1]); }
  }
}
