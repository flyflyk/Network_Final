import socket
import struct
import time

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100

def run_server():
    buffer = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, BIND_PORT))
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    
    # Receive loop
    while len(buffer) < TOTAL_PACKETS:
        try:
            data, addr = sock.recvfrom(1024)
            
            # Resolve packet
            seq_id = struct.unpack('!I', data[:4])[0]
            payload = data[4:].decode('utf-8')
            ack_packet = struct.pack('!I', seq_id)
            sock.sendto(ack_packet, addr)
            
            if seq_id not in buffer:
                buffer[seq_id] = payload
                print(f"[Recv] Seq: {seq_id} (Total: {len(buffer)}/{TOTAL_PACKETS})")
     
        except Exception as e:
            print(f"Error: {e}")

    # Display
    print("\n=== Collection Complete. Sorting... ===")
    sorted_keys = sorted(buffer.keys())
    for k in sorted_keys:
        print(f"Packet {k}: {buffer[k]}")
    print("Server will stay alive for 10 seconds to handle lagging packets...")
    
    start_wait = time.time()
    sock.settimeout(1.0)
    
    # ACK-Reflector loop
    while time.time() - start_wait < 10.0:
        try:
            data, addr = sock.recvfrom(1024)
            seq_id = struct.unpack('!I', data[:4])[0]
            ack_packet = struct.pack('!I', seq_id)
            sock.sendto(ack_packet, addr)
        except socket.timeout:
            continue
        except Exception:
            pass

    print("Server shutting down.")

if __name__ == "__main__":
    run_server()