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

def create_dashboard(received_ids, status_log):
    # Packet grid
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

    # Info panel
    progress = len(received_ids)
    color = "green" if progress == TOTAL_PACKETS else "yellow"
    
    info_content = f"[bold cyan]Server Status[/bold cyan]\n" \
                   f"Port: {SERVER_PORT}\n\n" \
                   f"Progress: [{color}]{progress}/{TOTAL_PACKETS}[/{color}]\n" \
                   f"{'-'*20}\n" \
                   f"{status_log}"

    # Layout: Left right split
    layout = Layout()
    layout.split_row(
        Layout(Panel(grid, title="[bold yellow]Packet Grid (10x10)[/bold yellow]", border_style="blue"), ratio=2),
        Layout(Panel(info_content, title="[bold white]System Log[/bold white]", border_style="white"), ratio=1)
    )
    return layout

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.setblocking(False)
    
    console = Console()
    console.clear()
    
    received_packets = {}
    current_log = "Waiting for connection..."
    
    # Live control
    with Live(create_dashboard(set(), current_log), refresh_per_second=FPS, screen=True) as live:
        
        # Receive Phase
        current_log = "[bold yellow]Receiving Packets...[/bold yellow]"
        live.update(create_dashboard(received_packets.keys(), current_log))
        
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
                    live.update(create_dashboard(received_packets.keys(), current_log))

                ack_msg = f"ACK|{seq_id}"
                client_addr = (client_ip_from_msg, SERVER_PORT)
                server_socket.sendto(ack_msg.encode('utf-8'), client_addr)
                
            except BlockingIOError:
                continue
            except Exception:
                pass
        
        # Teardown Phase
        current_log = "[bold magenta]Collection Complete![/bold magenta]\n" \
                      "Entering Teardown Phase...\n" \
                      "Handling stray packets..."
        live.update(create_dashboard(received_packets.keys(), current_log))
        
        last_packet_time = time.time()
        
        while True:
            try:
                data, _ = server_socket.recvfrom(4096)
                last_packet_time = time.time()
                
                message = data.decode('utf-8')
                parts = message.split('|', 3)
                if len(parts) < 4: continue

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
                break
        
        # Verification Phase
        sorted_packets = sorted(received_packets.items(), key=lambda x: x[0])
        
        final_msg = f"[bold green]✔ All {len(sorted_packets)} Packets Sorted![/bold green]\n\n" \
                    f"System Halted.\n" \
                    f"[blink]Press Ctrl+C to exit[/blink]"
        
        live.update(create_dashboard(received_packets.keys(), final_msg))
        
        # Keep the final screen
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run_server()