import asyncio
import logging
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer

# logging.basicConfig(level=logging.DEBUG)

async def test_stun():
    config = RTCConfiguration([
        RTCIceServer(
            urls=['stun:stun.l.google.com:19302']
        )
    ])
    
    pc = RTCPeerConnection(configuration=config)
    channel = pc.createDataChannel("test")
    gathering_complete = asyncio.Event()  # 添加事件标志
    
    @channel.on("open")
    def on_open():
        print("数据通道已打开")
    
    @pc.on("iceconnectionstatechange")
    def on_iceconnectionstatechange():
        print(f"ICE连接状态: {pc.iceConnectionState}")
    
    @pc.on("icecandidate")
    def on_icecandidate(candidate):
        if candidate:
            print(f"ICE候选者: {candidate.candidate}")
            print(f"ICE候选者类型: {candidate.type}")
            print(f"ICE协议: {candidate.protocol}")
        else:
            print("ICE候选者收集完成")
            gathering_complete.set()  # 设置完成标志

    try:
        # 创建offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        print("等待ICE收集完成...")
        await gathering_complete.wait()  # 等待收集完成
        
        print("\n本地描述:", pc.localDescription.sdp)
        
        # 给予足够时间观察状态
        await asyncio.sleep(5)
    
    finally:
        print("清理连接...")
        await pc.close()

if __name__ == "__main__":
    asyncio.run(test_stun())