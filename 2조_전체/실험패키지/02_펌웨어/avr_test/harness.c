// simavr로 실제 wc_meter.elf(ATmega328P, 16 MHz)를 사이클 단위로 실행하는 검증 하네스
// - 회로 모델(사인 필터·CS·페이스트 이중층 / 사각 핀저항), ADC 응답, DS18B20 1-Wire 슬레이브, UART 입출력
// 사용: ./harness wc_meter.elf R20 T_C clip(sine|sq) "명령1;명령2;..." [I2C=0]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <simavr/sim_avr.h>
#include <simavr/sim_elf.h>
#include <simavr/avr_uart.h>
#include <simavr/avr_adc.h>
#include <simavr/avr_ioport.h>
#include <simavr/sim_cycle_timers.h>
static avr_t *avr; static double R20=200,Tp=20; static int clip=1;
static double f1=2.11,f2=2.11,vcs=2.11-1.813,vdl=0,vdlq=0; const double VG=1.813;
static avr_irq_t *pinD2;
#define T_US ((double)avr->cycle/16.0)
static double Rnow(void){return R20/(1+0.02*(Tp-20));}
static void model(double *vd,double *vn,double *v9,double *v1){
  double vb=fmin(fmax(f2,0.02),3.5); *vd=vb-vcs; double R=Rnow();
  if(clip==1){double i=(*vd-VG-vdl)/(330+R); *vn=VG+vdl+i*R;} else *vn=*vd;
  uint8_t ddrb=avr->data[0x24], portb=avr->data[0x25]; int o9=ddrb&2,o8=ddrb&1; double s9=(portb&2)?5:0,s8=(portb&1)?5:0;
  if(o9&&o8&&clip==2){double r9=s9?28:24,r8=s8?29:23,I=(s9-s8-vdlq)/(r9+330+R+r8); *v9=s9-I*r9; *v1=s8+I*r8+I*R+vdlq;}
  else {*v9=o9?s9:0; *v1=*v9;}
}
static void step(double dt){
  double vin=5.0*avr->data[0xB4]/256.0, tau=1/(2*M_PI*2300.0);
  f1+=dt*1e-6/tau*(vin-f1); f2+=dt*1e-6/tau*(f1-f2);
  double vd,vn,v9,v1; model(&vd,&vn,&v9,&v1); double R=Rnow();
  double i= clip==1?(vd-VG-vdl)/(330+R):0; vcs+=i/10e-6*dt*1e-6; vdl+=(i-vdl/100e3)/40e-6*dt*1e-6;
  uint8_t ddrb=avr->data[0x24],portb=avr->data[0x25]; int o9=ddrb&2,o8=ddrb&1; double s9=(portb&2)?5:0,s8=(portb&1)?5:0;
  if(o9&&o8&&clip==2){double r9=s9?28:24,r8=s8?29:23,I=(s9-s8-vdlq)/(r9+330+R+r8); vdlq+=(I-vdlq/100e3)/40e-6*dt*1e-6;}
}
// ---- ADC ----
static unsigned adcCount[8]; static double lastSq=-1, sqEdges=0, sqMaxRead=0, lastEdgeT=0; static uint8_t lastPortB=0;
static void adc_trig(avr_irq_t *irq,uint32_t value,void *p){
  avr_adc_mux_t m; memcpy(&m,&value,sizeof m); int ch=m.src;
  double vd,vn,v9,v1; model(&vd,&vn,&v9,&v1); double v= ch==0?vn: ch==1?vd: ch==2?v9: ch==3?v1: 0;
  if(ch<8) adcCount[ch]++;
  if(ch==3 && (avr->data[0x24]&3)==3){ double dtE=T_US-lastEdgeT; if(dtE>sqMaxRead) sqMaxRead=dtE; }
  avr_raise_irq(avr_io_getirq(avr,AVR_IOCTL_ADC_GETIRQ,ADC_IRQ_ADC0+ch),(uint32_t)lround(v*1000));
}
// ---- DS18B20 1-Wire 슬레이브 ----
static int mLow=0; static double tFall=0,slaveUntil=-1; static int st=0,bitc=0; static uint8_t rx=0,sp[9]; static int txbit=0, lineOut=1, cmdState=0;
static int dsPresentCnt=0, dsBytes=0; static double minPresenceGap=1e9;
static uint8_t crc8(const uint8_t*p,int n){uint8_t c=0;while(n--){uint8_t in=*p++;for(int i=0;i<8;i++){uint8_t mx=(c^in)&1;c>>=1;if(mx)c^=0x8C;in>>=1;}}return c;}
static void gotByte(uint8_t b){ dsBytes++;
  if(cmdState==0){ cmdState = (b==0xCC)?1:9; }
  else if(cmdState==1){ if(b==0x44) cmdState=9; else if(b==0xBE){ int16_t raw=(int16_t)lround(Tp*16); sp[0]=raw&255;sp[1]=(raw>>8)&255;sp[2]=0x4B;sp[3]=0x46;sp[4]=0x7F;sp[5]=0xFF;sp[6]=0x0C;sp[7]=0x10;sp[8]=crc8(sp,8); txbit=0; cmdState=2; } } }
static void ow_poll(void){
  int low = (avr->data[0x2A]&4) && !(avr->data[0x2B]&4);   // DDRD2=1 && PORTD2=0
  double t=T_US;
  if(low && !mLow){ tFall=t; if(cmdState==2 && txbit<72){ int b=(sp[txbit/8]>>(txbit%8))&1; if(!b) slaveUntil=t+30; txbit++; } }
  if(!low && mLow){ double d=t-tFall;
    if(d>=400){ slaveUntil=-1; cmdState=0; bitc=0; rx=0; slaveUntil=t+30+120; tFall=t+30; dsPresentCnt++; st=1; }
    else if(cmdState!=2){ int bit = d<15; rx|= bit<<bitc; if(++bitc==8){ gotByte(rx); bitc=0; rx=0; } } }
  mLow=low;
  int slow = slaveUntil>0 && t< slaveUntil && t>= (st==1? tFall: 0);
  if(st==1 && t>=slaveUntil) st=0;
  int line = !(low||slow);
  if(line!=lineOut){ lineOut=line; avr_raise_irq(pinD2,line); }
}
// ---- 주기 타이머: 0.5 µs마다 1-Wire, 2 µs마다 회로 ----
static int tick=0;
static avr_cycle_count_t timer_cb(avr_t *a,avr_cycle_count_t when,void *p){
  ow_poll();
  uint8_t pb=avr->data[0x25]&3; if(pb!=lastPortB && (avr->data[0x24]&3)==3){ sqEdges++; lastEdgeT=T_US; } lastPortB=pb;
  if(++tick==4){ tick=0; step(2.0); }
  return when+8;
}
// ---- UART ----
static char out[1<<20]; static int outn=0;
static void uart_out(avr_irq_t *irq,uint32_t v,void *p){ if(outn<(int)sizeof(out)-1) out[outn++]=(char)v; putchar((char)v); }
int main(int argc,char**argv){
  elf_firmware_t fw={{0}}; elf_read_firmware(argv[1],&fw);
  R20=atof(argv[2]); Tp=atof(argv[3]); clip= !strcmp(argv[4],"sq")?2:!strcmp(argv[4],"none")?0:1;
  avr=avr_make_mcu_by_name("atmega328p"); avr_init(avr); avr->frequency=16000000; avr_load_firmware(avr,&fw);
  avr->avcc=5000; avr->aref=5000; avr->vcc=5000;
  uint32_t fl=0; avr_ioctl(avr,AVR_IOCTL_UART_GET_FLAGS('0'),&fl); fl&=~AVR_UART_FLAG_STDIO; avr_ioctl(avr,AVR_IOCTL_UART_SET_FLAGS('0'),&fl);
  avr_irq_register_notify(avr_io_getirq(avr,AVR_IOCTL_UART_GETIRQ('0'),UART_IRQ_OUTPUT),uart_out,NULL);
  avr_irq_register_notify(avr_io_getirq(avr,AVR_IOCTL_ADC_GETIRQ,ADC_IRQ_OUT_TRIGGER),adc_trig,NULL);
  pinD2=avr_io_getirq(avr,AVR_IOCTL_IOPORT_GETIRQ('D'),2); avr_raise_irq(pinD2,1);
  avr_raise_irq(avr_io_getirq(avr,AVR_IOCTL_IOPORT_GETIRQ('D'),7),1);    // 버튼 안 눌림
  avr_cycle_timer_register(avr,8,timer_cb,NULL);
  avr_irq_t *uin=avr_io_getirq(avr,AVR_IOCTL_UART_GETIRQ('0'),UART_IRQ_INPUT);
  char cmds[512]; strncpy(cmds,argc>5?argv[5]:"",511); char *save=NULL; char *tok=strtok_r(cmds,";",&save);
  double nextCmdT=1.5e6; double endT=0; int state;
  while(1){
    state=avr_run(avr);
    if(state==cpu_Done||state==cpu_Crashed){ printf("\n[CPU %s]\n",state==cpu_Crashed?"CRASH":"done"); break; }
    if(T_US>=nextCmdT){
      if(!tok){ if(endT==0) endT=T_US+2e5; }
      else { // 메시지 경계를 기다렸다가 한 글자씩 (115200 bps ≈ 87 µs/byte)
        static int ci=0; char c= tok[ci]? tok[ci] : '\n';
        avr_raise_irq(uin,(uint8_t)c); nextCmdT=T_US+200;
        if(!tok[ci]){ ci=0; tok=strtok_r(NULL,";",&save); nextCmdT=T_US+ (tok? 6e6:0); if(!tok) endT=T_US+9e6; } else ci++; }
    }
    if(endT>0 && T_US>endT) break;
    if(T_US>60e6){ printf("\n[TIMEOUT]\n"); break; }
  }
  fprintf(stderr,"\n[harness] sim_time=%.3f s  adcReads A0..A3=%u %u %u %u  sqEdges=%.0f  max(A3 read - edge)=%.1f us  ds_presence=%d ds_bytes=%d\n",
    T_US/1e6,adcCount[0],adcCount[1],adcCount[2],adcCount[3],sqEdges,sqMaxRead,dsPresentCnt,dsBytes);
  return 0;
}
