from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler


class ThreadedTcpServer(ThreadingMixIn, TCPServer):
    pass

class TCPHandler(StreamRequestHandler):
    def handle(self):
        try:
            print("Got connection from {}".format(self.client_address))
            # data = self.rfile.readline()
            sock = self.connection
            data = sock.recv(1024)
            print('echo: ', data, ', len:', len(data))
            self.wfile.write(data)
        except Exception as e:
            print('{}:{}'.format(type(e), e))


def main():
    PORT: int = 8080
    server = ThreadedTcpServer(('localhost', PORT), TCPHandler)
    server.allow_reuse_address = True
    print("Starting server at port {}, use <Ctrl-C> to stop", PORT)
    server.serve_forever()

if __name__ == '__main__':
    main()