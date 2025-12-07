import socket
import time

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

SERVER_IP = "0.0.0.0"
SERVER_PORT = 5405
TOTAL_PACKETS = 100
FPS = 30


def create_dashboard(received_packets, status_log):
    grid = Table(
        show_header=False, show_edge=False, box=None, padding=(0, 0), expand=False
    )

    for _ in range(10):
        grid.add_column(justify="center", width=2)

    for row in range(10):
        cells = []
        for col in range(10):
            seq_id = row * 10 + col

            if seq_id < TOTAL_PACKETS:
                if seq_id in received_packets:
                    pixel_val = received_packets[seq_id]
                    if pixel_val == "1":
                        cells.append("[red]██[/red]")
                    else:
                        cells.append("[grey23]██[/grey23]")
                else:
                    cells.append("[dim]··[/dim]")
            else:
                cells.append("  ")
        grid.add_row(*cells)

    count = len(received_packets)
    progress_color = "green" if count == TOTAL_PACKETS else "yellow"

    info_content = (
        f"[bold cyan]Server Status (SCRAMBLED MODE)[/bold cyan]\n"
        f"Port: {SERVER_PORT}\n\n"
        f"Pixels: [{progress_color}]{count}/{TOTAL_PACKETS}[/{progress_color}]\n"
        f"{'-' * 20}\n"
        f"{status_log}"
    )

    grid_panel_content = Align.center(grid, vertical="middle")
    layout = Layout()
    layout.split_row(
        Layout(
            Panel(
                grid_panel_content,
                title="[bold yellow]Image Reconstruction (Arrival Order)[/bold yellow]",
                border_style="blue",
            ),
            ratio=2,
        ),
        Layout(
            Panel(
                info_content,
                title="[bold white]System Log[/bold white]",
                border_style="white",
            ),
            ratio=1,
        ),
    )
    return layout


def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.setblocking(False)

    console = Console()
    console.clear()

    received_packets = {}  # Maps arrival_index -> payload
    seen_seqs = set()  # Tracks actual seq_ids to handle ACKs correctly
    arrival_index = 0

    current_log = "Waiting for stream..."

    with Live(
        create_dashboard(received_packets, current_log),
        refresh_per_second=FPS,
        screen=True,
    ) as live:
        # Receiving phase
        current_log = "[bold yellow]Reconstructing (Ignoring Order)...[/bold yellow]"
        live.update(create_dashboard(received_packets, current_log))

        while len(received_packets) < TOTAL_PACKETS:
            try:
                data, _ = server_socket.recvfrom(4096)
                message = data.decode("utf-8")

                parts = message.split("|", 3)
                if len(parts) < 4:
                    continue

                client_ip_from_msg = parts[0]
                seq_id = int(parts[1])
                payload = parts[3]

                # CRITICAL CHANGE: Ignore seq_id for placement, use arrival_index
                if seq_id not in seen_seqs:
                    seen_seqs.add(seq_id)
                    received_packets[arrival_index] = payload
                    arrival_index += 1
                    live.update(create_dashboard(received_packets, current_log))

                # Still ACK the correct seq_id so client continues
                ack_msg = f"ACK|{seq_id}"
                client_addr = (client_ip_from_msg, SERVER_PORT)
                server_socket.sendto(ack_msg.encode("utf-8"), client_addr)

            except BlockingIOError:
                continue
            except Exception:
                pass

        # Verification phase
        current_log = (
            "[bold red]Image Complete (Scrambled)![/bold red]\nVerifying Integrity..."
        )
        live.update(create_dashboard(received_packets, current_log))

        last_packet_time = time.time()
        while True:
            try:
                data, _ = server_socket.recvfrom(4096)
                last_packet_time = time.time()
                message = data.decode("utf-8")
                parts = message.split("|", 3)
                if len(parts) < 4:
                    continue

                ack_msg = f"ACK|{int(parts[1])}"
                server_socket.sendto(ack_msg.encode("utf-8"), (parts[0], SERVER_PORT))
            except Exception:
                pass

            if time.time() - last_packet_time > 2.0:
                break

        final_msg = (
            "[bold red]✘ RECONSTRUCTION SCRAMBLED[/bold red]\n\n"
            "Sorted: 0%\n"
            "Loss: 0%\n\n"
            "[blink]Press Ctrl+C to exit[/blink]"
        )

        live.update(create_dashboard(received_packets, final_msg))

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    run_server()
