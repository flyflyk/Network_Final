import socket
import base64
import time

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100
BLOCK_SIZE = 49 # Format: [ID(5 bytes)] + [Base64_Data(44 bytes)] = 49 bytes
LEN_HEADER = 5

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
    sock.bind((BIND_IP, BIND_PORT))
    
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    
    received_data = {}
    fin_payload = b'FIN' * 10
    collect_fin = False

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if not collect_fin:
                if not data.startswith(b'PING'):
                    # Batch unpacking
                    num_chunks = len(data) // BLOCK_SIZE
                    for i in range(num_chunks):
                        start = i * BLOCK_SIZE
                        chunk = data[start : start + BLOCK_SIZE]
                        try:
                            seq_id = int(chunk[:LEN_HEADER])
                            if 1 <= seq_id <= TOTAL_PACKETS:
                                if seq_id not in received_data:
                                    b64_body = chunk[LEN_HEADER:]
                                    received_data[seq_id] = base64.b64decode(b64_body)
                        except ValueError:
                            pass
                
                if len(received_data) == TOTAL_PACKETS:
                    collect_fin = True
                    sorted_packets = [received_data[k] for k in sorted(received_data.keys())]
                    print(f"[Server] Received all {TOTAL_PACKETS} packets.")
                    print(f"First: {sorted_packets[0][:20]}...") 
                    print(f"Last:  {sorted_packets[-1][:20]}...")

            if collect_fin:
                for _ in range(5):
                    sock.sendto(fin_payload, addr)
                    time.sleep(0.002)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        pass