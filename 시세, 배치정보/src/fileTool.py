import json

class JsonTool:
    def __init__(self, file):
        self.filename = file
        pass

    # Json으로 파일 저장
    def saveJsonFile(self, content):
        with open(self.filename, "w", encoding='UTF-8-sig') as output_file:
            json.dump(content, output_file, indent="\t", ensure_ascii=False)
        print('입력이 완료되었습니다.')


class TextTool:
    def __init__(self):
        pass

    def readTextFile(self, fileName):
        with open(fileName, 'r') as f:
            for line in f: pass


if __name__ == "__main__":
    # 경로 설정
    import os
    db_path = 'C:/Users/USER/Downloads/mm/자료/시세, 배치정보/db'
    db = os.path.join(db_path, "result.json")

    # json으로 데이터 저장
    jsonTool = JsonTool(db)
