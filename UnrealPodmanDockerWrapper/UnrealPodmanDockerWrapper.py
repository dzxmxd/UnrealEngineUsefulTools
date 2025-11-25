import sys
import subprocess
import shlex
import os

def main():
    # 获取传给 docker.exe 的所有参数
    args = sys.argv[1:]

    # 你可以在这里做参数修正，例如修复 UE 的 ulimit 写法
    # UE 会传：['--ulimit', '[{"Name":"nofile","Hard":100000,"Soft":100000}]']
    # Docker 支持，但 podman 不支持。这里我们简单丢弃 ulimit，避免报错。
    filtered_args = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a == "--ulimit":
            # 丢弃 --ulimit 以及其参数
            skip_next = True
            continue
        filtered_args.append(a)

    # podman 替代 docker
    cmd = ["podman"] + filtered_args

    # Windows 下防止奇怪的编码问题
    if os.name == "nt":
        cmd = ["podman.exe"] + filtered_args

    print("[docker-wrapper] Executing:", " ".join(shlex.quote(c) for c in cmd))

    # 调用 podman
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stdout, stderr = proc.communicate()

    # 转发输出
    if stdout:
        print(stdout, end="")
    if stderr:
        print(stderr, file=sys.stderr, end="")

    # 返回相同 exit code
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
