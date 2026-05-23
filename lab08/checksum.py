def calculate_checksum(data):
    s = 0
    for i in range(0, len(data), 2):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        s += (b1 << 8) + b2
    while (s >> 16 != 0):
        s = (s & 0xFFFF) + (s >> 16)
    return ~s

def verify_checksum(data, chksm):
    actual_chksm = calculate_checksum(data)
    if actual_chksm != chksm:
        return False
    return True

def test_success():
    # test on data with even number of bytes
    data_1 = bytearray(2)
    data_1[0] = 0x12
    data_1[1] = 0x34
    chk_1 = calculate_checksum(data_1)
    verdict = verify_checksum(data_1, chk_1)
    assert(verdict)
    print("test_success_1 passed: checksum of", data_1, "equals", chk_1)

    # test on data with odd number of bytes
    data_2 = bytearray(5)
    data_2[0] = 0x12
    data_2[1] = 0x34
    data_2[2] = 0x56
    data_2[3] = 0x78
    data_2[4] = 0x9A
    chk_2 = calculate_checksum(data_2)
    verdict_2 = verify_checksum(data_2, chk_2)
    assert(verdict_2)
    print("test_success_2 passed: checksum of", data_2, "equals", chk_2)

def test_fail():
    # test on data with even number of bytes
    data_1 = bytearray(2)
    data_1[0] = 0x12
    data_1[1] = 0x34
    chk_1 = calculate_checksum(data_1)
    data_1[1] ^= 0b00001000 # simulate data corruption
    verdict = verify_checksum(data_1, chk_1)
    assert(not verdict)
    print("test_fail_1 passed: checksum of corrupted", data_1, "does NOT equal", chk_1)

    # test on data with odd number of bytes
    data_2 = bytearray(5)
    data_2[0] = 0x12
    data_2[1] = 0x34
    data_2[2] = 0x56
    data_2[3] = 0x78
    data_2[4] = 0x9A
    chk_2 = calculate_checksum(data_2)
    data_2[3] ^= 0b00001000 # simulate data corruption
    verdict_2 = verify_checksum(data_2, chk_2)
    assert(not verdict_2)
    print("test_fail_2 passed: checksum of corrupted", data_2, "does NOT equal", chk_2)

if __name__ == "__main__":
    test_success()
    test_fail()
