#!/usr/bin/env micropython

import json
import struct
import time

from binascii import unhexlify
from ucryptolib import aes
from hashlib import md5
from socket import getaddrinfo, socket, AF_INET, SOCK_DGRAM

IP = "foo"
TOKEN = unhexlify("bar")

"""
TODO:
    - device list
    - use logging
    - load configuration from file
"""

class Request:
    def __init__(self, unknown, device_id, stamp, token, payload):
        self.unknown = unknown
        self.device_id = device_id
        self.stamp = stamp
        self.token = token
        self.payload = payload

        self.key = md5(self.token).digest()
        self.iv = md5(self.key + self.token).digest()
        print("Key: ", self.key)
        print("IV: ", self.iv)

    def _get_header(self, payload):
        print("Device ID: ", self.device_id)
        print("Stamp: ", self.stamp)
        print("Token: ", self.token)
        print("Length: ", len(payload) + 32)
        return bytearray(
            struct.pack(
                "!BBHIII16s",
                0x21, 0x31,  # Magic Number
                # FIXME: Make this a constant.
                len(payload) + 32,  # Packet Length,
                self.unknown, # Unknown
                self.device_id,  # Device ID
                self.stamp,  # Stamp
                # FIXME: Remove type conversion.
                self.token,  # Token
            )
        )

    @staticmethod
    def _pkcs7_pad(payload, block_size):
        pad_length = block_size - (len(payload) % block_size)
        print("Pad Length: ", pad_length)
        # pad = chr(amount_to_pad)
        # return text + pad * amount_to_pad
        return payload + bytes(pad_length for _ in range(pad_length))

    def _encrypt_payload(self):
        print("Payload: ", self.payload)

        # padded_payload = self._pkcs7_pad(self.payload, 128)
        padded_payload = self._pkcs7_pad(self.payload, 16)  # FIXME: Make this a constant
        print("Padded Payload: ", padded_payload)

        cipher = aes(self.key, 2, self.iv)  # FIXME: Use constant
        enc_payload = cipher.encrypt(padded_payload)
        print("Enc Payload: ", enc_payload)

        # FIXME: Rename for consistnecy.
        return enc_payload

    def encode(self):
        # FIXME: Refactor.
        if not self.payload:
            packet = self._get_header(b'')
            print("No payload, skipping encryption")
            return packet

        enc_payload = self._encrypt_payload()
        packet = self._get_header(enc_payload)
        print("Init Header: ", packet)
        packet += enc_payload

        checksum = md5(packet).digest()
        print("Checksum: ", checksum)

        # FIXME: Update the relevant bytes directly.
        for i in range(0, 16):
            packet[i + 16] = checksum[i]
        print("Updated Packet: ", packet)
        return packet


class Response:
    def __init__(self, response, token):
        # FIXME: Share this between Request and Response.
        self.token = token
        self.key = md5(self.token).digest()
        self.iv = md5(self.key + self.token).digest()

        # FIXME: Only get the relevant bytes.
        # FIXME: Unpack head, decrypt the rest.
        print("Response header: ", struct.unpack('!2sHIII16s', response[:32]))
        _, _, _, self.device_id, self.stamp, _ = struct.unpack('!2sHIII16s', response)

        self.payload = response[32:]  # FIXME: Make this a constant.
        print("Response payload: ", self.payload)

    def decode(self):
        cipher = aes(self.key, 2, self.iv)  # FIXME: Use constant
        dec_payload = cipher.decrypt(self.payload)
        print("Decrypted payload: ", dec_payload)

        unpadded_payload = self._pkcs7_unpad(dec_payload)
        print("Unpadded payload: ", unpadded_payload)

        return json.loads(unpadded_payload.decode('utf-8'))

    @staticmethod
    def _pkcs7_unpad(payload):
        if len(payload) % 16:  # FIXME: Make block size a constant/argument.
            return payload

        pad_len = payload[-1]  # FIXME: Make this consistent with the padder.
        return payload[:-pad_len]



class Device:
    def __init__(self, ip, token):
        self.ip = ip
        self.token = token

        # FIXME: Set the port as variable.
        addr = getaddrinfo(self.ip, 54321, 0, SOCK_DGRAM)
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.settimeout(5)  # FIXME: Make timeout configurable.
        self.socket.connect(addr[0][-1])

        hello = Request(
                unknown=0xffffffff,
                device_id=0xffffffff,
                stamp=0xffffffff,
                # FIXME: Remove type conversion.
                token=str(0xffffffff),
                payload='',
        )
        self.stamp = 0 # FIXME
        self.device_id = 0xffffffff  # FIXME
        # response = Response(self._get_response(hello.encode()))
        # self.device_id = response.device_id
        # self.stamp = response.stamp
        # print("Stamp: ", response.stamp)

    def send_command(self, command):
        print("--------------------------------------------------------------------------------")  # FIXME
        print("Command: ", command)

        # FIXME: Add ID automatically.
        # FIXME: Is the trailing byte needed?
        payload = bytearray(json.dumps(command).encode("utf-8") + b"\x00")

        self.stamp += 1
        request = Request(
                unknown=0x00000000,
                device_id=self.device_id,
                stamp=self.stamp,
                token=self.token,
                payload=payload,
        )
         response = Response(response=self._get_response(request.encode()), token=self.token)
        print("Command response: ", response)

        # FIXME: Check return code.
        # {'id': 1, 'result': ['ok'], 'exe_time': 10}
        return response.decode()

    def close(self):
        self.socket.close()  # FIXME: Do this automatically?

    def _get_response(self, packet):
        print("Writing to socket: ", packet)
        x = self.socket.write(packet)  # FIXME: Ensure all data is written.

        response = self.socket.recv(4096)  # FIXME: Read all data.
        print("Raw Response: ", response)

        return response


test = Device(IP, TOKEN)
r = test.send_command({"id": 1, "method": "set_power", "params": ["off"]})
print("Parsed response:", r)
#test.send_command({'id': 1, 'method': 'miIO.info', 'params': []})
test.close()


