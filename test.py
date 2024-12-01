from socket import *
import time

def test_stun_server(stun_host, stun_port):
    try:
        s = socket(AF_INET, SOCK_DGRAM)
        s.settimeout(2)
        start_time = time.time()
        s.sendto(b"", (stun_host, stun_port))
        try:
            data, addr = s.recvfrom(1024)
            end_time = time.time()
            print(f"STUN服务器 {stun_host}:{stun_port} 可用")
            print(f"响应时间: {(end_time - start_time)*1000:.2f}ms")
            return True
        except timeout:
            print(f"STUN服务器 {stun_host}:{stun_port} 超时无响应")
            return False
    except Exception as e:
        print(f"测试 STUN服务器 {stun_host}:{stun_port} 失败: {e}")
        return False
    finally:
        s.close()

if __name__ == "__main__":
    # with open("valid_hosts.txt", "r") as f:
    #     stun_servers = f.read().splitlines()
    stun_servers = ["relay.webwormhole.io:3478"]
    for server in stun_servers:
        host, port = server.split(":")
        test_stun_server(host, int(port))