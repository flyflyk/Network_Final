import socket
import struct

BIND_IP = "0.0.0.0"
BIND_PORT = 5405
TOTAL_PACKETS = 100

def run_server():
    buffer = {}
    has_started = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, BIND_PORT))
    print(f"Server listening on {BIND_IP}:{BIND_PORT}")
    print("Mode: Passive Collection (Waiting for data...)")
    
    while True:
        try:
            sock.settimeout(3.0) 
            data, _ = sock.recvfrom(1024)
            has_started = True
            
            # Resolve seq ID
            seq_id = struct.unpack('!I', data[:4])[0]
            payload = data[4:].decode('utf-8')
            
            # Save in buffer
            if seq_id not in buffer:
                buffer[seq_id] = payload
                print(f"[Recv] New Seq: {seq_id} (Count: {len(buffer)}/{TOTAL_PACKETS})")
            
            if len(buffer) >= TOTAL_PACKETS:
                print("All 100 packets collected!")
                break

        except socket.timeout:
            if has_started:
                print("\nNo data for 3 seconds. Assuming transmission complete.")
                break
            else:
                continue
        except Exception as e:
            print(f"Error: {e}")


    print("\n=== Final Result (Sorted) ===")    
    # Check loss
    missing_packets = []
    for i in range(1, TOTAL_PACKETS + 1):
        if i not in buffer:
            missing_packets.append(i)
            
    if missing_packets:
        print(f"Warning: Missing {len(missing_packets)} packets: {missing_packets}")
    else:
        print("Success: No packet loss!")

    # Sort
    sorted_keys = sorted(buffer.keys())
    for k in sorted_keys:
        print(f"Packet {k}: {buffer[k]}")
        
    print("\nServer shutting down.")

if __name__ == "__main__":
    run_server()