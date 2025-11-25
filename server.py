import socket
import struct
import time
import random
import base64

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100
LEN_HEADER = 5 
LEN_RAW_PAYLOAD = 32
LEN_B64_PAYLOAD = 44 

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
    first_packet_arrival = None
    last_addr = None
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.bind((BIND_IP, BIND_PORT))
    
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    fin_packet = f"{0:05d}".encode('utf-8') + b'FIN' * 5
    while len(restored_blocks) < TOTAL_PACKETS:
        try:
            sock.settimeout(5.0)
            data, addr = sock.recvfrom(4096) 
            last_addr = addr
            
            if first_packet_arrival is None:
                first_packet_arrival = time.time()
            
            offset = 0
            while offset + LEN_HEADER <= len(data):
                try:
                    seed_str = data[offset : offset + LEN_HEADER]
                    seed = int(seed_str)
                    offset += LEN_HEADER
                except ValueError: break

                if seed == 0:
                    sock.sendto(fin_packet, addr)
                    continue

                payload = None
                if 1 <= seed <= TOTAL_PACKETS:
                    if offset + LEN_RAW_PAYLOAD <= len(data):
                        payload = data[offset : offset + LEN_RAW_PAYLOAD]
                        offset += LEN_RAW_PAYLOAD
                        neighbors = {seed}
                    else: break 
                else:
                    if offset + LEN_B64_PAYLOAD <= len(data):
                        b64_data = data[offset : offset + LEN_B64_PAYLOAD]
                        offset += LEN_B64_PAYLOAD
                        try:
                            payload = base64.b64decode(b64_data)
                        except: continue
                        neighbors = set(get_neighbors(seed))
                    else: break

                if payload is None: continue

                # Decoding
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

    # FIN
    server_duration = (time.time() - first_packet_arrival) * 1000
    print(f"\n[Done] Processing Time: {server_duration:.3f} ms. Sending FINs...")

    if last_addr:
        for _ in range(20):
            sock.sendto(fin_packet, last_addr)
            time.sleep(0.0005)

    start_wait = time.time()
    sock.settimeout(0.1)
    
    while time.time() - start_wait < 5.0:
        try:
            data, addr = sock.recvfrom(1024)
            sock.sendto(fin_packet, addr)
        except socket.timeout:
            continue
        except Exception:
            pass
            
    print("Server shutting down.")

if __name__ == "__main__":
    run_server()