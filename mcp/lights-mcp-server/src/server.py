import traceback, argparse, uvicorn, os
from mcp.server.fastmcp import FastMCP
import serial, time, logging
import serial.tools.list_ports
from typing import Optional
from .models.auduino import LightInfo, FetchLightsInfoOutput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Auduino MCP Server")

def _find_arduino_port():
    """
    自動尋找 Arduino 連接埠
    在 Linux 上尋找 ttyACM*，在 macOS 上尋找 cu.usbmodem*
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Linux: ttyACM0, ttyACM1, etc.
        if "ttyACM" in port.device:
            return port.device
        # macOS: cu.usbmodem*, cu.usbserial*, etc.
        if "cu.usbmodem" in port.device or "cu.usbserial" in port.device:
            return port.device
    return None

led_count = 3
BAUD_RATE = 9600

# 支援兩種連接模式：
# 1. 直接連接串口（Linux 或 macOS host 直接運行）
# 2. 通過 TCP 連接（macOS + Docker，使用 socat 轉發）
USE_TCP = os.getenv("SERIAL_USE_TCP", "false").lower() == "true"
TCP_HOST = os.getenv("SERIAL_TCP_HOST", "host.docker.internal")
TCP_PORT = int(os.getenv("SERIAL_TCP_PORT", "5555"))

if USE_TCP:
    # 使用 TCP 連接模式（適用於 macOS + Docker）
    try:
        logger.info(f"Connecting to Arduino via TCP: {TCP_HOST}:{TCP_PORT}")
        # 使用 socket:// URL 來建立 TCP 連接
        ser = serial.serial_for_url(f"socket://{TCP_HOST}:{TCP_PORT}", timeout=1)
        time.sleep(2)
        initial_message = ser.readline().decode('utf-8').strip()
        logger.info(f"Connect to Arduino via TCP success: {initial_message}")
    except Exception as e:
        logger.error(
            f"Connect to Arduino via TCP ({TCP_HOST}:{TCP_PORT}) error.\n"
            f"Please make sure:\n"
            f"> socat is running on your host machine\n"
            f"> Command: socat TCP-LISTEN:{TCP_PORT},reuseaddr,fork /dev/cu.usbmodem*,raw,echo=0\n"
            f"Detail error log:\n"
            f"{e}"
        )
        exit()
else:
    # 使用直接串口連接模式（適用於 Linux + Docker 或 host 直接運行）
    PORT = os.getenv("SERIAL_PORT") or _find_arduino_port()
    
    if PORT is None:
        logger.error(
            "No Arduino device found. Please ensure your Arduino is connected "
            "and the necessary drivers are installed."
        )
        exit()

    try:
        logger.info(f"Connecting to Arduino via serial port: {PORT}")
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        # 等待 2 秒，讓 Arduino 完成重置並準備就緒
        time.sleep(2) 
        # 讀取 Arduino 啟動時發送的 "Arduino Ready." 訊息，清空緩衝區
        initial_message = ser.readline().decode('utf-8').strip()
        logger.info(f"Connect to Arduino({PORT}) success: {initial_message}")

    except serial.SerialException as e:
        logger.error(
            f"Connect to Arduino({PORT}) error, please check:\n"
            f"> Did Arduino connect to your computer?\n"
            f"> Is the port name `{PORT}` correct?\n"
            f"Detail error log:\n"
            f"{e}"
        )
        exit()


@mcp.tool(name="get_lights_statuses", description="Get information of all lights, or a specific light if ID is provided.")
async def get_lights_statuses(light_id: Optional[int] = None) -> str:
    """
    Get the information of all lights, or a specific light if ID is provided.
    Generally call this tool to check the status of each light after change the brightness of it.

    Args:
        light_id: Optional. The ID of the light to fetch. If not provided, returns information for all lights.
    """
    try:
        if light_id is not None and not (0 <= light_id < led_count):
            return f"The light_id must be a integer between [0-{led_count - 1}], got {light_id}"

        ser.write(b's\n')
        
        response = ser.readline().decode('utf-8').strip()
        
        all_infos = FetchLightsInfoOutput()
        if response and response.startswith('S,'):
            parts = response.split(',')
            
            status = [int(p) for p in parts[1:]]
            for i, val_255 in enumerate(status):
                # ----- 將 0-255 的值反向映射回 0-100 -----
                val_100 = int(round((val_255 / 255.0) * 100))
                all_infos.infos.append(
                    LightInfo(
                        light_id=i,
                        brightness=val_100
                    )
                )
        else:
            return f"Got invaild response from Arduino: '{response}'"
        
        if light_id is not None:
            for light_info in all_infos.infos:
                if light_info.light_id == light_id:
                    return light_info.model_dump_json()
            # This part should not be reached if light_id validation is correct
            return f"Light with ID {light_id} not found."
        else:
            return all_infos.model_dump_json()
    
    except Exception as e:
        traceback.print_exc()
        return (
            f"❌ Fetch the information of lights error, error log as below:\n"
            f"```\n{e}\n```\n\n"
            )


@mcp.tool(name="get_light_count", description="Get the amount of lights.")
async def get_led_count() -> str:
    """Get the amount of lights that current system has.

    If you got the error message of something like: `The light_id must be a integer between [0-0]`, means the system still don't know how many lights is there, you should call this tool to check the amount first.
    """
    global led_count

    ser.write(b'i\n') # 發送 'i' 指令
    response = ser.readline().decode('utf-8').strip()

    try:
        if response and response.startswith('I,'):
            # Arduino 回傳範例： 'I,3'
            count = int(response.split(',')[1])
            led_count = count
            return str(count)
        else:
            return f"Got invaild response from Arduino: '{response}'"

    except Exception as e:
        traceback.print_exc()
        return (
            f"❌ Get amount of lights error, error log as below:\n"
            f"```\n{e}\n```\n\n"
            )


@mcp.tool(name="set_light_brightness", description="Set specific light's brightness.")
async def set_light_brightness(light_id: int, brightness: int):
    """
    Set brightness value of specific light.
    Always use this tool to change the brightness of the light.

    Args:
        light_id: The ID of the light which is going to set brightness. It must be a integer and start with 0. Usually, user says `the first light` means the light of `light_id=0`; `the third light` means the light of `light_id=2`.
        brightness: The percentage of brightness value, must be a integer between [0-100], `0` means turn off, `100` means the maximum brightness.
    """
    try:
        if not (0 <= light_id < led_count):
            return f"The light_id must be a integer between [0-{led_count - 1}], got {light_id}"

        if not (0 <= brightness <= 100):
            return f"The brightness value must be a integer between [0-100], got {brightness}"
        

        # ----- 將 0-100 的值映射到 0-255 -----
        # 使用 round() 確保四捨五入，結果更精確
        brightness_255 = int(round((brightness / 100.0) * 255))

        command = f"<{light_id},{brightness_255}>\n"
        ser.write(command.encode('utf-8'))
        return f"The bightness of light-{light_id} is set to {brightness}%"
    except Exception as e:
        traceback.print_exc()
        return (
            f"❌ Set the brightness of light-{light_id} error, error log as below:\n"
            f"```\n{e}\n```\n\n"
            )


@mcp.tool(name="turn_on_light", description="Turn specific light on.")
async def turn_on_light(light_id: int):
    """
    Turn on specific light to the maximum brightness (100%).

    Args:
        light_id: The ID of the light which is going to be turned on. It must be a integer and start with 0.
    """
    try:
        if not (0 <= light_id < led_count):
            return f"The light_id must be a integer between [0-{led_count - 1}], got {light_id}"

        brightness_255 = 255

        command = f"<{light_id},{brightness_255}>\n"
        ser.write(command.encode('utf-8'))
        return f"The bightness of light-{light_id} is set to 100%"
    except Exception as e:
        traceback.print_exc()
        return (
            f"❌ Turn on light-{light_id} error, error log as below:\n"
            f"```\n{e}\n```\n\n"
            )


@mcp.tool(name="turn_off_light", description="Turn specific light off.")
async def turn_off_light(light_id: int):
    """
    Turn off specific light (set brightness to 0%).

    Args:
        light_id: The ID of the light which is going to be turned off. It must be a integer and start with 0.
    """
    try:
        if not (0 <= light_id < led_count):
            return f"The light_id must be a integer between [0-{led_count - 1}], got {light_id}"

        brightness_255 = 0

        command = f"<{light_id},{brightness_255}>\n"
        ser.write(command.encode('utf-8'))
        return f"The bightness of light-{light_id} is set to 0%"
    except Exception as e:
        traceback.print_exc()
        return (
            f"❌ Turn off light-{light_id} error, error log as below:\n"
            f"```\n{e}\n```\n\n"
            )


@mcp.tool(name="blink_light", description="Make a specific light blink a given number of times and interval.")
async def blink_light(light_id: int, times: int, interval: float = 0.5):
    """
    Make a specific light blink a given number of times.

    Args:
        light_id: The ID of the light to blink.
        times: The number of times to blink the light.
        interval: The time in seconds between each on/off state change. Defaults to 0.5.
    """
    try:
        if not (0 <= light_id < led_count):
            return f"The light_id must be an integer between [0-{led_count - 1}], got {light_id}"
        if not (times > 0):
            return f"The times must be a positive integer, got {times}"
        if not (interval > 0):
            return f"The interval must be a positive float, got {interval}"

        for _ in range(times):
            # Turn on
            ser.write(f"<{light_id},255>\n".encode('utf-8'))
            time.sleep(interval)
            # Turn off
            ser.write(f"<{light_id},0>\n".encode('utf-8'))
            time.sleep(interval)
        
        return f"Light-{light_id} blinked {times} times successfully."
    except Exception as e:
        traceback.print_exc()
        return (
            f"❌ Blink light-{light_id} error, error log as below:\n"
            f"```\n{e}\n```\n\n"
            )
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MCP Streamable HTTP based server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP to listen on")
    parser.add_argument("--port", type=int, default=2828, help="Port to listen on")
    args = parser.parse_args()

    # Start the server with Streamable HTTP transport
    uvicorn.run(mcp.streamable_http_app, host=args.host, port=args.port)