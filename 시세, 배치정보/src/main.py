from specInfo import *
from fileTool import *
from collections import defaultdict


if __name__ == "__main__":
    # 경로 설정
    import os
    main_path = 'C:/Users/USER/Downloads/mm/자료/시세, 배치정보'
    feed_spec = os.path.join(main_path, "feed spec/KOSPI200지수옵션_실시간_UDP(12M)_1.550_2022080301.xls")
    feed_file = os.path.join(main_path, "feed file/20220803.batch.log")

    spec = ExcelByPandas()
    totalSpec = spec.getTotalSpecInfo(main_path + '/feed spec')
    totalTr = spec.getTotalTrInfo(main_path + '/feed spec')

    total_result = defaultdict(list) # 전체결과를 저장하는 곳
    try:
        with open(feed_file) as f:

            for line in f:
                sub_result = dict()
                trCd = line[9:14]
                try:
                    trNm = totalTr[trCd]['TR명']
                except:
                    print(trNm, trCd)
                    continue
                idx = 9
                byte_line = line.encode('euc-kr')
                a = totalSpec[trNm]
                b = totalTr[trCd]
                for name, _len in totalSpec[trNm]:
                    mark = byte_line[idx: idx + int(_len)]
                    sub_result[name] = mark.decode('euc-kr').rstrip()
                    idx += int(_len)
                total_result[trNm].append(sub_result) # 결과를 저장하는 곳

    except Exception as e:
        print(total_result)
        pass


    # db_path = 'C:/Users/USER/Downloads/mm/자료/시세, 배치정보/db'
    # db = os.path.join(db_path, "result.json")
    # jsonTool = JsonTool(db)
    #
    # for x in total_result.values():
    #     jsonTool.saveJsonFile(sub_result)


