import asyncio
class ConferenceServer:
    def __init__(self, server_ip, main_port):
        self.server_ip = server_ip
        self.main_port = main_port
        self.conferences = {}  # Dictionary to store active conferences

    async def handle_client(self, reader, writer):
        """Handle client requests for creating, joining, or canceling conferences."""
        async with reader, writer:
            while True:
                request = await reader.readline()
                if not request:
                    break
                request = request.decode().strip()
                print(f"Received request: {request}")

                if 'create' in request:
                    # Extract conference ID from request or generate one
                    conference_id = int(request.split()[1])
                    port = 8080 + conference_id  # Simple port allocation strategy
                    self.conferences[conference_id] = port
                    await writer.write(f"Conference {conference_id} created on port {port}\n".encode())
                elif 'join' in request:
                    conference_id = int(request.split()[1])
                    if conference_id in self.conferences:
                        await writer.write("Welcome to the conference\n".encode())
                    else:
                        await writer.write("Conference not found\n".encode())
                elif 'cancel' in request:
                    conference_id = int(request.split()[1])
                    if conference_id in self.conferences:
                        del self.conferences[conference_id]
                        await writer.write("Conference canceled\n".encode())
                    else:
                        await writer.write("Conference not found\n".encode())

    async def start(self):
        """Start the server."""
        server = await asyncio.start_server(self.handle_client, self.server_ip, self.main_port)
        async with server:
            await server.serve_forever()


if __name__ == '__main__':
    server = ConferenceServer('127.0.0.1', 5555)
    asyncio.run(server.start())