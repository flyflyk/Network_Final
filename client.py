import socket
import struct
import time
import random

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100
MAX_PAYLOAD_LEN = 32
AGGREGATION_SIZE = 30 

def fast_xor(b1, b2):
    parts1 = struct.unpack('!QQQQ', b1)
    parts2 = struct.unpack('!QQQQ', b2)
    result = [(p1 ^ p2) for p1, p2 in zip(parts1, parts2)]
    return struct.pack('!QQQQ', *result)

def get_neighbors(seed):
    rng = random.Random(seed)
    degree = rng.choices([1, 2, 3, 4, 5, 6], weights=[10, 30, 30, 15, 10, 5])[0]
    neighbors = rng.sample(range(1, TOTAL_PACKETS + 1), degree)
    return neighbors

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    
    # Pre-generate source blocks
    source_blocks = {}
    for seq_id in range(1, TOTAL_PACKETS + 1):
        raw_str = f"Data_for_{seq_id}"
        payload = raw_str.encode('utf-8').ljust(MAX_PAYLOAD_LEN, b'\x00')
        source_blocks[seq_id] = payload

    start_time = time.time()
    udp_packets_sent = 0

    def send_packed(chunks_list):
        nonlocal udp_packets_sent
        # Batch chunks
        for i in range(0, len(chunks_list), AGGREGATION_SIZE):
            batch = chunks_list[i : i + AGGREGATION_SIZE]
            # Concatenate
            udp_payload = b''.join(batch)
            sock.sendto(udp_payload, (PROXY_IP, PROXY_PORT))
            udp_packets_sent += 1

    # Systematic(raw)
    sys_chunks = []
    for seq_id in range(1, TOTAL_PACKETS + 1):
        header = struct.pack('!I', seq_id)
        sys_chunks.append(header + source_blocks[seq_id])
    
    # Sequentially send
    print("Sending Systematic...")
    send_packed(sys_chunks)

    # Shuffled send
    random.shuffle(sys_chunks)
    send_packed(sys_chunks)
    
    # Re-send shuffled
    random.shuffle(sys_chunks)
    send_packed(sys_chunks)

    # Fountain Repair
    print("Sending Fountain Repair...")
    repair_chunks = []
    base_seed = 10001
    
    for i in range(120):
        seed = base_seed + i
        neighbors = get_neighbors(seed)
        mixed = source_blocks[neighbors[0]]
        for n_id in neighbors[1:]:
            mixed = fast_xor(mixed, source_blocks[n_id])
        
        repair_chunks.append(struct.pack('!I', seed) + mixed)
        
    send_packed(repair_chunks)

    duration = time.time() - start_time
    print(f"\n[Client] Finished. Sent {udp_packets_sent} UDP packets in {duration:.3f}s")
    sock.close()

if __name__ == "__main__":
    run_client()