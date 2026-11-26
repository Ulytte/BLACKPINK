// 구성 6 (비접촉 + AC 전하 증폭기) 사인파 구동 버전
// 변경점: D9 사각파 -> D9 고속 PWM(Timer1, 62.5 kHz) + LM358 B 2차 저역통과필터 -> 약 977 Hz 사인파
// 측정: A0(전하 증폭기 출력)의 교류 RMS. 값이 클수록 전극 사이 결합(정전용량)이 큼
// 가정: Arduino Uno, D2 = DS18B20 (온도는 측정 전후에만), I2C LCD는 이 시험 스케치에서 생략

#include <math.h>

const uint8_t N = 64;          // 사인 테이블 점 수
const uint8_t MID = 89;        // 중심 듀티 (약 1.75 V)
const uint8_t AMP = 64;        // 진폭 (약 1.25 V peak) -> LM358 출력 범위 0.5~3.0 V 안
const uint16_t SAMPLES = 2000; // RMS 샘플 수 (약 0.22초)
const uint8_t REPEAT = 3;      // 3회 측정 후 중앙값

uint8_t sineTab[N];
volatile uint8_t idx = 0;

ISR(TIMER1_OVF_vect) {         // 16 us마다 다음 사인값
  OCR1A = sineTab[idx];
  idx = (idx + 1) & (N - 1);
}

void sineStart() { idx = 0; TIMSK1 = _BV(TOIE1); }
void sineStop()  { TIMSK1 = 0; OCR1A = MID; }   // 정지 시 중심값 고정

float acRms(uint8_t pin, uint16_t n) {          // 교류 성분 RMS (표준편차)
  float mean = 0, m2 = 0;
  for (uint16_t k = 1; k <= n; k++) {
    float x = analogRead(pin) * (5.0 / 1023.0);
    float d = x - mean;
    mean += d / k;
    m2 += d * (x - mean);
  }
  return sqrt(m2 / (n - 1));
}

float median3(float a, float b, float c) {
  if (a > b) { float t = a; a = b; b = t; }
  if (b > c) { float t = b; b = c; c = t; }
  if (a > b) { float t = a; a = b; b = t; }
  return b;
}

void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < N; i++)
    sineTab[i] = (uint8_t)(MID + AMP * sin(2.0 * PI * i / N) + 0.5);
  pinMode(9, OUTPUT);
  TCCR1A = _BV(COM1A1) | _BV(WGM10);            // Fast PWM 8비트, OC1A(D9)
  TCCR1B = _BV(WGM12) | _BV(CS10);              // 분주 1 -> 62.5 kHz
  sineStop();
  Serial.println("A0_rms[mV] (median of 3)");
}

void loop() {
  float v[REPEAT];
  sineStart();
  delay(100);                                   // 필터·바이어스 안정화
  for (uint8_t r = 0; r < REPEAT; r++) v[r] = acRms(A0, SAMPLES);
  sineStop();

  Serial.println(median3(v[0], v[1], v[2]) * 1000.0, 2);
  delay(1000);
}
