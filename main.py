import serial
import cbor2
from cobs import cobs
import zlib
import time

def mock_device(port, commands_responses_mapping):
    with serial.Serial(port, 115200, timeout=1) as ser:
        
        buffer = bytearray()
        while True:  # The device should listen indefinitely.
            byte = ser.read(1)
            
            if byte == b'\x00':  # SOF or EOF
                if len(buffer) > 0:  # If buffer is not empty, we have received a full message.
                    
                    # COBS Decode
                    payload_with_crc32 = cobs.decode(buffer)
                    
                    # Extract CBOR payload and CRC32
                    cbor_encoded = payload_with_crc32[:-4]
                    received_crc32_bytes = payload_with_crc32[-4:]
                    
                    # Verify CRC32
                    calculated_crc32_bytes = zlib.crc32(cbor_encoded).to_bytes(4, 'big')
                    if received_crc32_bytes != calculated_crc32_bytes:
                        print("CRC32 mismatch!")
                    else:
                        # CBOR Decode
                        message = cbor2.loads(cbor_encoded)
                        print(f"Received: {message}")
                        
                        response = commands_responses_mapping.get(message, "Unknown command")
                        
                        # Mock some delay if needed
                        time.sleep(0.5) 
                        
                        print('Sending response:', response)
                        send_message(ser, response)
                        
                    # Clear the buffer for the next message
                    buffer = bytearray()
                    
                # If buffer is empty, this is the start of a new message. Just continue to read more bytes.
                continue
            
            else:
                buffer.extend(byte)


def send_message(ser, message):
    # Encode the message using CBOR
    cbor_encoded = cbor2.dumps(message)
    
    # Calculate CRC32
    crc32 = zlib.crc32(cbor_encoded)
    crc32_bytes = crc32.to_bytes(4, 'big')  # Convert CRC32 to 4 bytes
    
    # Append CRC32 to CBOR payload
    payload_with_crc32 = cbor_encoded + crc32_bytes
    
    # COBS encode the payload
    cobs_encoded = cobs.encode(payload_with_crc32)
    
    # Add SOF and EOF, then send the message
    frame = b'\x00' + cobs_encoded + b'\x00'
    ser.write(frame)
    print(f"Sent: {message} Encoded Frame: {frame}")


commands_responses_mapping = {
    #powerSupply
    "SET VOLTAGE 5": "Voltage Set: OK",
    "SET CURRENT 0.5": "Current Set: OK",
    "SET OUTPUT OFF": "Output Set: OFF",
    "SET OUTPUT ON": "Output Set: ON",
    "GET POWER CONSUMTION": "0.2",
    #controller
    "START": "started: true",
    "DUT INSERTED": "inserted: true",
    "GET 5V":"5",
    "GET 3V":"3.3",
    "GET LED brightness ON":"0.3",
    "GET LED brightness OFF":"0",
    "GET IR LED brightness ON":"2",
    "GET IR LED brightness OFF":"0",
    "SEND IR COMMAND":"ir command sent",
    #chip
    "GET MAC":"mac: FF:02:AF:9F:4C:00",
    "PING CHIP": "ping received",
    "GET TOUCH SENSOR DATA":"touch sensor data: OK",
    "GET RT410 CONNETION STATUS":"rt410 status: OK",
    "PERFORM DISPLAY SOCKET TEST": "socket test: passed",
    "TURN ON LED":"led status: ON",
    "TURN OFF LED":"led status: OFF",
    "TURN ON IR LEDS":"IR LEDS: ON",
    "TURN OFF IR LEDS":"IR LEDS: OFF",
    "GET IR SENSOR STATUS":"ir command received",
    "ENCRYPT CHIP":"chip encrypted",
    "GET ENCRYPTION STATUS":"encryption status: OK",
    "{0:[24]}":"-50" # wifi rssi
}

mock_device("/dev/pts/5", commands_responses_mapping)  # Change the port as needed
