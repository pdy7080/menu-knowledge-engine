#!/usr/bin/env python3
"""
SSH 터널을 포함한 Claude 번역 래퍼 스크립트

이 스크립트는:
1. SSH 터널을 백그라운드에서 연다 (localhost:5432 -> server:5432)
2. Claude 배치 번역을 실행한다
3. 완료 후 SSH 터널을 닫는다
"""

import subprocess
import time
import sys
from pathlib import Path

def main():
    ssh_key_path = Path.home() / ".ssh" / "menu_deploy"

    print("=" * 80)
    print("Claude Batch Translation with SSH Tunnel")
    print("=" * 80)

    # 1. SSH 터널 열기
    print("\n[*] Opening SSH tunnel...")
    tunnel_process = subprocess.Popen(
        [
            'ssh', '-i', str(ssh_key_path),
            '-L', '5432:localhost:5432',
            '-N',  # 명령 실행 없이 터널만
            '-o', 'ServerAliveInterval=60',  # Keep alive
            'chargeap@d11475.sgp1.stableserver.net'
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 터널이 설정될 때까지 대기
    print(f"[+] SSH tunnel opened (PID: {tunnel_process.pid})")
    print("[*] Waiting 5 seconds for tunnel to establish...")
    time.sleep(5)

    try:
        # 2. Claude 배치 번역 실행
        print("\n[*] Starting Claude batch translation...")
        print("-" * 80)

        result = subprocess.run(
            [sys.executable, "scripts/claude_batch_translation.py"],
            cwd=Path(__file__).parent.parent
        )

        if result.returncode == 0:
            print("\n" + "=" * 80)
            print("[+] Translation completed successfully!")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print(f"[-] Translation failed with exit code {result.returncode}")
            print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")

    finally:
        # 3. SSH 터널 닫기
        print("\n[*] Closing SSH tunnel...")
        tunnel_process.terminate()
        tunnel_process.wait()
        print("[+] SSH tunnel closed")

if __name__ == "__main__":
    main()
