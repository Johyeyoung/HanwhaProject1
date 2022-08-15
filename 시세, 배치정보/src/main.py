from specInfo import *
from fileTool import *
from collections import defaultdict
from MarketDataReader import *


if __name__ == "__main__":
    # 경로 설정
    import os
    main_path = '..'
    feed_spec = os.path.join(main_path, "feed spec/KOSPI200지수옵션_실시간_UDP(12M)_1.550_2022080301.xls")
    feed_file = os.path.join(main_path, "feed file/20220803.batch.log")

    spec = MetaData()
    totalSpecDf, totalSpec = spec.getSpecInfoByDirectory(main_path + '/feed spec')
    totalTr = spec.getTrInfoByDirectory(main_path + '/feed spec')
    trCdList = spec.totalTrDict.keys()

    total_result = defaultdict(list) # 전체결과를 저장하는 곳
    total_df = dict()

    try:
        with open(feed_file, encoding='cp949') as f:
            for line in f:

                trCd, idx, sub_result = line[9:14], 9, dict()

                if trCd not in trCdList:
                    print(f'코드\'{trCd}\'의 정보가 없습니다.')
                    continue
                else:
                    trNm = spec.totalTrDict[trCd]['TR명']

                # 특정 종목 코드만 필터링
                opStockTrcd = ['A0184', 'A0034', 'A0025', 'A0134', 'A0174']
                if trCd not in opStockTrcd: continue

                for name, _len in totalSpec[trNm]:
                    byte_line = line.encode('euc-kr')
                    mark = byte_line[idx: idx + int(_len)]
                    idx += int(_len)
                    if name not in ['종목코드', '기초자산종목코드', 'ATM구분코드', '만기일', '행사가격', '기준가', '종목한글']:
                       continue
                    sub_result[name] = mark.decode('euc-kr').rstrip()
                total_result[trCd].append(sub_result)  # 결과를 저장하는 곳
                trNm = None
    except Exception as e:
        print(e)
        pass


    db_path = '../db'
    db = os.path.join(db_path, "result.json")
    jsonTool = JsonTool(db)
    jsonTool.saveJsonFile(total_result)

