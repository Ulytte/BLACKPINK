// =====================================================================
//  wc_meter.ino — 2조 W/C 판별 실험 펌웨어 (실험 보드 Rev 5 전용)
//  Arduino Uno. 추가 라이브러리 필요 없음 (Wire, EEPROM은 기본 포함)
//
//  핀
//   D3  사인파 PWM (Timer2, 62.5 kHz, 64단계 → 약 977 Hz)
//   A1  사인: 기준저항 R1 위쪽(구동)      A0  사인: 전극 쪽 노드
//   D9  사각: 구동 (+)                    D8  사각: 귀환 (−)
//   A2  사각: RQ 위쪽(D9 쪽)              A3  사각: 전극 쪽 노드
//   D2  DS18B20 (4.7 kΩ 풀업)             D7  버튼 (GND로, 내부 풀업)
//   A4/A5  I2C LCD 16x2 (주소 자동 탐색, 없어도 동작)
//
//  시리얼 115200, 줄 끝 "새 줄(LF)". 'h' 입력하면 명령 목록.
//  출력 줄 머리표: MEAS(측정 결과) REP(반복 1회) TEMP(온도) WARN(경고) #(설명)
// =====================================================================
#include <Wire.h>
#include <EEPROM.h>
#include <math.h>

// ---------------- 사인파 설정 (시뮬 xover_fix.py로 검증한 값) ----------------
const uint8_t N_TAB = 64;
const uint8_t MID   = 108;   // 중심 듀티 → 약 2.11 V
const uint8_t AMP   = 52;    // 진폭 듀티 → 약 1.02 V peak (출력 약 1.1~3.1 V)
const uint16_t SINE_PAIRS = 1500;   // A1·A0 번갈아 1500쌍 (약 0.4초)
// ---------------- 사각파 설정 ----------------
const uint16_t SQ_WARM   = 20;      // 예열 주기
const uint16_t SQ_CYCLES = 200;     // 측정 주기 (1 ms × 200 = 0.2초)
const uint16_t SQ_T_READ = 150;     // 엣지 후 첫 읽기 시각 [µs]
const uint16_t SQ_HALF   = 500;     // 반주기 [µs]
const uint8_t  REPS      = 3;       // 1회 측정 = 3번 반복의 중앙값
const uint8_t  REF_N     = 5;       // 기준 저장 시 측정 횟수

const uint8_t PIN_DS = 2, PIN_BTN = 7, PIN_SQ_DRV = 9, PIN_SQ_RET = 8, PIN_PWM = 3;

// ---------------- 설정 (EEPROM 저장) ----------------
struct Settings {
  uint16_t magic;
  float alpha;        // 온도계수 [1/°C], Z20 = Z × (1 + α(T − 20))
  float r1;           // 사인 기준저항 실측값 [Ω]
  float rq;           // 사각 기준저항 실측값 [Ω]
  float sig;          // 판정에 쓸 σ [Ω] (0이면 기준 반복 σ만 사용)
  float refMean[2];   // [0]=사인 [1]=사각, 20 °C 환산 기준값
  float refSD[2];
  uint8_t refN[2];
};
const uint16_t MAGIC = 0x2C05;
Settings S;

// ---------------- 상태 ----------------
uint8_t sineTab[N_TAB];
// 동기검파 기준 사인표 (256단계, ×127, 플래시에 저장). cos(k) = SIN256[(k+64)&255]
const int8_t SIN256[256] PROGMEM = {
     0,    3,    6,    9,   12,   16,   19,   22,   25,   28,   31,   34,   37,   40,   43,   46,
    49,   51,   54,   57,   60,   63,   65,   68,   71,   73,   76,   78,   81,   83,   85,   88,
    90,   92,   94,   96,   98,  100,  102,  104,  106,  107,  109,  111,  112,  113,  115,  116,
   117,  118,  120,  121,  122,  122,  123,  124,  125,  125,  126,  126,  126,  127,  127,  127,
   127,  127,  127,  127,  126,  126,  126,  125,  125,  124,  123,  122,  122,  121,  120,  118,
   117,  116,  115,  113,  112,  111,  109,  107,  106,  104,  102,  100,   98,   96,   94,   92,
    90,   88,   85,   83,   81,   78,   76,   73,   71,   68,   65,   63,   60,   57,   54,   51,
    49,   46,   43,   40,   37,   34,   31,   28,   25,   22,   19,   16,   12,    9,    6,    3,
     0,   -3,   -6,   -9,  -12,  -16,  -19,  -22,  -25,  -28,  -31,  -34,  -37,  -40,  -43,  -46,
   -49,  -51,  -54,  -57,  -60,  -63,  -65,  -68,  -71,  -73,  -76,  -78,  -81,  -83,  -85,  -88,
   -90,  -92,  -94,  -96,  -98, -100, -102, -104, -106, -107, -109, -111, -112, -113, -115, -116,
  -117, -118, -120, -121, -122, -122, -123, -124, -125, -125, -126, -126, -126, -127, -127, -127,
  -127, -127, -127, -127, -126, -126, -126, -125, -125, -124, -123, -122, -122, -121, -120, -118,
  -117, -116, -115, -113, -112, -111, -109, -107, -106, -104, -102, -100,  -98,  -96,  -94,  -92,
   -90,  -88,  -85,  -83,  -81,  -78,  -76,  -73,  -71,  -68,  -65,  -63,  -60,  -57,  -54,  -51,
   -49,  -46,  -43,  -40,  -37,  -34,  -31,  -28,  -25,  -22,  -19,  -16,  -12,   -9,   -6,   -3};
volatile uint8_t idx = 0;
char label[17] = "-";
float lastT = NAN; unsigned long lastTms = 0;
long  waterMs = -1;                    // 물 넣은 시각 (w 명령)
uint8_t mode = 0;                      // 0 사인, 1 사각 (버튼이 쓰는 모드)
bool lcdOK = false; uint8_t lcdAddr = 0;

// =====================================================================
//  사인파 발생 (Timer2)
// =====================================================================
ISR(TIMER2_OVF_vect) {
  OCR2B = sineTab[idx];
  idx = (idx + 1) & (N_TAB - 1);
}
void sineStart() { idx = 0; TIMSK2 = _BV(TOIE2); }
void sineStop()  { TIMSK2 = 0; OCR2B = MID; }   // 중심값 고정 → 커패시터 전압 유지, 전류 0

// 현재 사인 위상 (0~255 = 한 주기). idx(64단계) + PWM 카운터(TCNT2)로 4배 세분
uint8_t phase256() {
  noInterrupts();
  uint8_t i = idx, t = TCNT2;
  if ((TIFR2 & _BV(TOV2)) && t < 128) i = (i + 1) & (N_TAB - 1);   // 넘침 인터럽트 대기 중
  interrupts();
  return (uint8_t)((i << 2) | (t >> 6));
}

// =====================================================================
//  3×3 최소제곱: x ≈ a·cos + b·sin + c  (정규방정식, 가우스 소거)
// =====================================================================
struct Acc { long sx, sxc, sxs; long sc, ss, scc, sss, scs; unsigned long sxx; uint16_t n; };
void accClear(Acc &A) { memset(&A, 0, sizeof(A)); }
void accAdd(Acc &A, int x, uint8_t k) {
  int c = (int8_t)pgm_read_byte(&SIN256[(uint8_t)(k + 64)]), s = (int8_t)pgm_read_byte(&SIN256[k]);
  A.sx += x; A.sxc += (long)x * c; A.sxs += (long)x * s;
  A.sc += c; A.ss += s; A.scc += (long)c * c; A.sss += (long)s * s; A.scs += (long)c * s;
  A.sxx += (unsigned long)x * x; A.n++;
}
// 성공 시 a,b (단위: ADC 카운트) 반환
bool accSolve(const Acc &A, float &a, float &b) {
  float M[3][4] = {
    {(float)A.scc, (float)A.scs, (float)A.sc, (float)A.sxc},
    {(float)A.scs, (float)A.sss, (float)A.ss, (float)A.sxs},
    {(float)A.sc,  (float)A.ss,  (float)A.n,  (float)A.sx }};
  for (uint8_t i = 0; i < 3; i++) {
    uint8_t p = i;
    for (uint8_t r = i + 1; r < 3; r++) if (fabs(M[r][i]) > fabs(M[p][i])) p = r;
    if (fabs(M[p][i]) < 1e-6) return false;
    if (p != i) for (uint8_t c = 0; c < 4; c++) { float t = M[i][c]; M[i][c] = M[p][c]; M[p][c] = t; }
    for (uint8_t r = 0; r < 3; r++) if (r != i) {
      float f = M[r][i] / M[i][i];
      for (uint8_t c = i; c < 4; c++) M[r][c] -= f * M[i][c];
    }
  }
  a = M[0][3] / M[0][0] * 127.0;   // 기준이 ×127 이므로 되돌림
  b = M[1][3] / M[1][1] * 127.0;
  return true;
}
float accStd(const Acc &A) {
  float m = (float)A.sx / A.n;
  float v = (float)A.sxx / A.n - m * m;
  return v > 0 ? sqrt(v * A.n / (A.n - 1)) : 0;
}

// =====================================================================
//  측정 1회
//  반환: Z [Ω] (실패 시 NAN). aux: 부가 정보
// =====================================================================
struct Rep { float z, aux1, aux2, aux3; const __FlashStringHelper *warn; };

Rep measureSine() {
  Rep R = {NAN, NAN, NAN, NAN, NULL};
  Acc D, Nn; accClear(D); accClear(Nn);
  sineStart();
  delay(60);                               // 필터·결합 커패시터 안정화
  uint16_t lfsr = 0xACE1;
  for (uint16_t i = 0; i < SINE_PAIRS; i++) {
    uint8_t k = phase256(); int x = analogRead(A1); accAdd(D, x, k);
    k = phase256();         x = analogRead(A0); accAdd(Nn, x, k);
    lfsr = (lfsr >> 1) ^ (-(lfsr & 1u) & 0xB400u);
    delayMicroseconds(lfsr & 15);          // 위상 고르게 흩기
  }
  sineStop();
  float ad, bd, an, bn;
  if (!accSolve(D, ad, bd) || !accSolve(Nn, an, bn)) { R.warn = F("위상 데이터 부족"); return R; }
  // 복소 진폭 Vd = ad + j·bd, Vn = an + j·bn  →  Z = R1 · Vn / (Vd − Vn)
  float dr = ad - an, di = bd - bn, den = dr * dr + di * di;
  float zr = S.r1 * (an * dr + bn * di) / den, zi = S.r1 * (bn * dr - an * di) / den;
  float magD = sqrt(ad * ad + bd * bd), magN = sqrt(an * an + bn * bn);
  float sd = accStd(D), sn = accStd(Nn);
  R.z = sqrt(zr * zr + zi * zi);
  R.aux1 = atan2(zi, zr) * 180.0 / PI;              // 위상 [도]
  R.aux2 = (sd > sn) ? S.r1 * sn / (sd - sn) : NAN; // 옛 방식(RMS) 값, 비교용
  R.aux3 = magD * 5.0 / 1023.0;                     // 구동 진폭 [V]
  if (magD < 60)              { R.warn = F("사인파 없음: 칩 방향·D3·전원 확인"); R.z = NAN; }
  else if (magN > 0.97 * magD) { R.warn = F("전극 열림: 사인 단자 E1·E4 집게 확인"); R.z = NAN; }
  else if (magN < 0.02 * magD) { R.warn = F("전극 합선 또는 E1 집게 빠짐"); R.z = NAN; }
  return R;
}

Rep measureSquare() {
  Rep R = {NAN, NAN, NAN, NAN, NULL};
  sineStop();
  digitalWrite(PIN_SQ_DRV, LOW); digitalWrite(PIN_SQ_RET, LOW);
  pinMode(PIN_SQ_DRV, OUTPUT); pinMode(PIN_SQ_RET, OUTPUT);
  unsigned long a9p = 0, a1p = 0, a9n = 0, a1n = 0;
  for (uint16_t c = 0; c < SQ_WARM + SQ_CYCLES; c++) {
    for (uint8_t half = 0; half < 2; half++) {
      // D9 = PB1, D8 = PB0 : 두 핀을 동시에 바꿈
      uint8_t pat = half ? _BV(0) : _BV(1);
      PORTB = (PORTB & ~(_BV(0) | _BV(1))) | pat;
      unsigned long t0 = micros();
      while (micros() - t0 < SQ_T_READ) {}
      int v9 = analogRead(A2);
      int v1 = analogRead(A3);
      if (c >= SQ_WARM) { if (half) { a9n += v9; a1n += v1; } else { a9p += v9; a1p += v1; } }
      while (micros() - t0 < SQ_HALF) {}
    }
  }
  pinMode(PIN_SQ_DRV, INPUT); pinMode(PIN_SQ_RET, INPUT);   // 끝나면 전극을 띄움 (직류 0)
  digitalWrite(PIN_SQ_DRV, LOW); digitalWrite(PIN_SQ_RET, LOW);
  float s9 = ((float)a9p - (float)a9n) / SQ_CYCLES;   // D9 쪽 진폭 (카운트)
  float s1 = ((float)a1p - (float)a1n) / SQ_CYCLES;   // 전극 쪽 진폭
  // D9·D8 대칭 가정: Z = RQ · (S1 + S9) / (S9 − S1)
  R.aux1 = s9 * 5.0 / 1023.0; R.aux2 = s1 * 5.0 / 1023.0;
  if (s9 < 300)                { R.warn = F("사각파 없음: D9·D8·A2 배선 확인"); return R; }
  if (s9 - s1 < 0.02 * s9)     { R.warn = F("전극 열림: 사각 단자 Q1·Q4 집게 확인"); return R; }
  if (s1 + s9 < 0.01 * s9)     { R.warn = F("전극 합선 또는 Q1 집게 빠짐"); return R; }
  R.z = S.rq * (s1 + s9) / (s9 - s1);
  return R;
}

// =====================================================================
//  DS18B20 (1-Wire, D2)
// =====================================================================
#ifndef HOST_TEST
// D2 = PD2. 직접 레지스터 조작으로 OneWire 라이브러리와 같은 타이밍 (Arduino 함수 지연 제거)
#define OW_LOW()   (DDRD |= _BV(2))      // PORTD2는 항상 0 → 출력으로 바꾸면 LOW로 끌어내림
#define OW_REL()   (DDRD &= ~_BV(2))     // 입력(외부 4.7 kΩ 풀업이 HIGH로 올림)
#define OW_READ()  ((PIND >> 2) & 1)
bool owReset() {
  PORTD &= ~_BV(2);
  noInterrupts(); OW_LOW(); interrupts();
  delayMicroseconds(480);
  noInterrupts(); OW_REL(); delayMicroseconds(70);
  bool present = !OW_READ(); interrupts();
  delayMicroseconds(410);
  return present;
}
void owWriteBit(uint8_t b) {
  noInterrupts(); OW_LOW();
  if (b) { delayMicroseconds(10); OW_REL(); interrupts(); delayMicroseconds(55); }
  else   { delayMicroseconds(65); OW_REL(); interrupts(); delayMicroseconds(5); }
}
uint8_t owReadBit() {
  noInterrupts(); OW_LOW(); delayMicroseconds(3);
  OW_REL(); delayMicroseconds(10); uint8_t b = OW_READ(); interrupts();
  delayMicroseconds(53);
  return b;
}
void owWrite(uint8_t v) { for (uint8_t i = 0; i < 8; i++) owWriteBit((v >> i) & 1); }
uint8_t owRead() { uint8_t v = 0; for (uint8_t i = 0; i < 8; i++) v |= owReadBit() << i; return v; }
#else
bool owReset(); void owWrite(uint8_t v); uint8_t owRead();
#endif
uint8_t crc8(const uint8_t *p, uint8_t n) {
  uint8_t crc = 0;
  while (n--) { uint8_t in = *p++; for (uint8_t i = 0; i < 8; i++) { uint8_t mix = (crc ^ in) & 1; crc >>= 1; if (mix) crc ^= 0x8C; in >>= 1; } }
  return crc;
}
float readTempC() {
  sineStop();
  if (!owReset()) return NAN;
  owWrite(0xCC); owWrite(0x44);
  delay(800);
  if (!owReset()) return NAN;
  owWrite(0xCC); owWrite(0xBE);
  uint8_t sp[9]; for (uint8_t i = 0; i < 9; i++) sp[i] = owRead();
  if (crc8(sp, 8) != sp[8]) return NAN;
  int16_t raw = (int16_t)((sp[1] << 8) | sp[0]);
  float t = raw / 16.0;
  if (t == 85.0 || t < -20 || t > 80) return NAN;   // 85 °C = 변환 안 된 초기값
  return t;
}

// =====================================================================
//  I2C LCD (PCF8574 백팩, P0=RS P1=RW P2=EN P3=백라이트 P4..7=D4..7)
// =====================================================================
void lcdRaw(uint8_t v) { Wire.beginTransmission(lcdAddr); Wire.write(v | 0x08); Wire.endTransmission(); }
void lcdNib(uint8_t v) { lcdRaw(v | 0x04); delayMicroseconds(1); lcdRaw(v & ~0x04); delayMicroseconds(50); }
void lcdByte(uint8_t v, uint8_t rs) { lcdNib((v & 0xF0) | rs); lcdNib(((v << 4) & 0xF0) | rs); }
void lcdCmd(uint8_t c) { if (!lcdOK) return; lcdByte(c, 0); if (c < 4) delay(2); }
void lcdInit() {
  const uint8_t cand[] = {0x27, 0x3F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E};
  for (uint8_t i = 0; i < sizeof(cand); i++) {
    Wire.beginTransmission(cand[i]);
    if (Wire.endTransmission() == 0) { lcdAddr = cand[i]; lcdOK = true; break; }
  }
  if (!lcdOK) return;
  delay(50);
  lcdNib(0x30); delay(5); lcdNib(0x30); delayMicroseconds(150); lcdNib(0x30); lcdNib(0x20);
  lcdCmd(0x28); lcdCmd(0x0C); lcdCmd(0x06); lcdCmd(0x01);
}
void lcdLine(uint8_t row, const char *s) {
  if (!lcdOK) return;
  lcdCmd(0x80 | (row ? 0x40 : 0));
  for (uint8_t i = 0; i < 16; i++) lcdByte(*s ? *s++ : ' ', 1);
}

// =====================================================================
//  설정 저장
// =====================================================================
void defaults() {
  S.magic = MAGIC; S.alpha = 0.020; S.r1 = 330.0; S.rq = 330.0; S.sig = 0;
  for (uint8_t m = 0; m < 2; m++) { S.refMean[m] = NAN; S.refSD[m] = NAN; S.refN[m] = 0; }
}
void save() { EEPROM.put(0, S); }
void load() { EEPROM.get(0, S); if (S.magic != MAGIC) { defaults(); save(); } }

// =====================================================================
//  출력 도우미
// =====================================================================
void pf(float v, uint8_t d) { if (isnan(v)) Serial.print(F("nan")); else Serial.print(v, d); }
void head(const __FlashStringHelper *tag) { Serial.print(tag); Serial.print(','); Serial.print(millis()); Serial.print(','); Serial.print(label); Serial.print(','); }
float tMin() { return waterMs < 0 ? NAN : (millis() - (unsigned long)waterMs) / 60000.0; }
float corr20(float z) { return isnan(lastT) ? NAN : z * (1.0 + S.alpha * (lastT - 20.0)); }

float median3(float a, float b, float c) {
  if (a > b) { float t = a; a = b; b = t; }
  if (b > c) { float t = b; b = c; c = t; }
  if (a > b) { float t = a; a = b; b = t; }
  return b;
}

// 측정 세트 1회 = REPS번 반복 → 중앙값. 성공 시 Z(측정 온도) 반환
float measureSet(uint8_t m, bool quiet) {
  float z[REPS]; uint8_t ok = 0;
  for (uint8_t r = 0; r < REPS; r++) {
    Rep R = m ? measureSquare() : measureSine();
    if (!quiet) {
      head(F("REP")); Serial.print(m ? F("SQ") : F("SINE")); Serial.print(','); Serial.print(r + 1); Serial.print(',');
      pf(R.z, 2); Serial.print(','); pf(R.aux1, 3); Serial.print(','); pf(R.aux2, 3); Serial.print(','); pf(R.aux3, 3); Serial.println();
    }
    if (R.warn) { head(F("WARN")); Serial.println(R.warn); return NAN; }
    z[ok++] = R.z;
    delay(100);
  }
  return median3(z[0], z[1], z[2]);
}

void showLCD(uint8_t m, float z, float z20, float zs, bool judged) {
  char l1[17], l2[17], a[8], b[8];
  dtostrf(z, 6, 1, a); dtostrf(isnan(lastT) ? 0 : lastT, 4, 1, b);
  snprintf(l1, 17, "%s Z%s T%s", m ? "SQ" : "SI", a, isnan(lastT) ? "--" : b);
  if (isnan(z20)) snprintf(l2, 17, "Z20 ? (t cmd)");
  else {
    dtostrf(z20, 6, 1, a);
    if (judged) { dtostrf(zs, 4, 1, b); snprintf(l2, 17, "%s %s %ss", a, fabs(zs) >= 3 ? "ABN" : "OK ", b); }
    else snprintf(l2, 17, "Z20 %s noREF", a);
  }
  lcdLine(0, l1); lcdLine(1, l2);
}

void doMeasure(uint8_t m) {
  mode = m;
  lcdLine(0, m ? "Square measuring" : "Sine measuring"); lcdLine(1, "");
  float z = measureSet(m, false);
  if (isnan(z)) { lcdLine(0, "ERROR - see PC"); lcdLine(1, m ? "check Q1/Q4" : "check E1/E4"); return; }
  float z20 = corr20(z);
  float zs = NAN; bool judged = false;
  if (S.refN[m] > 0 && !isnan(z20)) {
    float sg = S.refSD[m]; if (S.sig > sg) sg = S.sig;
    if (sg > 0) { zs = (z20 - S.refMean[m]) / sg; judged = true; }
  }
  if (!isnan(lastT) && millis() - lastTms > 300000UL) { head(F("WARN")); Serial.println(F("온도 측정이 5분 넘게 지났음: t 명령으로 다시 재기")); }
  head(F("MEAS")); Serial.print(m ? F("SQ") : F("SINE")); Serial.print(',');
  pf(tMin(), 2); Serial.print(','); pf(z, 2); Serial.print(','); pf(lastT, 2); Serial.print(',');
  pf(z20, 2); Serial.print(','); pf(zs, 2); Serial.print(',');
  Serial.println(judged ? (fabs(zs) >= 3 ? F("ABNORMAL") : F("NORMAL")) : F("NOREF"));
  showLCD(m, z, z20, zs, judged);
}

void doReference(uint8_t m) {
  mode = m;
  if (isnan(lastT)) { head(F("WARN")); Serial.println(F("기준 저장 전에 t 로 온도부터 재기")); return; }
  lcdLine(0, "Saving REF..."); lcdLine(1, m ? "square x5" : "sine x5");
  float v[REF_N]; float sum = 0;
  for (uint8_t i = 0; i < REF_N; i++) {
    float z = measureSet(m, true);
    if (isnan(z)) { lcdLine(0, "REF failed"); return; }
    v[i] = corr20(z); sum += v[i];
    head(F("REFREP")); Serial.print(m ? F("SQ") : F("SINE")); Serial.print(','); Serial.print(i + 1); Serial.print(','); pf(v[i], 2); Serial.println();
  }
  float mean = sum / REF_N, ss = 0;
  for (uint8_t i = 0; i < REF_N; i++) ss += (v[i] - mean) * (v[i] - mean);
  S.refMean[m] = mean; S.refSD[m] = sqrt(ss / (REF_N - 1)); S.refN[m] = REF_N; save();
  head(F("REF")); Serial.print(m ? F("SQ") : F("SINE")); Serial.print(','); pf(mean, 2); Serial.print(','); pf(S.refSD[m], 3); Serial.println();
  char l[17], a[8], b[8]; dtostrf(mean, 6, 1, a); dtostrf(S.refSD[m], 4, 2, b);
  snprintf(l, 17, "REF%s %s", m ? "Q" : "S", a); lcdLine(0, l);
  snprintf(l, 17, "sd %s saved", b); lcdLine(1, l);
}

void doTemp() {
  lcdLine(0, "Reading temp..."); lcdLine(1, "");
  float t = readTempC();
  head(F("TEMP")); pf(t, 2); Serial.print(','); pf(tMin(), 2); Serial.println();
  if (isnan(t)) { head(F("WARN")); Serial.println(F("온도센서 응답 없음: D2·4.7k·센서 선 확인")); lcdLine(0, "Temp sensor ERR"); return; }
  lastT = t; lastTms = millis();
  char l[17], a[8]; dtostrf(t, 5, 2, a); snprintf(l, 17, "T = %s C", a); lcdLine(0, l);
}

void info() {
  Serial.print(F("# 설정: alpha=")); pf(S.alpha, 4); Serial.print(F(" r1=")); pf(S.r1, 2); Serial.print(F(" rq=")); pf(S.rq, 2);
  Serial.print(F(" sig=")); pf(S.sig, 3); Serial.print(F(" label=")); Serial.println(label);
  for (uint8_t m = 0; m < 2; m++) {
    Serial.print(m ? F("# 기준(사각) ") : F("# 기준(사인) "));
    if (S.refN[m]) { pf(S.refMean[m], 2); Serial.print(F(" ± ")); pf(S.refSD[m], 3); Serial.println(F(" Ω (20 °C 환산)")); }
    else Serial.println(F("없음"));
  }
  Serial.print(F("# LCD ")); if (lcdOK) { Serial.print(F("0x")); Serial.println(lcdAddr, HEX); } else Serial.println(F("없음"));
}

void help() {
  Serial.println(F("# ---- 명령 (입력 후 Enter) ----"));
  Serial.println(F("# s          사인파 측정 (집게: E1·E4)"));
  Serial.println(F("# q          사각파 측정 (집게: Q1·Q4)"));
  Serial.println(F("# t          온도 측정 (센서를 페이스트에 넣은 상태에서)"));
  Serial.println(F("# w          물 넣은 순간 표시 (경과 시간 기록 시작)"));
  Serial.println(F("# l 이름     시료 이름 (예: l W050-B1)"));
  Serial.println(F("# ref s      사인 기준 저장 (5번 측정)   ref q  사각 기준 저장"));
  Serial.println(F("# sig 4.0    판정 σ[Ω] 직접 지정 (분석에서 구한 σ_배합)"));
  Serial.println(F("# alpha 0.02 온도계수   r1 329.5 / rq 330.2  기준저항 실측값"));
  Serial.println(F("# info       설정 보기   reset  설정 초기화"));
  Serial.println(F("# 버튼: 짧게 = 측정(마지막 모드), 1.5초 이상 = 기준 저장"));
  Serial.println(F("#COLS MEAS,ms,label,mode,t_min,Z,T_C,Z20,zscore,judge"));
  Serial.println(F("#COLS REP,ms,label,mode,rep,Z,aux1,aux2,aux3  (SINE: 위상deg,Z_rms,Vd_amp / SQ: S9_V,S1_V,-)"));
}

void handle(char *s) {
  while (*s == ' ') s++;
  char *arg = strchr(s, ' '); if (arg) { *arg++ = 0; while (*arg == ' ') arg++; }
  if (!strcmp(s, "s")) doMeasure(0);
  else if (!strcmp(s, "q")) doMeasure(1);
  else if (!strcmp(s, "t")) doTemp();
  else if (!strcmp(s, "w")) { waterMs = millis(); head(F("WATER")); Serial.println(F("0")); lcdLine(0, "Water t=0 set"); }
  else if (!strcmp(s, "l") && arg) { strncpy(label, arg, 16); label[16] = 0; for (char *p = label; *p; p++) if (*p == ',') *p = '_'; Serial.print(F("# label=")); Serial.println(label); lcdLine(1, label); }
  else if (!strcmp(s, "ref") && arg && (*arg == 's' || *arg == 'q')) doReference(*arg == 'q');
  else if (!strcmp(s, "sig") && arg) { S.sig = atof(arg); save(); info(); }
  else if (!strcmp(s, "alpha") && arg) { S.alpha = atof(arg); save(); info(); }
  else if (!strcmp(s, "r1") && arg) { S.r1 = atof(arg); save(); info(); }
  else if (!strcmp(s, "rq") && arg) { S.rq = atof(arg); save(); info(); }
  else if (!strcmp(s, "info")) info();
  else if (!strcmp(s, "reset")) { defaults(); save(); info(); }
  else if (!strcmp(s, "h") || !strcmp(s, "help")) help();
  else if (*s) { Serial.print(F("# 모르는 명령: ")); Serial.println(s); }
}

// =====================================================================
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN, INPUT_PULLUP);
  pinMode(PIN_SQ_DRV, INPUT); pinMode(PIN_SQ_RET, INPUT);
  for (uint8_t i = 0; i < N_TAB; i++) {
    float a = 2.0 * PI * i / N_TAB;
    sineTab[i] = (uint8_t)(MID + AMP * sin(a) + 0.5);
  }
  pinMode(PIN_PWM, OUTPUT);
  TCCR2A = _BV(COM2B1) | _BV(WGM21) | _BV(WGM20);   // Fast PWM, OC2B(D3)
  TCCR2B = _BV(CS20);                               // 분주 1 → 62.5 kHz
  sineStop();
  load();
  Wire.begin();
  lcdInit();
  lcdLine(0, "2jo W/C meter"); lcdLine(1, "h = help (PC)");
  Serial.println(F("# 2조 W/C 측정기 Rev5 시작"));
  help(); info();
}

char buf[40]; uint8_t blen = 0;
unsigned long btnDown = 0; bool btnWas = false;

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { if (blen) { buf[blen] = 0; handle(buf); blen = 0; } }
    else if (blen < sizeof(buf) - 1) buf[blen++] = c;
  }
  bool down = (digitalRead(PIN_BTN) == LOW);
  if (down && !btnWas) btnDown = millis();
  if (!down && btnWas) {
    unsigned long held = millis() - btnDown;
    if (held >= 1500) doReference(mode);
    else if (held >= 40) doMeasure(mode);
  }
  btnWas = down;
}
