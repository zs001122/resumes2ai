from common import assert_status, client, print_json


def main() -> None:
    with client() as http:
        response = http.get("/api/health")
        assert_status(response, 200)
        print_json("health", response.json())


if __name__ == "__main__":
    main()
