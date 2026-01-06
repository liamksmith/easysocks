# 这是一个示例 Python 脚本。
import asyncio
import socket
import struct

from loguru import logger


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    print("a client has connected")
    try:
        ## $1
        data = await reader.read(262)
        if len(data) < 1:
            raise Exception("no data")
        writer.write(b"\x05\x00")   # 0x00: no authentiacion required always
        await writer.drain()
        ## skip auth  $2
        data = await reader.read(4)
        mode = data[1]
        if mode != 1:   # CONNECT X'01' / BIND X'02' / UDP ASSOCIATE X'03'
            logger.error('mode != 1')
            return
        addr_type = data[3]
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

        reply: bytes = b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        writer.write(reply)
        await writer.drain()

        task1 = asyncio.create_task(handle_tcp_out(reader, writer, remote_reader, remote_writer))
        task2 = asyncio.create_task(handle_tcp_income(reader, writer, remote_reader, remote_writer))
        await asyncio.gather(task1, task2)
    except socket.error as r:
        logger.error(r)
    except Exception as e:
        logger.info(e)
    finally:
        writer.close()
        await writer.wait_closed()
        print("a client has disconnected")

async def handle_tcp_out(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                         remote_reader: asyncio.StreamReader, remote_writer: asyncio.StreamWriter):
    # is_quit = False
    # while not is_quit:
    #     await asyncio.sleep(1)
    #     print("handle_tcp_out")
    is_quit = False
    while not is_quit:
        try:
            data = await reader.read(4096)
            # print(type(data))
            if len(data) == 0:
                print("handle_tcp_out: 连接正常关闭")
                break
            # print("handle_tcp_out cc read:", len(data))
            remote_writer.write(data)
            await remote_writer.drain()
            # print("handle_tcp_out cc write:", len(data))
        except socket.error as e:
            logger.error(e)
            is_quit = True
        except Exception as e:
            logger.error(e)
            is_quit = True
    writer.close()
    remote_writer.close()
    await writer.wait_closed()
    await remote_writer.wait_closed()

async def handle_tcp_income(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                            remote_reader: asyncio.StreamReader, remote_writer: asyncio.StreamWriter):
    # is_quit = False
    # while not is_quit:
    #     await asyncio.sleep(1)
    #     print("handle_tcp_income")
    is_quit = False
    while not is_quit:
        try:
            data = await remote_reader.read(4096)
            if len(data) == 0:
                print("handle_tcp_income: 连接正常关闭")
                break
            # print("cc handle_tcp_income read:", len(data))
            writer.write(data)
            await writer.drain()
            # print("cc handle_tcp_income write:", len(data))
        except socket.error as e:
            logger.error(e)
            is_quit = True
    writer.close()
    remote_writer.close()
    await writer.wait_closed()
    await remote_writer.wait_closed()


async def start_server():
    server = await asyncio.start_server(client_connected, port=10080)
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

