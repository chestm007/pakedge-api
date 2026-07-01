"""Smoke test against a real Pakedge switch."""

from pakedge_api import PakedgeClient
from tests.credentials import PakedgeCredentials

HOST = PakedgeCredentials.host
USER = PakedgeCredentials.user
PASS = PakedgeCredentials.password

assert (all([HOST, USER, PASS])), "PAKEDGE_USER, PAKEDGE_PASS and PAKEDGE_HOST envvars must be set."


def test_smoke() -> None:
    print(f"Testing PakedgeClient against {HOST}...")

    # Test 1: Login
    client = PakedgeClient(HOST, username=USER, password=PASS)
    assert not client.logged_in, "Should not be logged in initially"
    client.login()
    assert client.logged_in, "Should be logged in after login()"
    print("✓ Login successful")

    # Test 2: Port status
    ports = client.get_port_status()
    assert len(ports) > 0, f"Expected ports, got {len(ports)}"
    print(f"✓ Got {len(ports)} port statuses")
    for port in ports:  # Show first 4
        link = "UP" if port.linkstatus else "DOWN"
        print(f"  Port {port.port}: pvid={port.pvid}, link={link}")

    # Test 3: Firmware info
    fw = client.get_firmware_info()
    print(f"✓ Firmware: {fw.version}, update_available={fw.update_available}")

    # Test 4: Session check
    alive = client.check_session()
    print(f"✓ Session alive: {alive}")

    # Test 5: Context manager
    with PakedgeClient(HOST, username=USER, password=PASS) as c:
        assert c.logged_in
        print("✓ Context manager login works")
    assert not c.logged_in
    print("✓ Context manager logout works")

    # Test 6: Logout
    client.logout()
    assert not client.logged_in
    print("✓ Logout successful")

    print("\nAll tests passed ♥")


if __name__ == "__main__":
    test_smoke()
