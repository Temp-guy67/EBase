from fastapi.responses import PlainTextResponse

async def read_logs():
    file_path = 'app.log'
    try:
        with open(file_path, 'r') as file:
            logs = file.read()
            return PlainTextResponse(logs)
    except FileNotFoundError:
        return PlainTextResponse("Log file not found.")
    except Exception as e:
        return PlainTextResponse(f"An error occurred: {e}")