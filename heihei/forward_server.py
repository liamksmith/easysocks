# 这是一个示例 Python 脚本。
import asyncio
import socket
import struct
from optparse import OptionParser

from loguru import logger

class ForwardService:
    def __init__(self, proxy_host, proxy_port):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    async def client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # print("a client has connected")
        try:
            ## $1
            data = await reader.read(262)
            if len(data) < 1:
                raise Exception("no data")
            writer.write(b"\x05\x00")   # 0x00: no authentication required always
            await writer.drain()
            ## $2 skip AUTH, process CONNECT CMD
            data = await reader.read(4)
            mode = data[1]
            if mode != 1:  # CONNECT X'01' / BIND X'02' / UDP ASSOCIATE X'03'
                logger.error('mode != 1')
                return
            addr_type = data[3]

            buf_about_remote = struct.pack('>B', addr_type)
            if addr_type == 1:  # IP V4 address: X'01'
                addr_ip = await reader.read(4)
                addr = socket.inet_ntoa(addr_ip)
                logger.info("CONNECT - target addr is: " + addr)
                buf_about_remote += addr_ip
            elif addr_type == 3:  # DOMAINNAME: X'03'
                data = await reader.read(1)
                addr_len = data[0]
                addr = await reader.read(addr_len)
                addr = addr.decode()
                logger.info("CONNECT - target addr is: " + addr)
                buf_about_remote += struct.pack('>B', addr_len)
                buf_about_remote += addr.encode()
            else:
                # not support
                logger.error("addr_type:{} not support".format(addr_type))
                raise Exception('addr_type not support')
            port = await reader.read(2)
            buf_about_remote += port

            logger.info('connecting proxy server %s:%d' % (self.proxy_host, self.proxy_port))
            remote_reader, remote_writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)
            logger.info("connected:{}, {}".format(self.proxy_host, self.proxy_port))
            # tell proxy the target server:port
            remote_writer.write(buf_about_remote)
            await remote_writer.drain()
            result = await remote_reader.read(1)
            if len(result) == 0:
                logger.error("proxy server has closed the connection.")
                remote_writer.close()
                return
            if result[0] != 0x00:
                logger.error("proxy server has denied the request.")
                remote_writer.close()
                return

            # OK, the proxy tells us target server has connected.
            reply: bytes = b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00"
            writer.write(reply)
            await writer.drain()

            task1 = asyncio.create_task(ForwardService.handle_tcp_out(reader, writer, remote_reader, remote_writer))
            task2 = asyncio.create_task(ForwardService.handle_tcp_income(reader, writer, remote_reader, remote_writer))
            await asyncio.gather(task1, task2)
        except socket.error as r:
            logger.error(r)
        # except Exception as e:
        #     logger.info(e)
        finally:
            writer.close()
            await writer.wait_closed()
            # print("a client has disconnected")

    @staticmethod
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
                    # print("handle_tcp_out: 连接正常关闭")
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

    @staticmethod
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
                    # print("handle_tcp_income: 连接正常关闭")
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

    async def start_server(self):
        server = await asyncio.start_server(self.client_connected, port=10080)
        # print(type(server))
        addr = server.sockets[0].getsockname()
        logger.info(f"forward service running {addr[0]}:{addr[1]}")
        # 保持服务器运行
        await server.serve_forever()

    def run(self):
        asyncio.run(self.start_server())


def main():
    parser = OptionParser()
    parser.add_option("-r", "--host", action="store", type="string", dest="proxy_host", default="127.0.0.1",
                      help="input proxy server host e.g. 118.1.24.4")
    parser.add_option("-p", "--port", action="store", type="int", dest="proxy_port", default=2333,
                      help="proxy server port")
    opts, _ = parser.parse_args()
    try:
        f = ForwardService(opts.proxy_host, opts.proxy_port)
        f.run()
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")

# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    main()

