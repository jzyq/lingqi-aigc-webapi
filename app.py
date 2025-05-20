if __name__ == "__main__":
    import uvicorn
    import main

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "secret", help="The secret file which contain senstive data like appid."
    )
    parser.add_argument("--host", help="WEB API host address", default="127.0.0.1")
    parser.add_argument("--port", help="WEB API port", default=8090)
    arguments = parser.parse_args()

    try:
        uvicorn.run(main.app, host=arguments.host, port=arguments.port)
    except KeyboardInterrupt:
        pass
