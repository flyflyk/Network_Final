import socket
import struct
import time
import threading

PROXY_IP = "10.10.2.XXX" # <--- Proxy server IP
PROXY_PORT = 5405
TOTAL_PACKETS = 100

acked_packets = set()
lock = threading.Lock()

def listen_acks(sock):
    global acked_packets
    while True:
        try:
            sock.settimeout(2.0)
            data, _ = sock.recvfrom(1024)
            ack_seq = struct.unpack('!I', data[:4])[0]
            with lock:
                acked_packets.add(ack_seq)
                
            if len(acked_packets) >= TOTAL_PACKETS:
                break
        except socket.timeout:
            if len(acked_packets) >= TOTAL_PACKETS:
                break
        except Exception as e:
            print(f"ACK Listener Error: {e}")
            break

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener = threading.Thread(target=listen_acks, args=(sock,))
    listener.start()
    print(f"Targeting Proxy: {PROXY_IP}:{PROXY_PORT}")
    print("Strategy: Aggressive Redundancy (Send duplicates to beat Delay/Drop)")

    # Format: [SeqID (4 bytes)][Data (string)]
    round_cnt = 1
    while len(acked_packets) < TOTAL_PACKETS:
        with lock:
            missing = [i for i in range(1, TOTAL_PACKETS + 1) if i not in acked_packets]
        if not missing:
            break

        print(f"--- Round {round_cnt}: Sending {len(missing)} packets ---")
        
        for seq_id in missing:
            # Construct packet
            header = struct.pack('!I', seq_id)
            payload = f"Data_for_{seq_id}".encode('utf-8')
            packet = header + payload
            
            # === Strategy ===
            # Send duplicates in the first round to overcome initial losses
            burst_count = 2 if round_cnt == 1 else 1
            
            for _ in range(burst_count):
                sock.sendto(packet, (PROXY_IP, PROXY_PORT))
                time.sleep(0.002) 
        time.sleep(1.0)
        round_cnt += 1

    listener.join()
    print(f"Success! All {TOTAL_PACKETS} packets acked.")
    sock.close()

if __name__ == "__main__":
    run_client()