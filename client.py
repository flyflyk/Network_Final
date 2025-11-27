import socket
import time
import select
import os
from dotenv import load_dotenv
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

load_dotenv()

CLIENT_IP = os.getenv('CLIENT_IP', '127.0.0.1')
PROXY_IP = os.getenv('PROXY_IP', '127.0.0.1')
PROXY_PORT = 5405
CLIENT_PORT = 5405
TOTAL_PACKETS = 100
FPS = 20

def create_client_dashboard(acked_seqs, start_time):
    grid = Table(show_header=False, show_edge=False, box=None, padding=0, expand=True)
    for _ in range(10):
        grid.add_column(justify="center")

    for row in range(10):
        cells = []
        for col in range(10):
            seq_id = row * 10 + col
            if seq_id < TOTAL_PACKETS:
                if seq_id in acked_seqs:
                    cells.append("[bold green]✔[/bold green]")
                else:
                    cells.append("[dim red]·[/dim red]")
            else:
                cells.append(" ")
        grid.add_row(*cells)

    duration = time.time() - start_time
    stats = f"[bold]Sending to:[/bold] {PROXY_IP}\n" \
            f"[bold]Progress:[/bold] {len(acked_seqs)}/{TOTAL_PACKETS}\n" \
            f"[bold]Time Elapsed:[/bold] {duration * 1000:.0f} ms"

    return Panel(grid, title=f"Client ACK Status ({stats})", border_style="magenta")

def run_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        client_socket.bind(('0.0.0.0', CLIENT_PORT)) 
    except OSError:
        print(f"[Error] Port {CLIENT_PORT} is busy.")
        return

    client_socket.setblocking(False)

    packets_data = [f"Data_{i}" for i in range(TOTAL_PACKETS)]
    acked_seqs = set()
    start_time = time.time()
    
    console = Console()
    console.clear()
    
    with Live(create_client_dashboard(acked_seqs, start_time), refresh_per_second=FPS, screen=True) as live:
        
        while len(acked_seqs) < TOTAL_PACKETS:
            for seq in range(TOTAL_PACKETS):
                if seq not in acked_seqs:
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
                            live.update(create_client_dashboard(acked_seqs, start_time))
                except BlockingIOError:
                    pass
                except Exception:
                    pass

            live.update(create_client_dashboard(acked_seqs, start_time))

    end_time = time.time()
    total_duration = end_time - start_time

    console.print(f"\n[bold green][Client] Success! All packets acknowledged.[/bold green]")
    console.print(f"[bold yellow][Result] Total Communication Time: {total_duration * 1000:.2f} ms[/bold yellow]")
    client_socket.close()

if __name__ == "__main__":
    run_client()