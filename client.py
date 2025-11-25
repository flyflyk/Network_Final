import socket
import struct
import time
import random
import base64

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100
MAX_PAYLOAD_LEN = 32

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
    sock.settimeout(0.5) 
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    
    source_blocks = {}
    for seq_id in range(1, TOTAL_PACKETS + 1):
        raw_str = f"Data_for_{seq_id}"
        payload = raw_str.encode('utf-8').ljust(MAX_PAYLOAD_LEN, b'\x00')
        source_blocks[seq_id] = payload

    udp_packets_sent = 0

    def send_packed(packets_list, batch_count):
        nonlocal udp_packets_sent
        for i in range(0, len(packets_list), batch_count):
            batch = packets_list[i : i + batch_count]
            udp_payload = b''.join(batch)
            sock.sendto(udp_payload, (PROXY_IP, PROXY_PORT))
            udp_packets_sent += 1
            time.sleep(0.002)

    # Prepare Systematic packets
    sys_chunks = []
    for seq_id in range(1, TOTAL_PACKETS + 1):
        header = f"{seq_id:05d}".encode('utf-8')
        sys_chunks.append(header + source_blocks[seq_id])

    start_time = time.time()

    print("Sending Systematic...")
    send_packed(sys_chunks, batch_count=30)
    random.shuffle(sys_chunks)
    send_packed(sys_chunks, batch_count=30)
    random.shuffle(sys_chunks)
    send_packed(sys_chunks, batch_count=30)

    print("Sending Fountain Repair...")
    repair_chunks = []
    base_seed = 10001
    for i in range(120):
        seed = base_seed + i
        neighbors = get_neighbors(seed)
        mixed = source_blocks[neighbors[0]]
        for n_id in neighbors[1:]:
            mixed = fast_xor(mixed, source_blocks[n_id])
        
        safe_payload = base64.b64encode(mixed)
        header = f"{seed:05d}".encode('utf-8')
        repair_chunks.append(header + safe_payload)
        
    send_packed(repair_chunks, batch_count=25)

    print("Data sent. Polling Server for FIN signal...")
    ping_packet = f"{0:05d}".encode('utf-8') + b'PING' * 5
    received_fin = False
    
    for _ in range(20):
        try:
            # Ping
            sock.sendto(ping_packet, (PROXY_IP, PROXY_PORT))
            
            # Capture FIN
            start_poll = time.time()
            while time.time() - start_poll < 0.5:
                try:
                    data, _ = sock.recvfrom(1024)
                    if b'FIN' in data or data.startswith(b'00000'):
                        end_time = time.time()
                        total_ms = (end_time - start_time) * 1000
                        print(f"\n[Success] Server ack completion!")
                        print(f"Total End-to-End Latency: {total_ms:.3f} ms")
                        received_fin = True
                        break
                except socket.timeout:
                    break
            
            if received_fin:
                break
                
        except Exception as e:
            print(f"Error: {e}")
            break

    if not received_fin:
        print("\n[Warning] Timed out waiting for Server FIN.")
        send_only_ms = (time.time() - start_time) * 1000
        print(f"Sending Duration (Client side only): {send_only_ms:.3f} ms")

    sock.close()

if __name__ == "__main__":
    run_client()