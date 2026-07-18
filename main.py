import os
import time
import csv
from datetime import datetime
import psutil

LOG_FILE = "dram_loss_by_resistance.csv"
SAMPLING_INTERVAL = 1.0  # 측정 간격 (1초)

# 고정 하드웨어 물리 상수
CAPACITANCE = 20e-15            # 축전기 용량 (20 fF)
VOLTAGE = 1.1                   # 동작 전압 (1.1 V)
SWITCHING_TIME = 0.5e-9         # 스위칭 제한 시간 (0.5 ns - 클럭 고정)

# [비교 변수] 미세화에 따라 변화하는 셀당 등가 저항군
RESISTANCE_LOW = 10
RESISTANCE_HIGH = RESISTANCE_LOW * 100

# 시스템의 총 DRAM 축전기(비트) 수 계산
TOTAL_RAM_BYTES = psutil.virtual_memory().total
TOTAL_CAPACITORS = TOTAL_RAM_BYTES * 8

# ==============================================================================
# 1. 물리학 공식을 이용한 핵심 계산 함수
# ==============================================================================
def calculate_joule_loss_per_switch(resistance):
    """
    [물리학2 유도 공식 적용]
    이상적 축전기 상수(1/2*C*V^2)를 배제하고, 제한 시간(t) 동안 저항(R)을 통과할 때 
    발생하는 순수 손실만 계산합니다.
    공식: E_loss = (Q^2 * R) / t = (C^2 * V^2 * R) / t
    """
    charge_q = CAPACITANCE * VOLTAGE
    joule_loss = (charge_q ** 2 * resistance) / SWITCHING_TIME
    return joule_loss

def estimate_activity(cpu_usage):
    """CPU 사용량에 비례하는 초당 스위칭 횟수를 추정합니다."""
    cpu_ratio = cpu_usage
    dynamic_activity = cpu_ratio
    return int(TOTAL_CAPACITORS * dynamic_activity)

def initialize_log():
    """저항별 순수 손실만 기록할 수 있도록 CSV 헤더를 생성합니다."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "CPU_Usage(%)", "Active_Switches", 
                "Joule_Loss_low(J)", "Joule_Loss_high(J)"
            ])

# ==============================================================================
# 2. 메인 실행 루프
# ==============================================================================
def main():
    # 각 저항별 1회 스위칭 시 발생하는 순수 손실 미리 계산
    loss_low = calculate_joule_loss_per_switch(RESISTANCE_LOW)
    loss_high = calculate_joule_loss_per_switch(RESISTANCE_HIGH)
    
    initialize_log()
    
    print("=" * 75)
    print(" [물리학2 수행평가] DRAM 미세화(저항 증가)에 따른 순수 줄열(Joule Heat) 손실 비교")
    print(f" * 고정 물리량: C = {CAPACITANCE*1e15:.1f} fF, V = {VOLTAGE} V, t = {SWITCHING_TIME*1e9} ns")
    print(f" * 분석 대상: 저항(R) 변화에 정비례하여 달라지는 동적 열손실")
    print("=" * 75)
    print(" ▶ 실시간 비교 측정 중... (정지하려면 Ctrl + C)\n")
    
    # 저항별 누적 줄열 손실 변수

    cum_low = 0.0
    cum_high = 0.0

    try:
        while True:

            cpu_usage = psutil.cpu_percent()
            active_switches = estimate_activity(cpu_usage)
            
            # 1초 동안 각 저항 조건에서 발생한 순수 줄열 소모량 누적
            cum_low = loss_low * active_switches
            cum_high = loss_high * active_switches
            
            now = datetime.now().strftime("%H:%M:%S")
            
            # 화면 출력 (오직 저항에 의해 가변되는 손실만 정밀하게 비교)
            print(f"[{now}] CPU:{cpu_usage:5.1f}% | "
                  f"옛날:{cum_low:6.7f} J | "
                  f"현대:{cum_high:6.7f} J")
            
            # CSV 파일에 저장
            with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                   cpu_usage, active_switches, 
                    round(cum_low, 8), round(cum_high, 8)
                ])
                
            time.sleep(SAMPLING_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 75)
        print(f" 시뮬레이션이 종료되었습니다. 결과가 '{LOG_FILE}'에 저장되었습니다.")
        print("=" * 75)

if __name__ == "__main__":
    main()