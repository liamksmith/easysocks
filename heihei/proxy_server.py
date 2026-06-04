# 这是一个示例 Python 脚本。
import asyncio
import socket
import ssl
import struct
from pathlib import Path

from loguru import logger

CERT_DIR = Path(__file__).parent.parent / "certs"
CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE = CERT_DIR / "server.key"

async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # print("a client has connected")
    try:
        data = await reader.read(1)
        if len(data) < 1:
            raise Exception("no data")
        addr_type = data[0]
        if addr_type == 1:  # IP V4 address: X'01'
            addr_ip = await reader.read(4)
            addr = socket.inet_ntoa(addr_ip)
            logger.info("CONNECT - target addr is: " + addr)
        elif addr_type == 3:  # DOMAINNAME: X'03'
            addr_len = await reader.read(1)
            addr = await reader.read(addr_len[0])
            addr = addr.decode()
            logger.info("CONNECT - target addr is: " + addr)
        else:
            # not support
            logger.error("addr_type:{} not support".format(addr_type))
            raise Exception('addr_type not support')
        port = struct.unpack('>H', await reader.read(2))

        logger.info('connecting %s:%d' % (addr, port[0]))
        remote_reader, remote_writer = await asyncio.open_connection(addr, port[0])
        logger.info("connected:{}, {}".format(addr, port[0]))

        # tell the forward server that we are prepared to send/recv data.
        reply: bytes = b"\x00"
        writer.write(reply)
        await writer.drain()

        task_to_target = asyncio.create_task(_relay_to_target(reader, writer, remote_reader, remote_writer))
        task_from_target = asyncio.create_task(_relay_from_target(reader, writer, remote_reader, remote_writer))
        await asyncio.gather(task_to_target, task_from_target)
    except socket.error as r:
        logger.error(r)
    except Exception as e:
        logger.error(e)
    finally:
        writer.close()  # OSError: [WinError 64] 指定的网络名不再可用。
        await writer.wait_closed()
        # print("a client has disconnected")

async def _relay_to_target(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                           remote_reader: asyncio.StreamReader, remote_writer: asyncio.StreamWriter):
    # is_quit = False
    # while not is_quit:
    #     await asyncio.sleep(1)
    #     print("handle_tcp_out")
    done = False
    while not done:
        try:
            data = await reader.read(4096)
            # print(type(data))
            if len(data) == 0:
                print("_relay_to_target: 连接正常关闭")
                break
            # print("handle_tcp_out cc read:", len(data))
            remote_writer.write(data)
            await remote_writer.drain()
            # print("handle_tcp_out cc write:", len(data))
        except socket.error as e:
            logger.error(e)
            done = True
        except Exception as e:
            logger.error(e)
            done = True
    writer.close()
    remote_writer.close()
    await writer.wait_closed()
    await remote_writer.wait_closed()

async def _relay_from_target(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                             remote_reader: asyncio.StreamReader, remote_writer: asyncio.StreamWriter):
    # is_quit = False
    # while not is_quit:
    #     await asyncio.sleep(1)
    #     print("handle_tcp_income")
    done = False
    while not done:
        try:
            data = await remote_reader.read(4096)
            if len(data) == 0:
                # print("handle_tcp_income: 连接正常关闭")
                break
            # print("cc handle_tcp_income read:", len(data))
            writer.write(data)
            await writer.drain()
            # print("cc handle_tcp_income write:", len(data))
        except socket.error as e:
            logger.error(e)
            done = True
    writer.close()
    remote_writer.close()
    await writer.wait_closed()
    await remote_writer.wait_closed()

async def start_server():
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    server = await asyncio.start_server(client_connected, port=2333, ssl=ssl_ctx)
    # print(type(server))
    addr = server.sockets[0].getsockname()
    logger.info(f"服务器启动在 {addr[0]}:{addr[1]}")
    # 保持服务器运行
    await server.serve_forever()

def main():
    """
    运行服务器
    """
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")

# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    main()

