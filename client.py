import socket
import time
import random
import base64

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100
MAX_PAYLOAD_LEN = 32

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.05) 
    
    all_chunks = []
    for seq_id in range(1, TOTAL_PACKETS + 1):
        raw_str = f"Data_for_{seq_id}"
        payload_bytes = raw_str.encode('utf-8').ljust(MAX_PAYLOAD_LEN, b'\x00')
        b64_payload = base64.b64encode(payload_bytes)
        header = f"{seq_id:05d}".encode('utf-8')
        all_chunks.append(header + b64_payload)

    BATCH_SIZE = 28
    packed_batches = []
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = b''.join(all_chunks[i : i + BATCH_SIZE])
        packed_batches.append(batch)
    
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    
    start_time = time.time()
    
    print("Sending data...")
    for round_idx in range(6):
        if round_idx >= 2:
            random.shuffle(packed_batches)
            
        for b in packed_batches: 
            sock.sendto(b, (PROXY_IP, PROXY_PORT))
            time.sleep(0.005)

    print("Data sent. Polling for FIN...")
    ping_msg = b'PING'
    received_fin = False
    polling_start_time = time.time()
    while time.time() - polling_start_time < 20.0:
        try:
            sock.sendto(ping_msg, (PROXY_IP, PROXY_PORT))
            sub_start = time.time()
            while time.time() - sub_start < 1.0:
                try:
                    data, _ = sock.recvfrom(2048)
                    
                    if b'FIN' in data:
                        end_time = time.time()
                        total_duration_ms = (end_time - start_time) * 1000
                        print(f"\n[Success] FIN received!")
                        print(f"Total Communication Time: {total_duration_ms:.3f} ms")
                        received_fin = True
                        break
                        
                except socket.timeout:
                    break
            
            if received_fin:
                break
            
            time.sleep(0.2)

        except Exception as e:
            print(f"Error: {e}")
            break
            
    if not received_fin:
        print("\n[Warning] Timed out waiting for FIN.")
        print(f"Elapsed: {(time.time() - start_time)*1000:.3f} ms")

    sock.close()

if __name__ == "__main__":
    run_client()