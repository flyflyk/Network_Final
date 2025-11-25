import socket
import struct
import time

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100
REDUNDANCY_COUNT = 8 

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    print("Sending packets 1 to 100...")

    start_time = time.time()

    for seq_id in range(1, TOTAL_PACKETS + 1):
        
        # Construct packet
        header = struct.pack('!I', seq_id)
        payload = f"Data_for_{seq_id}".encode('utf-8')
        packet = header + payload
        
        # Send multiple times
        for _ in range(REDUNDANCY_COUNT):
            sock.sendto(packet, (PROXY_IP, PROXY_PORT))
            time.sleep(0.002)
            
        if seq_id % 10 == 0:
            print(f"Sent packets up to {seq_id}...")

    duration = time.time() - start_time
    print(f"\n[Client] Finished sending. Duration: {duration:.2f}s")
    sock.close()

if __name__ == "__main__":
    run_client()