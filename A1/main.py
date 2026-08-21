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


categories = [
    "텍스트 생성",
    "이미지 생성",
    "영상 생성",
    "페르소나",
    "자동화",
    "기타"
]


def get_non_empty_input(message):
    while True:
        value = input(message).strip()
        if value:
            return value
        print("입력값은 비워둘 수 없습니다.")


def add_prompt():
    print("\n=== 프롬프트 추가 ===")

    title = get_non_empty_input("제목: ")
    content = get_non_empty_input("내용: ")

    print("\n카테고리를 선택하세요.")
    for index, category in enumerate(categories, start=1):
        print(f"{index}. {category}")

    while True:
        category_input = input("선택 또는 직접 입력: ").strip()

        if category_input.isdigit():
            number = int(category_input)
            if 1 <= number <= len(categories):
                category = categories[number - 1]
                break
        elif category_input:
            category = category_input
            break

        print("올바른 카테고리를 입력해주세요.")

    prompts.append({
        "title": title,
        "content": content,
        "category": category,
        "favorite": False
    })

    print("프롬프트가 추가되었습니다!")


def main():
    while True:
        show_menu()
        choice = input("선택: ")

        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        elif choice == "1":
            add_prompt()
        elif choice in ["2", "3", "4", "5", "6", "7"]:
            print("아직 준비 중인 기능입니다.")


main()