import socket
import struct
import time
import threading

PROXY_IP = "10.10.2.XXX" # <-- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100

acked_packets = set()
lock = threading.Lock()
running = True

def listen_acks(sock):
    global acked_packets, running
    
    print("ACK Listener started...")
    while running:
        try:
            sock.settimeout(1.0)
            data, _ = sock.recvfrom(1024)
            
            if len(data) >= 4:
                ack_seq = struct.unpack('!I', data[:4])[0]
                with lock:
                    if ack_seq not in acked_packets:
                        acked_packets.add(ack_seq)
        except socket.timeout:
            continue
        except Exception as e:
            if running:
                print(f"Listener Error: {e}")

def run_client():
    global running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener = threading.Thread(target=listen_acks, args=(sock,))
    listener.start()
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    round_cnt = 1
    
    while len(acked_packets) < TOTAL_PACKETS:
        with lock:
            missing = [i for i in range(1, TOTAL_PACKETS + 1) if i not in acked_packets]
        
        if not missing:
            break

        print(f"\n--- Round {round_cnt}: Sending {len(missing)} packets ---")
        burst_cnt = 4 if round_cnt == 1 else 3
        
        for seq_id in missing:
            header = struct.pack('!I', seq_id)
            payload = f"Data_for_{seq_id}".encode('utf-8')
            packet = header + payload
            for _ in range(burst_cnt):
                sock.sendto(packet, (PROXY_IP, PROXY_PORT))
                time.sleep(0.0005) 

        print(f"Waiting for ACKs... Current Progress: {len(acked_packets)}/100")
        time.sleep(2.5)
        round_cnt += 1

    print("\n[Client] All packets acknowledged!")
    running = False
    listener.join()
    sock.close()

if __name__ == "__main__":
    run_client()