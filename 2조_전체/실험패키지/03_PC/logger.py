#!/usr/bin/env python3
"""
2조 측정 기록기 — Arduino(wc_meter.ino)와 대화하면서 모든 줄을 CSV로 저장한다.

사용법
  python logger.py                 # 포트 자동 선택 후 대화형 (명령을 치면 Arduino로 보냄)
  python logger.py --port COM5     # 포트 직접 지정 (Windows: COM3 등, Mac: /dev/cu.usbmodem…)
  python logger.py --from-file 시리얼모니터_복사본.txt   # Arduino IDE 시리얼 모니터 내용을 붙여 넣은 파일을 CSV로 변환

저장 위치: data/ 폴더
  raw_날짜시각.txt  : 받은 줄 전부 (원본, 절대 지우지 말 것)
  meas.csv / rep.csv / temp.csv / ref.csv / warn.csv : 종류별로 이어 붙임 (여러 날 실험이 한 파일에 쌓임)

필요: pip install pyserial  (변환 모드는 필요 없음)
종료: quit 입력 또는 Ctrl+C
"""
import argparse, csv, datetime, os, pathlib, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
COLS = {
    "MEAS": ["pc_time", "ms", "label", "mode", "t_min", "Z", "T_C", "Z20", "zscore", "judge"],
    "REP": ["pc_time", "ms", "label", "mode", "rep", "Z", "aux1", "aux2", "aux3"],
    "TEMP": ["pc_time", "ms", "label", "T_C", "t_min"],
    "REF": ["pc_time", "ms", "label", "mode", "ref_mean", "ref_sd"],
    "WARN": ["pc_time", "ms", "label", "message"],
    "WATER": ["pc_time", "ms", "label", "zero"],
}


class Store:
    def __init__(self, tag):
        DATA.mkdir(exist_ok=True)
        self.raw = open(DATA / f"raw_{tag}.txt", "a", encoding="utf-8")

    def line(self, s, pc_time=None):
        s = s.rstrip("\r\n")
        if not s:
            return
        now = pc_time or datetime.datetime.now().isoformat(timespec="seconds")
        self.raw.write(f"{now}\t{s}\n"); self.raw.flush()
        kind = s.split(",", 1)[0]
        if kind in COLS:
            parts = s.split(",")
            row = [now] + parts[1:]
            want = len(COLS[kind])
            if kind == "WARN" and len(row) > want:          # 메시지에 쉼표가 있으면 합침
                row = row[:want - 1] + [",".join(row[want - 1:])]
            if len(row) != want:
                print(f"  (형식이 예상과 다름, raw에만 저장: {s})"); return
            path = DATA / f"{kind.lower()}.csv"
            new = not path.exists()
            with open(path, "a", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                if new: w.writerow(COLS[kind])
                w.writerow(row)


def pick_port():
    from serial.tools import list_ports
    ports = list(list_ports.comports())
    if not ports:
        sys.exit("연결된 시리얼 포트가 없어. USB 케이블과 Arduino IDE에서 포트가 보이는지 확인해.")
    good = [p for p in ports if any(k in (p.description or "") + (p.manufacturer or "")
                                    for k in ("Arduino", "CH340", "USB-SERIAL", "USB Serial", "wch", "FTDI"))]
    if len(good) == 1:
        return good[0].device
    print("포트를 골라:")
    for i, p in enumerate(ports):
        print(f"  {i}: {p.device}  {p.description}")
    return ports[int(input("번호> "))].device


def live(port, baud):
    import serial
    tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st = Store(tag)
    ser = serial.Serial(port, baud, timeout=0.2)
    print(f"[{port}] 연결됨. Arduino가 재시작되는 동안 2초 기다려. 'h' = 명령 목록, 'quit' = 끝내기")
    stop = threading.Event()

    def reader():
        buf = b""
        while not stop.is_set():
            buf += ser.read(256)
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                s = raw.decode("utf-8", "replace").rstrip("\r")
                print(s)
                st.line(s)

    th = threading.Thread(target=reader, daemon=True); th.start()
    time.sleep(2)
    try:
        while True:
            cmd = input()
            if cmd.strip() in ("quit", "exit"):
                break
            st.raw.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t>>> {cmd}\n")
            ser.write((cmd + "\n").encode())
    except (KeyboardInterrupt, EOFError):
        pass
    stop.set(); th.join(1); ser.close()
    print(f"저장됨: {DATA}")


def convert(path):
    tag = "import_" + pathlib.Path(path).stem
    st = Store(tag)
    n = 0
    for s in open(path, encoding="utf-8", errors="replace"):
        # Arduino IDE 시리얼 모니터의 '타임스탬프 보기'(예: 14:03:21.123 -> ) 형식도 처리
        if " -> " in s[:20]:
            s = s.split(" -> ", 1)[1]
        if "\t" in s and s.split("\t", 1)[0][:4].isdigit():
            pc, s = s.split("\t", 1)
            st.line(s, pc)
        else:
            st.line(s)
        n += 1
    print(f"{n}줄 변환 → {DATA}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--from-file")
    a = ap.parse_args()
    if a.from_file:
        convert(a.from_file)
    else:
        live(a.port or pick_port(), a.baud)
