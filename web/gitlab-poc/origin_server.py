# simple_listener.py
import socket
import threading

HOST = "127.0.0.1"
PORT = 9090

def handle_client(conn, addr):
    print(f"[+] Received connection from {addr}")
    try:
        data = conn.recv(4096)
        if data:
            print("--- REQUEST DATA ---")
            print(data.decode('latin1', errors='replace'))
            print("--------------------")
        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nHello from your server!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)
    print(f"[*] Listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()

