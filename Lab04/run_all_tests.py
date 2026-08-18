#!/usr/bin/env python3
"""
Smoke test for all 10 programs. Starts each server, runs its client, checks the
output, shuts the server down.

Run:  python run_all_tests.py
      python run_all_tests.py 4 7      (only questions 4 and 7)
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

# (q, folder, client args, stdin, expected substrings, extra clients to run first)
TESTS = [
    (1, 'q01_chat', ['asha'], 'hello everyone\nquit\n', ['Welcome asha']),
    (2, 'q02_factorial', ['5', '10'], None, ['5! = 120', '10! = 3628800']),
    (2, 'q02_factorial', ['-3'], None, ['undefined for negative']),
    (3, 'q03_binary_sha256', ['send/sample.bin'], None, ['OK:', 'verified']),
    (4, 'q04_reliable_udp', [], None, ['sent 2752 bytes in 3 chunk(s)', 'ACKed']),
    (5, 'q05_multi_service', ['CALC', '12 + 5'], None, ['17']),
    (5, 'q05_multi_service', ['STRING', 'hello'], None, ['upper=HELLO', 'reverse=olleh']),
    (5, 'q05_multi_service', ['TIME'], None, ['Server time']),
    (5, 'q05_multi_service', ['FILE', 'notes.txt'], None, ['FILE service']),
    (6, 'q06_student_db', ['INSERT|101|Asha|88'], None, ['Inserted 101']),
    (6, 'q06_student_db', ['SEARCH|101'], None, ['101 | Asha | 88']),
    (6, 'q06_student_db', ['DELETE|101'], None, ['Deleted 101']),
    (6, 'q06_student_db', ['SEARCH|999'], None, ['not found']),
    (7, 'q07_select_server', ['hello', 'socket'], None, ['HELLO', 'SOCKET']),
    (8, 'q08_quiz', ['Asha', '2', '3', '2', '3', '2'], None, ['Your score: 5/5']),
    (9, 'q09_remote_cmd', ['pwd'], None, ['q09_remote_cmd']),
    (9, 'q09_remote_cmd', ['rm', '-rf', '/'], None, ['is not allowed']),
    (9, 'q09_remote_cmd', ['ls;', 'cat'], None, ['not allowed']),
    (10, 'q10_file_server', ['asha', 'pass123', 'upload', 'upload_me.txt'], None,
         ['login successful', 'uploaded']),
    (10, 'q10_file_server', ['asha', 'badpass', 'list'], None, ['invalid username']),
    (10, 'q10_file_server', ['ravi', 'pass456', 'download', 'upload_me.txt'], None,
         ['saved downloads/upload_me.txt']),
]


def run_case(number, folder, args, stdin_text, expected):
    cwd = os.path.join(HERE, folder)
    label = f"Q{number:<2} {folder:<20} {' '.join(args)[:34] or '(default)':<34}"

    server = subprocess.Popen([PY, 'server.py'], cwd=cwd,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(0.7)

    try:
        result = subprocess.run([PY, 'client.py'] + args, cwd=cwd, input=stdin_text,
                                capture_output=True, text=True, timeout=40)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = '<<client timed out>>'
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

    missing = [e for e in expected if e not in output]
    if missing:
        print(f"FAIL  {label}  missing: {missing}")
        for line in output.strip().splitlines()[-12:]:
            print('        ', line)
        return False

    print(f"PASS  {label}")
    return True


def main():
    wanted = {int(a) for a in sys.argv[1:]} if len(sys.argv) > 1 else None
    cases = [t for t in TESTS if wanted is None or t[0] in wanted]

    print(f"Running {len(cases)} case(s)\n" + "=" * 78)
    passed = sum(run_case(*c) for c in cases)
    print("=" * 78)
    print(f"{passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == '__main__':
    sys.exit(main())
