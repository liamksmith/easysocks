import asyncio

async def tcp_client():
    """基础 TCP 客户端示例"""
    # 建立连接
    reader, writer = await asyncio.open_connection('cip.cc', 80)
    print(f"连接到 cip.cc:80")

    try:
        # 发送 HTTP 请求
        request = b'GET / HTTP/1.0\r\nHost: cip.cc\r\n\r\n'
        writer.write(request)
        await writer.drain()  # 确保数据发送完成

        # 读取响应
        response = b''
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                break
            response += chunk

        print(f"收到 {len(response)} 字节响应")
        print(response[:200].decode('utf-8', errors='ignore'))

    finally:
        # 关闭连接
        writer.close()
        await writer.wait_closed()
        print("连接已关闭")


asyncio.run(tcp_client())