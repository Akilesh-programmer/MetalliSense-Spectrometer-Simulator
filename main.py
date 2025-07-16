from opc_server import SpectrometerOPCUAServer

if __name__ == "__main__":
    print("[INFO] Starting Spectrometer OPC-UA Server...")
    server = SpectrometerOPCUAServer()
    server.run()
