import socket
import struct
import time
import random

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100
MAX_PAYLOAD_LEN = 32
CHUNK_SIZE = 4 + MAX_PAYLOAD_LEN

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

def run_server():
    restored_blocks = {}
    droplets = [] 
    first_packet_time = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.bind((BIND_IP, BIND_PORT))
    
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    
    while len(restored_blocks) < TOTAL_PACKETS:
        try:
            sock.settimeout(2.0)
            data, _ = sock.recvfrom(4096)
            
            if first_packet_time is None:
                first_packet_time = time.time()
            
            # Unpack
            offset = 0
            while offset + CHUNK_SIZE <= len(data):
                chunk = data[offset : offset + CHUNK_SIZE]
                seed = struct.unpack('!I', chunk[:4])[0]
                payload = chunk[4:]
                offset += CHUNK_SIZE
                if 1 <= seed <= TOTAL_PACKETS:
                    neighbors = {seed}
                else:
                    neighbors = set(get_neighbors(seed))
                
                # Fast peeling
                for known_id in list(neighbors):
                    if known_id in restored_blocks:
                        payload = fast_xor(payload, restored_blocks[known_id])
                        neighbors.remove(known_id)
                
                if len(neighbors) == 1:
                    new_id = list(neighbors)[0]
                    if new_id not in restored_blocks:
                        restored_blocks[new_id] = payload
                        stack = [new_id]
                        while stack:
                            solved_id = stack.pop()
                            solved_data = restored_blocks[solved_id]
                            for i in range(len(droplets) - 1, -1, -1):
                                d_neighbors, d_data = droplets[i]
                                if solved_id in d_neighbors:
                                    d_data = fast_xor(d_data, solved_data)
                                    d_neighbors.remove(solved_id)
                                    droplets[i][1] = d_data
                                    if len(d_neighbors) == 1:
                                        found_id = list(d_neighbors)[0]
                                        if found_id not in restored_blocks:
                                            restored_blocks[found_id] = d_data
                                            stack.append(found_id)
                                        droplets.pop(i)
                elif len(neighbors) > 1:
                    droplets.append([neighbors, payload])

        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error: {e}")

    total_time = time.time() - first_packet_time
    print(f"\n\n=== Success! {total_time:.3f}s ===")
    
    sorted_keys = sorted(restored_blocks.keys())
    for k in sorted_keys:
        print(f"Packet {k}: {restored_blocks[k].rstrip(b'\x00').decode('utf-8')}")
    print("Server shutting down.")

if __name__ == "__main__":
    run_server()