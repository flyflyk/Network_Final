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
    start_time_from_client = None
    
    while len(received_packets) < TOTAL_PACKETS:
        try:
            data, addr = server_socket.recvfrom(4096)
            message = data.decode('utf-8')
            
            parts = message.split('|', 2)
            if len(parts) < 3:
                continue
                
            seq_id = int(parts[0])
            timestamp = float(parts[1])
            payload = parts[2]
            
            if start_time_from_client is None or timestamp < start_time_from_client:
                start_time_from_client = timestamp

            if seq_id not in received_packets:
                received_packets[seq_id] = payload

            ack_msg = f"ACK|{seq_id}"
            server_socket.sendto(ack_msg.encode('utf-8'), addr)
            
        except BlockingIOError:
            continue
        except Exception as e:
            print(f"[Server] Error: {e}")

    end_time = time.time()
    total_duration = end_time - start_time_from_client
    
    print("\n" + "="*30)
    print(f"[Server] All {TOTAL_PACKETS} packets collected.")
    print(f"[Result] Total Communication Time: {total_duration:.6f} seconds")
    print(f"[Server] Entering Teardown Phase...")
    print("="*30)
   
    last_packet_time = time.time()
    
    while True:
        try:
            data, addr = server_socket.recvfrom(4096)
            last_packet_time = time.time()
            
            message = data.decode('utf-8')
            parts = message.split('|', 1)
            seq_id = int(parts[0])
            
            ack_msg = f"ACK|{seq_id}"
            server_socket.sendto(ack_msg.encode('utf-8'), addr)
            
        except BlockingIOError:
            pass
        except Exception:
            pass

        if time.time() - last_packet_time > 3.0:
            print("[Server] No retries received for 3 seconds. Shutting down.")
            break
            
    sorted_packets = sorted(received_packets.items(), key=lambda x: x[0])
    print(f"[Server] Final check: {len(sorted_packets)} packets sorted.")

if __name__ == "__main__":
    run_server()