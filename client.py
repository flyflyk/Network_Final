import socket
import time
import select
import os
from dotenv import load_dotenv
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

load_dotenv()

CLIENT_IP = os.getenv('CLIENT_IP', '127.0.0.1')
PROXY_IP = os.getenv('PROXY_IP', '127.0.0.1')
PROXY_PORT = 5405
CLIENT_PORT = 5405
TOTAL_PACKETS = 100
FPS = 30

HEART_BITMAP = [
    0, 0, 1, 1, 0, 0, 1, 1, 0, 0,  # Row 0
    0, 1, 1, 1, 1, 1, 1, 1, 1, 0,  # Row 1
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Row 2
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Row 3
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Row 4
    0, 1, 1, 1, 1, 1, 1, 1, 1, 0,  # Row 5
    0, 0, 1, 1, 1, 1, 1, 1, 0, 0,  # Row 6
    0, 0, 0, 1, 1, 1, 1, 0, 0, 0,  # Row 7
    0, 0, 0, 0, 1, 1, 0, 0, 0, 0,  # Row 8
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0   # Row 9
]

def create_client_dashboard(acked_seqs, start_time, is_finished=False, total_time=0):
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

    if is_finished:
        status_color = "bold green"
        status_text = "SENT & CONFIRMED"
        duration_ms = total_time * 1000
        footer = "[blink]Press Ctrl+C to exit[/blink]"
    else:
        status_color = "bold yellow"
        status_text = "UPLOADING..."
        duration_ms = (time.time() - start_time) * 1000
        footer = "Waiting for ACKs..."

    progress = len(acked_seqs)
    
    info_text = f"Target: {PROXY_IP}\n\n" \
                f"Status: [{status_color}]{status_text}[/{status_color}]\n" \
                f"Progress: {progress}/{TOTAL_PACKETS}\n" \
                f"Time: [bold white]{duration_ms:.0f} ms[/bold white]\n\n" \
                f"{footer}"

    layout = Layout()
    layout.split_row(
        Layout(Panel(grid, title="[magenta]Upload Status[/magenta]", border_style="magenta"), ratio=2),
        Layout(Panel(info_text, title="Client Info", border_style="white"), ratio=1)
    )
    return layout

def run_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        client_socket.bind(('0.0.0.0', CLIENT_PORT)) 
    except OSError:
        print(f"[Error] Port {CLIENT_PORT} is busy.")
        return

    client_socket.setblocking(False)
    packets_data = [str(bit) for bit in HEART_BITMAP]
    
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
            
            # Receive ACKs
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
        
        final_layout = create_client_dashboard(acked_seqs, start_time, is_finished=True, total_time=total_duration)
        live.update(final_layout)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
    client_socket.close()

if __name__ == "__main__":
    run_client()