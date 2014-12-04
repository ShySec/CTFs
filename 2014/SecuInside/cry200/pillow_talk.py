# Source Generated with Decompyle++
# File: pillow_reader.pyc (Python 3.2)

import socket
import struct
import sys
import binascii
from PKI import PKI
from PKI import PubKey
g_guestkey = '\xc3\xa1\xc3\xa7\xc2\xac\xc2\xa9\x19\xcc\xc3\xb0'
g_pki_client = PKI()
g_pki_server = PKI()

def s2i(s):
    b = s2b(s)
    t = binascii.hexlify(b)
    return int(t, 16)


def b2s(b):
    res = ''
    for x in b:
        res += chr(x)

    return res


def s2b(s):
    res = b''
    for x in s:
        res += bytes([
            ord(x)])

    return res


def i2s(i):
    d = hex(i)
    if d[-1] == 'L':
        d = d[:-1]
    if d[:2] == '0x':
        d = d[2:]
    if len(d) % 2 == 1:
        d = '0' + d
    res = bytes.fromhex(d)
    res = b2s(res)
    return res


def create_socket(host, port):
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s


def exchange_key():
    s.recv(1024)
    write(hex(g_pki_client.pubkey.n), False)
    data = read(1024, False)
    if data[-1] == 76:
        data = data[:-1]
    n = int(data, 16)
    return PubKey(n)


def write(data, with_encryption = True):
    if with_encryption:
        if not len(data) < 4.63871e+18:
            raise AssertionError
        data = g_pki_server.encrypt(s2i(data))
    size = b2s(struct.pack('<I', len(data)))
    send_data = size + data
    s.send(s2b(send_data))


def read(size, with_encryption = True):
    size_str = s.recv(4)
    size = struct.unpack('<I', size_str)[0]
    data = s.recv(size)
    if size != len(data):
        print('Wrong data size.\n')
        sys.exit(1)
    if with_encryption:
        data_int = s2i(b2s(data))
        data = i2s(g_pki_client.decrypt(data_int))
    return data


def read_files(authkey, filenames):
    cmd = 'cat '
    for filename in filenames:
        cmd += filename + ' '

    cmd = cmd.rstrip() + '\n'
    write(authkey + cmd)
    res = ''
    for _ in range(len(filenames)):
        res += read(1024)

    return res


def main():
    global s, g_pki_server
    if len(sys.argv) < 4:
        print('Usage> %s <host> <port> <filename> <optional:authkey>' % sys.argv[0])
        return 1
    host = sys.argv[1]
    port = sys.argv[2]
    filename = sys.argv[3]
    if len(sys.argv) >= 5:
        key = sys.argv[4]
    else:
        key = g_guestkey
    s = create_socket(host, int(port))
    pubkey_server = exchange_key()
    g_pki_server = PKI(pubkey_server)
    print(read_files(key, [
        filename]))

if __name__ == '__main__':
    main()
