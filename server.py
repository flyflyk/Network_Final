import socket
import struct
import time
import random

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100
MAX_PAYLOAD_LEN = 32

def xor_bytes(b1, b2):
    return bytes(x ^ y for x, y in zip(b1, b2))

def get_neighbors(seed):
    rng = random.Random(seed)
    degree = rng.randint(1, 6)
    neighbors = rng.sample(range(1, TOTAL_PACKETS + 1), degree)

    return neighbors

def run_server():
    restored_blocks = {}
    droplets = []
    first_packet_time = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, BIND_PORT))
    
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    
    while len(restored_blocks) < TOTAL_PACKETS:
        try:
            data, _ = sock.recvfrom(1024)
            if first_packet_time is None:
                first_packet_time = time.time()
            
            # Resolve packet
            seed = struct.unpack('!I', data[:4])[0]
            payload = data[4:]
            
            # Primitive padding handling
            if 1 <= seed <= TOTAL_PACKETS:
                neighbors = {seed}
            else:
                neighbors = set(get_neighbors(seed))
            
            # Remove known blocks
            for known_id in list(neighbors):
                if known_id in restored_blocks:
                    payload = xor_bytes(payload, restored_blocks[known_id])
                    neighbors.remove(known_id)
            
            # Check degree
            if len(neighbors) == 1:
                new_id = list(neighbors)[0]
                
                # Prevent duplicates
                if new_id not in restored_blocks:
                    restored_blocks[new_id] = payload
                    stack = [new_id]
                    while stack:
                        solved_id = stack.pop()
                        solved_data = restored_blocks[solved_id]
                        for i in range(len(droplets) - 1, -1, -1):
                            d_neighbors, d_data = droplets[i]
                            
                            if solved_id in d_neighbors:
                                d_data = xor_bytes(d_data, solved_data)
                                d_neighbors.remove(solved_id)
                                droplets[i][1] = d_data
                                if len(d_neighbors) == 1:
                                    found_id = list(d_neighbors)[0]
                                    if found_id not in restored_blocks:
                                        found_data = d_data
                                        restored_blocks[found_id] = found_data
                                        stack.append(found_id)
                                    droplets.pop(i)
                                    
            elif len(neighbors) > 1:
                droplets.append([neighbors, payload])

        except Exception as e:
            print(f"Error: {e}")

    total_time = time.time() - first_packet_time
    print(f"\n\n=== Fountain Complete! Recovered 100 packets in {total_time:.3f}s ===")
    
    # Sort
    sorted_keys = sorted(restored_blocks.keys())
    for k in sorted_keys:
        text = restored_blocks[k].rstrip(b'\x00').decode('utf-8')
        print(f"Packet {k}: {text}")
        
    print("Server shutting down.")

if __name__ == "__main__":
    run_server()