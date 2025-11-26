import socket
import time
import base64

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100
BLOCK_SIZE = 49 # Header (5 bytes ID) + Payload (32 bytes raw -> 44 bytes b64) = 49 bytes
LEN_HEADER = 5
LEN_B64_PAYLOAD = 44

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.bind((BIND_IP, BIND_PORT))
    
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    
    received_data = {}
    first_packet_time = None
    fin_packet = b'FIN' * 10
    
    while len(received_data) < TOTAL_PACKETS:
        try:
            data, addr = sock.recvfrom(4096)
            
            if first_packet_time is None:
                first_packet_time = time.time()
            
            # Ping
            if data.startswith(b'PING'):
                if len(received_data) == TOTAL_PACKETS:
                    sock.sendto(fin_packet, addr)
                continue

            # Resolve chunks
            L = len(data)
            full_blocks = L // BLOCK_SIZE
            
            for i in range(full_blocks):
                start = i * BLOCK_SIZE
                chunk = data[start : start + BLOCK_SIZE]
                try:
                    seq_id_str = chunk[:LEN_HEADER]
                    seq_id = int(seq_id_str)
                except ValueError:
                    continue
                
                # Decode and save
                if seq_id not in received_data and 1 <= seq_id <= TOTAL_PACKETS:
                    b64_body = chunk[LEN_HEADER:]
                    try:
                        raw_payload = base64.b64decode(b64_body)
                        received_data[seq_id] = raw_payload
                    except:
                        pass
            
            # Respond FIN if complete
            if len(received_data) == TOTAL_PACKETS:
                sock.sendto(fin_packet, addr)
                break

        except Exception as e:
            print(f"Error: {e}")
            continue

    duration = (time.time() - first_packet_time) * 1000
    print(f"\n[Done] Total Duration: {duration:.3f} ms")
    
    # Sort
    sorted_packets = [received_data[k] for k in sorted(received_data.keys())]
    print(f"First packet: {sorted_packets[0]}, Last: {sorted_packets[-1]}")

    # Respond FIN
    sock.settimeout(0.5)
    end_wait = time.time() + 2.0
    while time.time() < end_wait:
        try:
            _, a = sock.recvfrom(1024)
            sock.sendto(fin_packet, a)
        except socket.timeout:
            pass
            
    print("Server finished.")

if __name__ == "__main__":
    run_server()