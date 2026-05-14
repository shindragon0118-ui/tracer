from bootstrap.container import Container
import os

def main():
    app = Container().build_app()
    port = int(os.environ.get("PORT", 7860))  # PORT라는 환경변수가 있으면 그 값을 쓰고, 없으면 7860을 가져옴
    app.launch(
        server_name="0.0.0.0",  # 외부 접속 허용
        server_port=port
    )

if __name__ == "__main__":
    main()