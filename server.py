import socket
import time

SERVER_IP = '0.0.0.0'
SERVER_PORT = 5405
TOTAL_PACKETS = 100

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.setblocking(False)
    
    print(f"[Server] Listening on {SERVER_IP}:{SERVER_PORT}")
    
    received_packets = {}
    
    while len(received_packets) < TOTAL_PACKETS:
        try:
            data, addr = server_socket.recvfrom(4096)
            message = data.decode('utf-8')
            
            # Format: CLIENT_IP|SEQ|TIMESTAMP|DATA
            parts = message.split('|', 3)
            if len(parts) < 4:
                continue
                
            client_ip_from_msg = parts[0]
            seq_id = int(parts[1])
            payload = parts[3]
            
            if seq_id not in received_packets:
                received_packets[seq_id] = payload

            ack_msg = f"ACK|{seq_id}"
            client_addr = (client_ip_from_msg, SERVER_PORT)
            server_socket.sendto(ack_msg.encode('utf-8'), client_addr)
            
        except BlockingIOError:
            continue
        except Exception as e:
            print(f"[Server] Error: {e}")

    print("\n" + "="*30)
    print(f"[Server] All {TOTAL_PACKETS} packets collected.")
    print(f"[Server] Entering Teardown Phase...")
    print("="*30)
   
    last_packet_time = time.time()
    
    while True:
        try:
            data, addr = server_socket.recvfrom(4096)
            last_packet_time = time.time()
            
            message = data.decode('utf-8')
            parts = message.split('|', 3)
            if len(parts) < 4:
                continue

            client_ip_from_msg = parts[0]
            seq_id = int(parts[1])
            
            ack_msg = f"ACK|{seq_id}"
            client_addr = (client_ip_from_msg, SERVER_PORT)
            server_socket.sendto(ack_msg.encode('utf-8'), client_addr)
            
        except BlockingIOError:
            pass
        except Exception:
            pass

        if time.time() - last_packet_time > 3.0:
            print("[Server] No retries received for 3 seconds. Shutting down.")
            break
            
    sorted_packets = sorted(received_packets.items(), key=lambda x: x[0])
    print(f"\n[Server] Verification: {len(sorted_packets)} packets sorted successfully.")
    print("-" * 30)
    for seq, payload in sorted_packets:
        print(f"  Packet {seq}: {payload}")
    print("-" * 30)

if __name__ == "__main__":
    run_server()