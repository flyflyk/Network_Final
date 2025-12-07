import os
import socket
import time

from dotenv import load_dotenv

load_dotenv()

CLIENT_IP = os.getenv("CLIENT_IP", "127.0.0.1")
PROXY_IP = os.getenv("PROXY_IP", "127.0.0.1")
PROXY_PORT = 5405
CLIENT_PORT = 5405


def run_ping():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        sock.bind(("0.0.0.0", CLIENT_PORT))
    except OSError as e:
        print(f"[Error] Could not bind to port {CLIENT_PORT}: {e}")
        print(f"Please ensure port {CLIENT_PORT} is not in use.")
        return

    seq_num = 1
    payload_data = "PING"

    # Message format: CLIENT_IP|SEQ|TIMESTAMP|DATA
    message = f"{CLIENT_IP}|{seq_num}|{time.time()}|{payload_data}"
    encoded_message = message.encode("utf-8")

    print(f"[Ping] Sending ping to {PROXY_IP}:{PROXY_PORT}")

    start_time = time.time()
    sock.sendto(encoded_message, (PROXY_IP, PROXY_PORT))

    try:
        data, addr = sock.recvfrom(4096)
        end_time = time.time()
        ack_msg = data.decode("utf-8")

        if ack_msg.startswith("ACK|"):
            try:
                ack_seq = int(ack_msg.split("|")[1])
                if ack_seq == seq_num:
                    rtt = (end_time - start_time) * 1000  # RTT in milliseconds
                    print(f"[Ping] Received ACK from {addr}")
                    print(f"[Ping] RTT: {rtt:.2f} ms")
                else:
                    print(
                        f"[Ping] Error: Received ACK with wrong sequence number.\
                        Expected {seq_num}, got {ack_seq}."
                    )
            except (ValueError, IndexError):
                print(f"[Ping] Error: Malformed ACK received from {addr}: '{ack_msg}'")
        else:
            print(f"[Ping] Error: Received non-ACK message from {addr}: '{ack_msg}'")

    except socket.timeout:
        print("[Ping] Error: Request timed out.")
    except Exception as e:
        print(f"[Ping] An unexpected error occurred: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    run_ping()
