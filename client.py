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
    sock.settimeout(0.02)
    
    # Prepare all chunks
    # Format: [ID 5 bytes][Base64 Payload 44 bytes]
    all_chunks = []
    for seq_id in range(1, TOTAL_PACKETS + 1):
        raw_str = f"Data_for_{seq_id}"
        payload_bytes = raw_str.encode('utf-8').ljust(MAX_PAYLOAD_LEN, b'\x00')
        b64_payload = base64.b64encode(payload_bytes)
        header = f"{seq_id:05d}".encode('utf-8')
        all_chunks.append(header + b64_payload)

    # Chunk packing
    BATCH_SIZE = 28
    packed_batches = []
    
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = b''.join(all_chunks[i : i + BATCH_SIZE])
        packed_batches.append(batch)
    
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    print(f"Total Batches per round: {len(packed_batches)}")

    start_time = time.time()
    
    # Sequential -> Reverse -> Random
    for batch in packed_batches:
        sock.sendto(batch, (PROXY_IP, PROXY_PORT))
    for batch in reversed(packed_batches):
        sock.sendto(batch, (PROXY_IP, PROXY_PORT))
    random.shuffle(packed_batches)
    for batch in packed_batches:
        sock.sendto(batch, (PROXY_IP, PROXY_PORT))

    print("Polling for FIN...")
    ping_msg = b'PING'
    fin_received = False
    for _ in range(200):
        sock.sendto(ping_msg, (PROXY_IP, PROXY_PORT))
        try:
            data, _ = sock.recvfrom(1024)
            if b'FIN' in data:
                total_time = (time.time() - start_time) * 1000
                print(f"\n[Success] FIN received!")
                print(f"Total End-to-End Latency: {total_time:.3f} ms")
                fin_received = True
                break
        except socket.timeout:
            continue
            
    if not fin_received:
        print("Timeout waiting for FIN.")
        
    sock.close()

if __name__ == "__main__":
    run_client()