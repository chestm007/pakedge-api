from pakedge_api import PakedgeClient
from tests.credentials import PakedgeCredentials


def test_client_context() -> None:

    with PakedgeClient(
        host=PakedgeCredentials.host,
        username=PakedgeCredentials.user,
        password=PakedgeCredentials.password
    ) as client:
        assert client.logged_in, "Should be logged in."
        assert len(ports := client.get_port_status()) == 20
        raise Exception(ports)

if __name__ == "__main__":
    test_client_context()
