#!/usr/bin/env python3
"""统一测试入口:运行 tests/ 下全部 test_*.py。

用法:python3 tests/run_all.py
每个测试文件都是独立可运行的脚本,这里逐个以子进程执行并汇总结果。
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    files = sorted(f for f in glob.glob(os.path.join(HERE, "test_*.py")))
    total_pass = total_fail = 0
    failed_files = []
    for f in files:
        name = os.path.basename(f)
        print(f"\n===== {name} =====")
        proc = subprocess.run([sys.executable, f], capture_output=True, text=True)
        out = proc.stdout.strip()
        print(out)
        if proc.stderr.strip():
            print(proc.stderr.strip())
        total_pass += out.count("PASS ")
        fails = out.count("FAIL ") + out.count("ERROR ")
        total_fail += fails
        if proc.returncode != 0 or fails:
            failed_files.append(name)

    print("\n" + "=" * 40)
    print(f"总计:{total_pass} 通过,{total_fail} 失败")
    if failed_files:
        print("失败文件:" + ", ".join(failed_files))
    print("=" * 40)
    sys.exit(1 if failed_files else 0)


if __name__ == "__main__":
    main()
