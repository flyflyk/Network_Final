import socket
import struct
import time

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100

def run_server():
    buffer = {}
    first_packet_time = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, BIND_PORT))
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")

    while len(buffer) < TOTAL_PACKETS:
        try:
            data, _ = sock.recvfrom(1024)
            if first_packet_time is None:
                first_packet_time = time.time()
            
            seq_id = struct.unpack('!I', data[:4])[0]
            
            # Process only new packets
            if seq_id not in buffer:
                payload = data[4:].decode('utf-8')
                buffer[seq_id] = payload
            
        except Exception as e:
            print(f"Error: {e}")

    total_time = time.time() - first_packet_time
    print(f"\n\n=== Success! Collected all 100 packets in {total_time:.3f}s ===")
    
    # Sort
    sorted_keys = sorted(buffer.keys())
    for k in sorted_keys:
        print(f"Packet {k}: {buffer[k]}")
        
    print("Server shutting down immediately.")

if __name__ == "__main__":
    run_server()