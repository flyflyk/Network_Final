import socket
import struct

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, BIND_PORT))
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    buffer = {}
    
    while len(buffer) < TOTAL_PACKETS:
        try:
            data, addr = sock.recvfrom(1024)
            
            # Resolve packet
            seq_id = struct.unpack('!I', data[:4])[0]
            payload = data[4:].decode('utf-8')
            
            # Send ACK
            ack_packet = struct.pack('!I', seq_id)
            sock.sendto(ack_packet, addr)
            
            # Record received packet
            if seq_id not in buffer:
                buffer[seq_id] = payload
                print(f"[Recv] Seq: {seq_id} (Total: {len(buffer)}/{TOTAL_PACKETS})")
                
        except Exception as e:
            print(f"Error: {e}")

    print("\n=== Collection Complete. Sorting... ===")
    
    # Sort
    sorted_keys = sorted(buffer.keys())
    for k in sorted_keys:
        print(f"Packet {k}: {buffer[k]}")
        
    print("=== All 100 packets received and sorted successfully. ===")

if __name__ == "__main__":
    run_server()