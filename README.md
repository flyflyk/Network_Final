## Environment Setting

### 1. Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up envirionment variable

1.  Copy `.env.example` and rename as `.env`.
2.  Modify IP in `.env`.

## Usage

### 1. Launch Server

```bash
python server.py
```

### 2. Launch Proxy

```bash
chmod +x proxy_drop_10% proxy_delay_10% final_proxy
```

*   **10% packets dropped Proxy:**
    ```bash
    # On Windows
    proxy_drop_10%.exe
    # On Linux/macOS
    ./proxy_drop_10%
    ```

*   **10% packets delayed Proxy:**
    ```bash
    # On Windows
    proxy_delay_10%.exe
    # On Linux/macOS
    ./proxy_delay_10%
    ```

*   **Final Proxy:**
    ```bash
    # On Windows
    final_proxy.exe
    # On Linux/macOS
    ./final_proxy
    ```
### 3. Launch Client

```bash
python client.py
```