import os
import socket
import subprocess
import sys

def get_pids_using_port(port):
    """获取占用指定端口的进程ID列表"""
    pids = []
    try:
        # 使用netstat命令获取占用端口的进程
        output = subprocess.check_output(['netstat', '-ano'], universal_newlines=True)
        lines = output.split('\n')
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                # 提取PID
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[4]
                    pids.append(pid)
    except Exception as e:
        print(f"获取进程信息失败: {e}")
    return pids

def kill_processes(pids):
    """终止指定的进程"""
    for pid in pids:
        try:
            print(f"终止进程 {pid}...")
            subprocess.run(['taskkill', '/PID', pid, '/F'], check=False)
        except Exception as e:
            print(f"终止进程 {pid}失败: {e}")

def main():
    port = 5000
    print(f"检查占用端口 {port} 的进程...")
    pids = get_pids_using_port(port)
    
    if pids:
        print(f"发现 {len(pids)} 个进程占用端口 {port}:")
        for pid in pids:
            print(f"- PID: {pid}")
        kill_processes(pids)
    else:
        print(f"没有进程占用端口 {port}")
    
    print("\n重新启动项目...")
    # 启动Flask应用
    subprocess.Popen([sys.executable, 'app.py'])
    print("项目已启动，请访问 http://localhost:5000")

if __name__ == "__main__":
    main()
