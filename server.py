import socket
import time
import base64

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100
BLOCK_SIZE = 49 
LEN_HEADER = 5

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
    sock.bind((BIND_IP, BIND_PORT))
    
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    
    received_data = {}
    fin_payload = b'FIN' * 10 
    last_client_addr = None

    while len(received_data) < TOTAL_PACKETS:
        try:
            data, addr = sock.recvfrom(4096)
            last_client_addr = addr
            
            if data.startswith(b'PING'):
                continue
            
            num_chunks = len(data) // BLOCK_SIZE
            for i in range(num_chunks):
                start = i * BLOCK_SIZE
                chunk = data[start : start + BLOCK_SIZE]
                try:
                    seq_id = int(chunk[:LEN_HEADER])
                    if 1 <= seq_id <= TOTAL_PACKETS and seq_id not in received_data:
                        b64_body = chunk[LEN_HEADER:]
                        received_data[seq_id] = base64.b64decode(b64_body)
                except ValueError:
                    pass
                    
        except Exception as e:
            print(f"Error: {e}")

    print(f"[Server] Collection Complete!")
    sorted_packets = [received_data[k] for k in sorted(received_data.keys())]
    print(f"First: {sorted_packets[0][:20]}...")
    print(f"Last:  {sorted_packets[-1][:20]}...")
    
    if last_client_addr:
        for _ in range(10):
            sock.sendto(fin_payload, last_client_addr)
            time.sleep(0.005)

    sock.settimeout(15.0)
    print("[Server] Entering FIN-WAIT state...")
    
    start_wait = time.time()
    while time.time() - start_wait < 15.0:
        try:
            data, client_addr = sock.recvfrom(1024)
            sock.sendto(fin_payload, client_addr)
            sock.sendto(fin_payload, client_addr)
            
        except socket.timeout:
            break
        except Exception:
            pass

    print("Server shutting down.")

if __name__ == "__main__":
    run_server()