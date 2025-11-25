import socket
import struct
import time

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100
TOTAL_ROUNDS = 8 

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    
    # Pre-generate packets
    packets = []
    for seq_id in range(1, TOTAL_PACKETS + 1):
        header = struct.pack('!I', seq_id)
        payload = f"Data_for_{seq_id}".encode('utf-8')
        packets.append(header + payload)
    
    start_time = time.time()

    # Interleaved sending
    for round_idx in range(1, TOTAL_ROUNDS + 1):
        print(f"Sending Round {round_idx}/{TOTAL_ROUNDS}...")
        
        for packet in packets:
            sock.sendto(packet, (PROXY_IP, PROXY_PORT))
            
            # Traffic shaping
            if round_idx == 1:
                time.sleep(0.002) 
            else:
                time.sleep(0.0005)

    duration = time.time() - start_time
    print(f"\n[Client] Finished. Sent {TOTAL_PACKETS * TOTAL_ROUNDS} packets in {duration:.3f}s")
    sock.close()

if __name__ == "__main__":
    run_client()