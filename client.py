import socket
import struct
import time
import random

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100
MAX_PAYLOAD_LEN = 32
EXTRA_PACKETS = 60 

def xor_bytes(b1, b2):
    return bytes(x ^ y for x, y in zip(b1, b2))

def get_neighbors(seed):
    rng = random.Random(seed)
    degree = rng.randint(1, 6)
    neighbors = rng.sample(range(1, TOTAL_PACKETS + 1), degree)

    return neighbors

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    
    # Prepare source data blocks
    src_blocks = {}
    for seq_id in range(1, TOTAL_PACKETS + 1):
        raw_str = f"Data_for_{seq_id}"
        # Pad with null bytes to 32 length
        payload = raw_str.encode('utf-8').ljust(MAX_PAYLOAD_LEN, b'\x00')
        src_blocks[seq_id] = payload
    
    start_time = time.time()
    sent_count = 0
    
    # Systematic packets
    print("Sending Systematic packets...")
    for seq_id in range(1, TOTAL_PACKETS + 1):
        header = struct.pack('!I', seq_id) 
        sock.sendto(header + src_blocks[seq_id], (PROXY_IP, PROXY_PORT))
        sent_count += 1
        if seq_id % 10 == 0:
            time.sleep(0.002)
    
    # Fountain encoded packets
    print(f"Sending {EXTRA_PACKETS} Fountain Droplets...")
    base_seed = 10001 
    
    for i in range(EXTRA_PACKETS):
        seed = base_seed + i
        neighbors = get_neighbors(seed)
        mixed_payload = src_blocks[neighbors[0]]
        for n_id in neighbors[1:]:
            mixed_payload = xor_bytes(mixed_payload, src_blocks[n_id])
            
        header = struct.pack('!I', seed)
        sock.sendto(header + mixed_payload, (PROXY_IP, PROXY_PORT))
        sent_count += 1
    
        time.sleep(0.001)

    duration = time.time() - start_time
    print(f"\n[Client] Finished. Sent {sent_count} packets in {duration:.3f}s")
    sock.close()

if __name__ == "__main__":
    run_client()