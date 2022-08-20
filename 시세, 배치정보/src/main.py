from specInfo import *
from collections import defaultdict
from MarketDataReader import *

if __name__ == "__main__":
    #경로 설정
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
                    # if name not in ['종목코드', '기초자산종목코드', 'ATM구분코드', '만기일자', '행사가격', '기준가', '기초자산종가', '종목한글명'
                    #                 ,'상장일자', '거래일자']:
                    #    continue
                    sub_result[name] = mark.decode('euc-kr').rstrip()
                total_result[trCd].append(sub_result)  # 결과를 저장하는 곳
                trNm = None
    except Exception as e:
        print(e)
        pass



    import json
    db_path = '../db'
    db = os.path.join(db_path, "result.json")
    with open(db, 'w', encoding='utf-8') as f:
        json.dump(total_result, f, indent='\t', ensure_ascii=False)

    #
    #
    # main_path = '..'
    # feed_spec = os.path.join(main_path, "feed spec")
    # feed_file = os.path.join(main_path, "feed file/20220803.batch.log")
    #
    # spec = MetaData()
    # totalSpecDf, totalSpec = spec.getSpecInfoByDirectory(main_path + '/feed spec')
    # totalTr = spec.getTrInfoByDirectory(main_path + '/feed spec')
    #
    # with app.app_context(): # Db세션을 연결해야됨
    #     db.create_all()  # 선언했던 테이블 생성해줘야됨
    #     optionLoader = OptionLoader(batchpath=feed_file, specpath=feed_spec)
    #     # futureLoader = FutureLoader(batchpath=feed_file, specpath=feed_spec)
    #     # equityLoader = EquityLoader(batchpath=feed_file, specpath=feed_spec)
    #     option = optionLoader.stockInfoByOtherInfo('KR7005930003', 0, 'C', 'I1')  # 기초자산ID, 월물정보, callput, ATM정보
    #     option = optionLoader.stockInfoByOtherInfo('KR7005930003', 1, 'C', 'I1')  # 기초자산ID, 월물정보, callput, ATM정보
    #     optionList = optionLoader.getOptionListSoredByStrike('KR7005930003', 0, 'C', 'I')  # 기초자산ID, 월물정보, callput, ATM정보
    #
    #     position = optionLoader.getStockInfo('KR4323T30314')  # 포지션
    #     opstposition = optionLoader.getOpstPosition('KR4323T30314')  # 반대 포지션
    #     # future = futureLoader.stockInfo('KR4101S90005')  # 기초자산ID, 월물정보
    #     # equity = equityLoader.stockInfo('HK0000057197')
    #     # equity_nm = equityLoader.stockInfo('이스트아시아홀딩스')
    #
    #     print(option.inisCd, option.inisNm)
    #     print(optionList)
    #     print(position.inisCd, position.inisNm, position.strike)
    #     print(opstposition.inisCd, opstposition.inisNm, position.strike)
    #     # print(future.inisCd, future.inisNm)
    #     # print(equity.inisCd, equity.inisNm)
    #     # print(equity_nm.inisCd, equity_nm.inisNm)
    #
    #
    #
    #
    #
    #
