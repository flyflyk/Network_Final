## Setup

### 1. Install Dependencies

```bash
sudo apt update
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Next time you only need to execute:
```bash
source venv/bin/activate
```

### 2. Configure Environment

Copy the example `.env.example` file to `.env` and modify it with your IP addresses.

```bash
cp .env.example .env
```

**`.env` file:**
```dotenv
CLIENT_IP=127.0.0.1
PROXY_IP=127.0.0.1
```

## Usage

Run the services in separate terminals in the following order.

### 1. Start Server

The server listens for UDP packets on port `5405`.

```bash
python server.py
```

### 2. Start Proxy

The proxy forwards packets between the client and server. The proxy executables may require execute permissions (`chmod +x <filename>`).

*   `./proxy_drop_10%` (Drops 10% of packets)
*   `./proxy_delay_10%` (Delays 10% of packets)
*   `./final_proxy` (Final version)

*(Use `.exe` extension on Windows, e.g., `proxy_drop_10%.exe`)*

### 3. Start Client

The client reads the `.env` config and sends 100 packets to the proxy.

```bash
python client.py
```

### 4. Run Ping Test

`ping.py` sends a single packet to measure the Round Trip Time (RTT).

```bash
python ping.py
```
