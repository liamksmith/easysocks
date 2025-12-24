from socket import socket, AF_INET, SOCK_STREAM


def main():
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect(('localhost', 8080))
        rsnd = s.send('hello! world\n'.encode('utf-8'))
        print('send bytes:', rsnd)
        print(s.recv(1024).decode('utf-8'))
        s.close()
    except Exception as e:
        print(type(e), e)

if __name__ == '__main__':
    main()