import socket
import time
import select

PROXY_IP = '20.243.17.90'
PROXY_PORT = 5405
CLIENT_PORT = 5405
TOTAL_PACKETS = 100

def run_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        client_socket.bind(('0.0.0.0', CLIENT_PORT))
    except OSError:
        print(f"[Error] Port {CLIENT_PORT} is busy. Please close other processes using it.")
        return

    print(f"[Client] Sending to Proxy at {PROXY_IP}:{PROXY_PORT} from Port {CLIENT_PORT}")

    # Format: seq|timestamp|data
    packets_data = [f"Data_Packet_{i}" for i in range(TOTAL_PACKETS)]
    
    acked_seqs = set()
    start_time = time.time()
    
    while len(acked_seqs) < TOTAL_PACKETS:
        for seq in range(TOTAL_PACKETS):
            if seq not in acked_seqs:
                msg = f"{seq}|{start_time}|{packets_data[seq]}"
                try:
                    client_socket.sendto(msg.encode('utf-8'), (PROXY_IP, PROXY_PORT))
                except OSError:
                    pass

        start_wait = time.time()
        while time.time() - start_wait < 0.05:
            ready = select.select([client_socket], [], [], 0.01)
            if ready[0]:
                try:
                    data, _ = client_socket.recvfrom(1024)
                    ack_msg = data.decode('utf-8')
                    if ack_msg.startswith("ACK|"):
                        ack_seq = int(ack_msg.split('|')[1])
                        acked_seqs.add(ack_seq)
                except Exception:
                    pass
            
            if len(acked_seqs) == TOTAL_PACKETS:
                break
        
        print(f"\r[Client] Progress: {len(acked_seqs)}/{TOTAL_PACKETS} packets acknowledged...", end="")

    print(f"\n[Client] Finished. All {TOTAL_PACKETS} packets acknowledged.")
    client_socket.close()

if __name__ == "__main__":
    run_client()