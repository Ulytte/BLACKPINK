// 사인파 구동 접촉식 측정 - 시험용 스케치
// 구성 4S·2S용. Arduino Uno, D3 = PWM(Timer2), LM358 A = 2차 LPF 버퍼, LM358 B = 가상접지(약 1.81 V)
// A1 = 기준저항 위쪽(구동 전압), A0 = 기준저항과 전극 A 사이 노드
// 출력 주파수 = 62500 Hz / 64 = 약 977 Hz

#include <math.h>

const uint8_t N = 64;          // 사인 테이블 점 수 (2의 거듭제곱)
const uint8_t MID = 89;        // 중심 듀티 (89/255 x 5 V = 약 1.75 V)
const uint8_t AMP = 64;        // 진폭 듀티 (64/255 x 5 V = 약 1.25 V peak)
const float   R_REF = 330.0;   // 기준저항 R1 [옴] (구성 4S·2S)
const uint16_t SAMPLES = 2000; // RMS 계산용 샘플 수 (약 0.22초)

uint8_t sineTab[N];
volatile uint8_t idx = 0;

ISR(TIMER2_OVF_vect) {         // PWM 한 주기(16 us)마다 다음 사인값으로
  OCR2B = sineTab[idx];
  idx = (idx + 1) & (N - 1);
}

void sineStart() {
  idx = 0;
  TIMSK2 = _BV(TOIE2);
}

void sineStop() {              // 정지 시 중심값으로 고정 -> 가상접지와 같은 전압, 전류 0
  TIMSK2 = 0;
  OCR2B = MID;
}

// 교류 성분 RMS = 표준편차 (Welford 방식)
float acRms(uint8_t pin, uint16_t n) {
  float mean = 0, m2 = 0;
  for (uint16_t k = 1; k <= n; k++) {
    float x = analogRead(pin) * (5.0 / 1023.0);
    float d = x - mean;
    mean += d / k;
    m2 += d * (x - mean);
  }
  return sqrt(m2 / (n - 1));
}

void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < N; i++) {
    sineTab[i] = (uint8_t)(MID + AMP * sin(2.0 * PI * i / N) + 0.5);
  }
  pinMode(3, OUTPUT);
  TCCR2A = _BV(COM2B1) | _BV(WGM21) | _BV(WGM20);  // Fast PWM, OC2B(D3) 출력
  TCCR2B = _BV(CS20);                              // 분주 1 -> 62.5 kHz PWM
  sineStop();
  Serial.println("Vdrive_rms[V], Vnode_rms[V], Z[ohm]");
}

void loop() {
  sineStart();
  delay(50);                         // 필터·커패시터 안정화
  float vd = acRms(A1, SAMPLES);     // 기준저항 위쪽 교류 진폭
  float vn = acRms(A0, SAMPLES);     // 전극 쪽 노드 교류 진폭
  sineStop();

  // 근사식: 페이스트가 거의 저항성일 때 |Z| = R_ref x Vn / (Vd - Vn)
  float z = (vd > vn) ? R_REF * vn / (vd - vn) : -1;

  Serial.print(vd, 4); Serial.print(", ");
  Serial.print(vn, 4); Serial.print(", ");
  Serial.println(z, 1);

  delay(1000);
}
