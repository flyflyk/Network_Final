import socket
import time
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

SERVER_IP = '0.0.0.0'
SERVER_PORT = 5405
TOTAL_PACKETS = 100
FPS = 20

def create_dashboard(received_ids):
    grid = Table(show_header=False, show_edge=False, box=None, padding=0, expand=True)
    for _ in range(10):
        grid.add_column(justify="center")

    for row in range(10):
        cells = []
        for col in range(10):
            seq_id = row * 10 + col
            if seq_id < TOTAL_PACKETS:
                if seq_id in received_ids:
                    cells.append("[bold green]■[/bold green]")
                else:
                    cells.append("[dim]·[/dim]")
            else:
                cells.append(" ")
        grid.add_row(*cells)

    stats_text = f"[bold cyan]Status:[/bold cyan] Receiving\n" \
                 f"[bold green]Received:[/bold green] {len(received_ids)}/{TOTAL_PACKETS}\n" \
                 f"[dim]Listening on port {SERVER_PORT}[/dim]"

    layout = Layout()
    layout.split_column(
        Layout(Panel(grid, title="[bold yellow]Packet Grid[/bold yellow]", border_style="blue"), size=14),
        Layout(Panel(stats_text, title="Info", border_style="white"), size=6)
    )
    return layout

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.setblocking(False)
    
    console = Console()
    console.clear()
    console.print(f"[bold]Server started on {SERVER_IP}:{SERVER_PORT}[/bold]")
    
    received_packets = {}
    
    with Live(create_dashboard(set()), refresh_per_second=FPS, screen=True) as live:
        
        while len(received_packets) < TOTAL_PACKETS:
            try:
                data, _ = server_socket.recvfrom(4096)
                message = data.decode('utf-8')
                
                parts = message.split('|', 3)
                if len(parts) < 4:
                    continue
                    
                client_ip_from_msg = parts[0]
                seq_id = int(parts[1])
                payload = parts[3]

                if seq_id not in received_packets:
                    received_packets[seq_id] = payload
                    live.update(create_dashboard(received_packets.keys()))

                ack_msg = f"ACK|{seq_id}"
                client_addr = (client_ip_from_msg, SERVER_PORT)
                server_socket.sendto(ack_msg.encode('utf-8'), client_addr)
                
            except BlockingIOError:
                continue
            except Exception as e:
                pass
    
    print("\n" + "="*30)
    print(f"[Server] All {TOTAL_PACKETS} packets collected.")
    print(f"[Server] Entering Teardown Phase (Waiting 3s for stray packets)...")
    print("="*30)
   
    last_packet_time = time.time()
    
    while True:
        try:
            data, _ = server_socket.recvfrom(4096)
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

if __name__ == "__main__":
    run_server()