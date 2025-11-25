import socket
import struct
import time
import random

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100
MAX_PAYLOAD_LEN = 32
EXTRA_PACKETS = 300

def xor_bytes(b1, b2):
    return bytes(x ^ y for x, y in zip(b1, b2))

def get_neighbors(seed):
    rng = random.Random(seed)
    degree = rng.choices([1, 2, 3, 4, 5, 6], weights=[10, 30, 30, 15, 10, 5])[0]
    neighbors = rng.sample(range(1, TOTAL_PACKETS + 1), degree)
    return neighbors

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    
    # Prepare source data blocks
    source_blocks = {}
    for seq_id in range(1, TOTAL_PACKETS + 1):
        raw_str = f"Data_for_{seq_id}"
        payload = raw_str.encode('utf-8').ljust(MAX_PAYLOAD_LEN, b'\x00')
        source_blocks[seq_id] = payload
    
    start_time = time.time()
    sent_cnt = 0
    
    # Systematic packets
    print("Sending Systematic packets...")
    for seq_id in range(1, TOTAL_PACKETS + 1):
        header = struct.pack('!I', seq_id)
        sock.sendto(header + source_blocks[seq_id], (PROXY_IP, PROXY_PORT))
        sent_cnt += 1
        time.sleep(0.0005)
        
    # Re-send systematic packets
    print("Re-sending Systematic packets...")
    for seq_id in range(1, TOTAL_PACKETS + 1):
        header = struct.pack('!I', seq_id)
        sock.sendto(header + source_blocks[seq_id], (PROXY_IP, PROXY_PORT))
        sent_cnt += 1
        time.sleep(0.0005)

    # Fountain droplets
    print(f"Sending {EXTRA_PACKETS} Fountain Droplets...")
    base_seed = 10001 
    for i in range(EXTRA_PACKETS):
        seed = base_seed + i
        neighbors = get_neighbors(seed)
        
        # XOR payload
        mixed_payload = source_blocks[neighbors[0]]
        for n_id in neighbors[1:]:
            mixed_payload = xor_bytes(mixed_payload, source_blocks[n_id])
            
        header = struct.pack('!I', seed)
        sock.sendto(header + mixed_payload, (PROXY_IP, PROXY_PORT))
        sent_cnt += 1

    duration = time.time() - start_time
    print(f"\n[Client] Finished. Sent {sent_cnt} packets in {duration:.3f}s")
    sock.close()

if __name__ == "__main__":
    run_client()