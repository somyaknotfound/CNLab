#!/usr/bin/env python3
"""
Automated smoke test for all 10 assignment programs.

For each question it starts the server in a background process, runs the client
against it, checks the output contains the expected text, then shuts the server
down. Useful as a sanity check before the lab, and to confirm nothing broke
after you edit a file.

Run:  python run_all_tests.py
      python run_all_tests.py 3 7      (only questions 3 and 7)
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

# (number, folder, client args, stdin text, list of substrings expected in output)
TESTS = [
    (1, 'q01_uppercase',      ['hello world'],            None,          ['HELLO WORLD']),
    (2, 'q02_arithmetic',     ['12', '+', '5'],           None,          ['17']),
    (2, 'q02_arithmetic',     ['7', '/', '0'],            None,          ['division by zero']),
    (3, 'q03_prime_udp',      ['97'],                     None,          ['97 is a PRIME']),
    (3, 'q03_prime_udp',      ['100'],                    None,          ['NOT a prime']),
    (4, 'q04_echo',           [],                         'hi\nexit\n',  ['Echo : hi', 'Bye']),
    (5, 'q05_file_stats',     ['sample.txt'],             None,          ['Lines  : 4', 'Words  : 18']),
    (5, 'q05_file_stats',     ['nope.txt'],               None,          ['not found']),
    (6, 'q06_udp_clientinfo', ['hello udp'],              None,          ['Received 9 bytes']),
    (7, 'q07_palindrome',     ['racecar'],                None,          ['IS a palindrome']),
    (7, 'q07_palindrome',     ['hello'],                  None,          ['is NOT a palindrome']),
    (8, 'q08_file_transfer',  ['send/demo.txt'],          None,          ['OK:', 'demo.txt']),
    (9, 'q09_string_analysis',['Hello World'],            None,          ['Vowels     : 3',
                                                                         'Consonants : 7',
                                                                         'Words      : 2']),
    (10, 'q10_sort_array',    ['3', '1', '4', '1', '5'],  None,          ['[1, 1, 3, 4, 5]']),
]


def run_case(number, folder, args, stdin_text, expected):
    cwd = os.path.join(HERE, folder)
    label = f"Q{number:<2} {folder:<22} {' '.join(args) or '(interactive)':<24}"

    server = subprocess.Popen(
        [PY, 'server.py'], cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(0.6)                     # let the server bind before connecting

    try:
        result = subprocess.run(
            [PY, 'client.py'] + args, cwd=cwd,
            input=stdin_text, capture_output=True, text=True, timeout=15)
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
        print('      client output:')
        for line in output.strip().splitlines():
            print('        ', line)
        return False

    print(f"PASS  {label}")
    return True


def main():
    wanted = {int(a) for a in sys.argv[1:]} if len(sys.argv) > 1 else None
    cases = [t for t in TESTS if wanted is None or t[0] in wanted]

    print(f"Running {len(cases)} test case(s)\n" + "=" * 72)
    passed = sum(run_case(*c) for c in cases)
    print("=" * 72)
    print(f"{passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == '__main__':
    sys.exit(main())
