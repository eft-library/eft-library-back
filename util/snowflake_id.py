import time
import threading

class SnowflakeGenerator:
    def __init__(self, datacenter_id=0, worker_id=0):
        self.datacenter_id = datacenter_id & 0x1F   # 5 bits
        self.worker_id = worker_id & 0x1F           # 5 bits
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

        # 비트 쉬프트 기준
        self.worker_id_shift = 12
        self.datacenter_id_shift = 17
        self.timestamp_shift = 22
        self.sequence_mask = 0xFFF  # 12 bits sequence

        # 기준 시간 (예: 2020-01-01)
        self.epoch = 1577836800000  # 밀리초 단위 timestamp

    def _timestamp(self):
        return int(time.time() * 1000)

    def generate_id(self):
        with self.lock:
            timestamp = self._timestamp()

            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Rejecting requests until %d." % self.last_timestamp)

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.sequence_mask
                if self.sequence == 0:
                    # 시퀀스 오버플로우, 다음 밀리초까지 대기
                    while timestamp <= self.last_timestamp:
                        timestamp = self._timestamp()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            snowflake_id = (
                ((timestamp - self.epoch) << self.timestamp_shift) |
                (self.datacenter_id << self.datacenter_id_shift) |
                (self.worker_id << self.worker_id_shift) |
                self.sequence
            )

            return snowflake_id
