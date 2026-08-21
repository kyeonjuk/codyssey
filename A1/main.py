prompts = [
    {
        "title": "보고서 작성 도우미",
        "content": "주어진 내용을 대학생 수준의 보고서 형식으로 정리해주세요.",
        "category": "텍스트 생성",
        "favorite": False
    },
    {
        "title": "게임 배경 이미지 생성",
        "content": "따뜻한 분위기의 판타지 게임 배경 이미지를 생성해주세요.",
        "category": "이미지 생성",
        "favorite": False
    },
    {
        "title": "뉴스 요약 도우미",
        "content": "주어진 뉴스 내용을 핵심만 간단하고 정확하게 요약해주세요.",
        "category": "자동화",
        "favorite": False
    }
]

def show_menu():
    print("\n=== 나만의 AI 프롬프트 관리 ===")
    print("1. 프롬프트 추가")
    print("2. 프롬프트 목록")
    print("3. 카테고리별 조회")
    print("4. 프롬프트 검색")
    print("5. 프롬프트 상세 보기")
    print("6. 즐겨찾기 관리")
    print("7. 즐겨찾기 목록")
    print("0. 종료")


def main():
    while True:
        show_menu()
        choice = input("선택: ")

        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        elif choice in ["1", "2", "3", "4", "5", "6", "7"]:
            print("아직 준비 중인 기능입니다.")
        else:
            print("올바른 메뉴 번호를 입력해주세요.")


main()