import socket
import time
import select
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_IP = os.getenv('CLIENT_IP', '20.196.152.54')
PROXY_IP = os.getenv('PROXY_IP', '20.243.17.90')
PROXY_PORT = 5405
CLIENT_PORT = 5405
TOTAL_PACKETS = 100

def run_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        client_socket.bind(('0.0.0.0', CLIENT_PORT))
    except OSError:
        print(f"[Error] Port {CLIENT_PORT} is busy.")
        return

    client_socket.setblocking(False)

    print(f"[Client] Sending to Proxy at {PROXY_IP}:{PROXY_PORT}")
    print(f"[Client] My return address is {CLIENT_IP}:{CLIENT_PORT}")

    packets_data = [f"Data_{i}" for i in range(TOTAL_PACKETS)]
    acked_seqs = set()
    start_time = time.time()
    
    while len(acked_seqs) < TOTAL_PACKETS:
        for seq in range(TOTAL_PACKETS):
            if seq not in acked_seqs:
                # Format: CLIENT_IP|SEQ|TIMESTAMP|DATA
                msg = f"{CLIENT_IP}|{seq}|{start_time}|{packets_data[seq]}"
                try:
                    client_socket.sendto(msg.encode('utf-8'), (PROXY_IP, PROXY_PORT))
                except BlockingIOError:
                    pass 
        

        ready = select.select([client_socket], [], [], 0.05)
        if ready[0]:
            try:
                while True:
                    data, _ = client_socket.recvfrom(4096)
                    ack_msg = data.decode('utf-8')
                    if ack_msg.startswith("ACK|"):
                        ack_seq = int(ack_msg.split('|')[1])
                        acked_seqs.add(ack_seq)
            except BlockingIOError:
                pass
            except Exception:
                pass
        
        print(f"\r[Client] Progress: {len(acked_seqs)}/{TOTAL_PACKETS}", end="")

    end_time = time.time()
    total_duration = end_time - start_time

    print(f"\n[Client] Success! All packets acknowledged.")
    print(f"[Result] Total Communication Time: {total_duration:.6f} seconds")
    client_socket.close()

if __name__ == "__main__":
    run_client()