import socket
import struct
import time

def create_stun_bind_request():
    """创建STUN绑定请求消息"""
    # STUN消息类型: 0x0001 (Binding Request)
    # STUN魔术字: 0x2112A442
    # 消息长度: 0
    # 事务ID: 12字节随机数
    header = struct.pack('>HHI12s', 
        0x0001,  # 消息类型
        0x0000,  # 消息长度
        0x2112A442,  # 魔术字
        b'0123456789ab'  # 事务ID
    )
    return header

def test_stun_server(stun_host="stun.l.google.com", stun_port=19302):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    
    try:
        print(f"正在测试 STUN 服务器: {stun_host}:{stun_port}")
        request = create_stun_bind_request()
        start_time = time.time()
        
        # 发送STUN绑定请求
        sock.sendto(request, (stun_host, stun_port))
        
        # 接收响应
        data, addr = sock.recvfrom(2048)
        elapsed = time.time() - start_time
        
        # 检查响应的魔术字
        if len(data) >= 20:
            magic_cookie = struct.unpack('>I', data[4:8])[0]
            if magic_cookie == 0x2112A442:
                print(f"STUN服务器响应来自: {addr}")
                print(f"响应时间: {elapsed:.3f}秒")
                return True
            
        print("收到无效响应")
        return False
        
    except socket.timeout:
        print(f"连接超时")
        return False
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    # 测试多个常用STUN服务器
    servers = [
        ("stun.l.google.com", 19302),
        ("stun.miwifi.com", 3478),
        ("stun.stunprotocol.org", 3478)
    ]
    
    for host, port in servers:
        print("\n" + "="*50)
        test_stun_server(host, port)